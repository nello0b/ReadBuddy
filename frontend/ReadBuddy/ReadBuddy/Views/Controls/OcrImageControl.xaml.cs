// ReadBuddy\Views\Controls\OcrImageControl.xaml.cs
using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Collections.Generic;
using System.Windows.Threading;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.Windows.Media.Imaging;
using ReadBuddy.Services;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.ViewModels;
using System.ComponentModel;
using System;
using Microsoft.Extensions.DependencyInjection;
using System.Threading.Tasks;

namespace ReadBuddy.Views.Controls
{
    public partial class OcrImageControl : UserControl
    {
        #region Fields and Dependency Properties

        private List<Rectangle> paragraphRects = new();
        private List<Rectangle> _wordRects = new();

        private readonly OcrImageViewModel _viewModel = new();
        private readonly IDialogService _dialogService = App.ServiceProvider.GetRequiredService<IDialogService>();
        /// <summary>Inject an external view-model; sets DataContext & hooks events.</summary>
        public OcrImageViewModel ViewModel => _viewModel;

        public void ReplaceWith(OcrImageViewModel source)
        {
            _viewModel.ImageSource = source.ImageSource;
            _viewModel.OcrResult = source.OcrResult;
            _viewModel.AudioChunks.Clear();
            _viewModel.Category = source.Category;
            _viewModel.ExtractionId = source.ExtractionId;
            foreach (var chunk in source.AudioChunks)
                _viewModel.AudioChunks.Add(chunk);
        }

        void ViewModel_PropertyChanged(object? s, PropertyChangedEventArgs e)
        {
            if (e.PropertyName is nameof(OcrImageViewModel.ImageSource)
                               or nameof(OcrImageViewModel.OcrResult))
            {
                RenderOverlay();
            }
        }



        // Brushes for overlay rendering

        private Brush PrimaryBrush => (Brush)Application.Current.Resources["PrimaryBrush"];
        private Brush SecondaryBrush => (Brush)Application.Current.Resources["SecondaryBrush"];
        private Brush AccentBrush => (Brush)Application.Current.Resources["AccentBrush"];
        private Brush ExtraLightBrush => (Brush)Application.Current.Resources["ExtraLightBrush"];

        private static readonly Brush TransparentYellowBrush = (Brush)Application.Current.Resources["TransparentYellowBrush"];


        // Audio playback state
        private MediaPlayer _mediaPlayer = new();
        private int _currentAudioIndex = 0;
        private bool _isPlaying = false;
        private bool _isPaused = false;

        // Zoom and pan state
        private double _zoomLevel = 1.0;
        private const double ZoomStep = 0.1;
        private const double MinZoom = 0.2;
        private const double MaxZoom = 5.0;
        private bool _userHasZoomed = false;
        private Point _panStartPoint;
        private Point _scrollStartOffset;
        private bool _isPanning = false;

        #endregion

        #region Properties
        public ImageSource? ImageSource { get => _viewModel.ImageSource; set => _viewModel.ImageSource = value; }
        public AnalyzeResult? OcrResult { get => _viewModel.OcrResult; set => _viewModel.OcrResult = value; }
        public ObservableCollection<AudioChunk> AudioChunks => _viewModel.AudioChunks;


        public IRelayCommand PlayPauseCommand { get; }
        public IRelayCommand StopCommand { get; }
        public IRelayCommand ResetZoomCommand { get; }
        public IRelayCommand<object?> ParagraphMouseEnterCommand { get; }
        public IRelayCommand<object?> ParagraphMouseLeaveCommand { get; }
        public IRelayCommand<object?> PlayParagraphCommand { get; }




        #endregion

        #region Constructor

        public OcrImageControl()
        {
            InitializeComponent();

            DataContext = _viewModel;

            PlayPauseCommand = new RelayCommand(OnPlayPause);
            StopCommand = new RelayCommand(OnStop);
            ResetZoomCommand = new RelayCommand(OnResetZoom);
            ParagraphMouseEnterCommand = new RelayCommand<object?>(OnParagraphMouseEnter);
            ParagraphMouseLeaveCommand = new RelayCommand<object?>(OnParagraphMouseLeave);
            PlayParagraphCommand = new RelayCommand<object?>(OnPlayParagraph);

            _viewModel.PropertyChanged += (s, e) =>
            {
                if (e.PropertyName is nameof(_viewModel.ImageSource)
                                   or nameof(_viewModel.OcrResult))
                {
                    RenderOverlay();
                }
            };

            _mediaPlayer.MediaEnded += OnMediaEnded;
            
            SizeChanged += (s, e) =>
            {
                if (!_userHasZoomed && OcrImage.Source is BitmapSource bitmap)
                {
                    FitImageToViewport(bitmap);
                }
            };
        }





        #endregion

        #region Overlay Rendering

        private async void RenderOverlay()
        {
            
            OverlayCanvas.Children.Clear();
            paragraphRects.Clear();
            _wordRects.Clear();
            // Render image and wait for zoom to be applied
            await RenderImageAsync();

            await Task.Delay(50);

            // Now render overlays after zoom is set
            // RenderWordOverlays();
            RenderParagraphOverlays();
        }

        private async Task RenderImageAsync()
        {
            if (ImageSource != null)
            {
                OcrImage.Source = ImageSource;

                if (ImageSource is BitmapSource bitmap)
                {
                    // Wait for the zoom to be applied synchronously
                    // Use Dispatcher to ensure layout is complete
                    await Dispatcher.BeginInvoke(new Action(() => 
                    {
                        FitImageToViewport(bitmap);
                    }), DispatcherPriority.Loaded);
                }
            }
        }

        private void RenderWordOverlays()
        {
            if (OcrResult?.Pages == null) return;

            foreach (var page in OcrResult.Pages)
            {
                foreach (var word in page.Words)
                {
                    var x = word.Polygon[0];
                    var y = word.Polygon[1];
                    var w = GeometryHelper.GetRegionWidth(word.Polygon);
                    var h = GeometryHelper.GetRegionHeight(word.Polygon);

                    var wordRect = new Rectangle
                    {
                        Width = w,
                        Height = h,
                        //Fill = AccentBrushTrans,
                        StrokeThickness = 0
                    };

                    Canvas.SetLeft(wordRect, x);
                    Canvas.SetTop(wordRect, y);
                    OverlayCanvas.Children.Add(wordRect);
                    _wordRects.Add(wordRect);
                }
            }
        }

        private void RenderParagraphOverlays()
        {
            paragraphRects.Clear();
            if (OcrResult?.Paragraphs == null) return;

            // Calculate the scaling factor between OCR coordinates and rendered image
            var scaleFactor = CalculateCoordinateScaleFactor();
            if (scaleFactor == null) return;

            for (int i = 0; i < OcrResult.Paragraphs.Count; i++)
            {
                var para = OcrResult.Paragraphs[i];
                if (para.BoundingRegions is not { Count: > 0 }) continue;

                var poly = para.BoundingRegions[0].Polygon;

                // Scale the OCR coordinates to match the rendered image size
                var scaledX = (poly[0] * scaleFactor.Value.X) - 4;
                var scaledY = (poly[1] * scaleFactor.Value.Y) - 4;
                var scaledW = (GeometryHelper.GetRegionWidth(poly) * scaleFactor.Value.X) + 8;
                var scaledH = (GeometryHelper.GetRegionHeight(poly) * scaleFactor.Value.Y) + 8;

                var rect = new Rectangle
                {
                    Width = scaledW,
                    Height = scaledH,
                    Stroke = PrimaryBrush,
                    StrokeThickness = 2,
                    RadiusX = 10,
                    RadiusY = 10,
                    Fill = Brushes.Transparent,
                    Cursor = Cursors.Hand,
                    Tag = i
                };

                int capturedIndex = i;

                rect.MouseLeftButtonUp += (s, e) => ScrollToParagraph(capturedIndex);
                rect.MouseEnter += (s, e) =>
                {
                    HighlightParagraph(capturedIndex, true);
                    rect.Stroke = SecondaryBrush;
                    rect.StrokeThickness = 3;
                    Panel.SetZIndex(rect, 1);
                };
                rect.MouseLeave += (s, e) =>
                {
                    HighlightParagraph(capturedIndex, false);
                    rect.Stroke = PrimaryBrush;
                    rect.StrokeThickness = 2;
                    Panel.SetZIndex(rect, 0);
                };

                Canvas.SetLeft(rect, scaledX);
                Canvas.SetTop(rect, scaledY);
                OverlayCanvas.Children.Add(rect);
                paragraphRects.Add(rect);
            }
        }

        /// <summary>
        /// Calculates the scaling factor needed to convert OCR coordinates to rendered image coordinates.
        /// </summary>
        private Point? CalculateCoordinateScaleFactor()
        {
            if (OcrImage.Source is not BitmapSource bitmap) return null;

            // Get the original image dimensions (what OCR coordinates are based on)
            double originalWidth = bitmap.PixelWidth;
            double originalHeight = bitmap.PixelHeight;

            // Get the current rendered image dimensions
            double renderedWidth = OcrImage.ActualWidth;
            double renderedHeight = OcrImage.ActualHeight;

            if (originalWidth <= 0 || originalHeight <= 0 || renderedWidth <= 0 || renderedHeight <= 0)
                return null;

            // Calculate the scaling factors
            double scaleX = renderedWidth / originalWidth;
            double scaleY = renderedHeight / originalHeight;

            return new Point(scaleX, scaleY);
        }

        #endregion

        #region Paragraph List Highlighting and Scrolling

        private void HighlightParagraph(int index, bool highlight)
        {
            if (ParagraphItemsControl == null || index < 0 || index >= ParagraphItemsControl.Items.Count) return;
            var container = (FrameworkElement)ParagraphItemsControl.ItemContainerGenerator.ContainerFromIndex(index);
            if (container != null)
            {
                var rtb = VisualTreeHelperExtensions.FindVisualChild<RichTextBox>(container);
                if (rtb != null)
                {
                    rtb.BorderBrush = highlight
                        ? SecondaryBrush
                        : PrimaryBrush;
                    rtb.Background = highlight
                        ? AccentBrush
                        : ExtraLightBrush;
                }
            }
        }

        private void ScrollToParagraph(int index)
        {
            if (ParagraphItemsControl == null || index < 0 || index >= ParagraphItemsControl.Items.Count) return;
            var container = (FrameworkElement)ParagraphItemsControl.ItemContainerGenerator.ContainerFromIndex(index);
            if (container != null)
            {
                container.BringIntoView();
                var rtb = VisualTreeHelperExtensions.FindVisualChild<RichTextBox>(container);
                if (rtb != null)
                {
                    var original = rtb.Background;
                    rtb.Background = Brushes.LightYellow;
                    var timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
                    timer.Tick += (s, e) => { rtb.Background = original; timer.Stop(); };
                    timer.Start();
                }
            }
        }

        private void HighlightOverlay(int index, bool highlight)
        {
            if (index < 0 || index >= paragraphRects.Count) return;
            var rect = paragraphRects[index];
            rect.Stroke = highlight ? SecondaryBrush : PrimaryBrush;
            rect.StrokeThickness = highlight ? 3 : 2;
            Panel.SetZIndex(rect, highlight ? 1 : 0);
        }


        private void OnParagraphMouseEnter(object? item)
        {
            if (item == null) return;
            int index = ParagraphItemsControl.Items.IndexOf(item);
            HighlightParagraph(index, true);
            HighlightOverlay(index, true);
        }

        private void OnParagraphMouseLeave(object? item)
        {
            if (item == null) return;
            int index = ParagraphItemsControl.Items.IndexOf(item);
            HighlightParagraph(index, false);
            HighlightOverlay(index, false);
        }


        #endregion

        #region Zoom and Pan

        private void ZoomScrollViewer_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            if (e.Delta > 0 && _zoomLevel < MaxZoom) _zoomLevel += ZoomStep;
            else if (e.Delta < 0 && _zoomLevel > MinZoom) _zoomLevel -= ZoomStep;

            ZoomTransform.ScaleX = _zoomLevel;
            ZoomTransform.ScaleY = _zoomLevel;
            e.Handled = true;
            ResetZoomButton.Visibility = Visibility.Visible;
            _userHasZoomed = true;
        }

        private void OnResetZoom()
        {
            if (OcrImage.Source is BitmapSource bitmap)
            {
                FitImageToViewport(bitmap);
                _userHasZoomed = false;
                ResetZoomButton.Visibility = Visibility.Collapsed;
            }
        }

        private void FitImageToViewport(BitmapSource bitmap)
        {
            ZoomScrollViewer.UpdateLayout();

            // Get actual viewport size, with fallbacks
            double availableWidth = ZoomScrollViewer.ViewportWidth > 0 ?
                ZoomScrollViewer.ViewportWidth : ZoomScrollViewer.ActualWidth;
            double availableHeight = ZoomScrollViewer.ViewportHeight > 0 ?
                ZoomScrollViewer.ViewportHeight : ZoomScrollViewer.ActualHeight;

            // If still no dimensions, wait for layout
            if (availableWidth <= 0 || availableHeight <= 0)
            {
                ZoomScrollViewer.SizeChanged += OnScrollViewerSizeChanged;
                return;
            }

            // Use DPI-aware dimensions instead of PixelWidth/PixelHeight
            double imageWidth = bitmap.Width;
            double imageHeight = bitmap.Height;

            double scaleX = availableWidth / imageWidth;
            double scaleY = availableHeight / imageHeight;
            double scale = Math.Min(scaleX, scaleY);

            scale = Math.Max(MinZoom, Math.Min(MaxZoom, scale));

            _zoomLevel = scale;
            ZoomTransform.ScaleX = scale;
            ZoomTransform.ScaleY = scale;
        }

        private void OnScrollViewerSizeChanged(object sender, SizeChangedEventArgs e)
        {
            ZoomScrollViewer.SizeChanged -= OnScrollViewerSizeChanged;
            if (ImageSource is BitmapSource bitmap)
            {
                FitImageToViewport(bitmap);
            }
        }

        private void ZoomScrollViewer_PreviewMouseRightButtonDown(object sender, MouseButtonEventArgs e)
        {
            _isPanning = true;
            _panStartPoint = e.GetPosition(ZoomScrollViewer);
            _scrollStartOffset = new Point(ZoomScrollViewer.HorizontalOffset, ZoomScrollViewer.VerticalOffset);
            ZoomScrollViewer.Cursor = Cursors.SizeAll;
            ZoomScrollViewer.CaptureMouse();
        }

        private void ZoomScrollViewer_PreviewMouseMove(object sender, MouseEventArgs e)
        {
            if (_isPanning && e.RightButton == MouseButtonState.Pressed)
            {
                Point currentPoint = e.GetPosition(ZoomScrollViewer);
                Vector delta = Point.Subtract(currentPoint, _panStartPoint);
                ZoomScrollViewer.ScrollToHorizontalOffset(_scrollStartOffset.X - delta.X);
                ZoomScrollViewer.ScrollToVerticalOffset(_scrollStartOffset.Y - delta.Y);
            }
        }

        private void ZoomScrollViewer_PreviewMouseRightButtonUp(object sender, MouseButtonEventArgs e)
        {
            _isPanning = false;
            ZoomScrollViewer.ReleaseMouseCapture();
            ZoomScrollViewer.Cursor = Cursors.Arrow;
        }

        #endregion

        #region Audio Playback

        private void OnPlayPause()
        {
            if (_isPlaying)
            {
                _mediaPlayer.Pause();
                _isPaused = true;
                _isPlaying = false;
                _viewModel.PlayIcon = "PlayPause";
            }
            else if (_isPaused)
            {
                _mediaPlayer.Play();
                _isPaused = false;
                _isPlaying = true;
                _viewModel.PlayIcon = "Pause";
            }
            else
            {
                _currentAudioIndex = 0;
                _viewModel.PlayIcon = "Pause";
                PlayCurrentAudioChunk();
            }
        }

        private void OnStop()
        {
            if (_mediaPlayer != null)
            {
                _mediaPlayer.Stop();
                _isPlaying = false;
                _isPaused = false;
                _currentAudioIndex = -1;
                _viewModel.PlayIcon = "Play";
                UpdateParagraphHighlights();
            }
        }

        private async void PlayCurrentAudioChunk()
        {
            if (AudioChunks == null || AudioChunks.Count == 0 || _currentAudioIndex >= AudioChunks.Count)
            {
                _dialogService.ShowInfo("No audio to play.");
                _isPlaying = false;
                return;
            }

            var chunk = AudioChunks[_currentAudioIndex];
            string mp3Path = chunk.Mp3Path;

            if (!File.Exists(mp3Path))
            {
                _dialogService.ShowInfo($"Missing audio file: {mp3Path}");
                _isPlaying = false;
                return;
            }

            _mediaPlayer.Stop();
            _mediaPlayer.Close();
            _mediaPlayer.Open(new Uri(mp3Path, UriKind.RelativeOrAbsolute));
            _mediaPlayer.Play();
            _isPlaying = true;
            _isPaused = false;
            _viewModel.PlayIcon = "Pause";
            UpdateParagraphHighlights();
        }



        private async void OnMediaEnded(object sender, EventArgs e)
        {
            if (!_isPlaying) return;

            _currentAudioIndex++;

            if (_currentAudioIndex < AudioChunks.Count)
            {
                UpdateParagraphHighlights();
                await Application.Current.Dispatcher.InvokeAsync(PlayCurrentAudioChunk);
            }
            else
            {
                await Application.Current.Dispatcher.InvokeAsync(() =>
                {
                    _isPlaying = false;
                    _isPaused = false;
                    _currentAudioIndex = -1;
                    _viewModel.PlayIcon = "Play";
                    UpdateParagraphHighlights();
                });
            }
        }

        private void OnPlayParagraph(object? parameter)
        {
            if (parameter is not Paragraph paragraph)
                return;

            // Find paragraph index
            var index = OcrResult?.Paragraphs?.IndexOf(paragraph) ?? -1;
            if (index < 0 || index >= AudioChunks.Count)
                return;

            // Set the index and call the playback function
            _currentAudioIndex = index;
            PlayCurrentAudioChunk();
        }




        private void UpdateParagraphHighlights()
        {
            for (int i = 0; i < paragraphRects.Count; i++)
            {
                paragraphRects[i].Fill = Brushes.Transparent;
                paragraphRects[i].Stroke = PrimaryBrush;
            }

            int idx = _currentAudioIndex;
            if (idx >= 0 && idx < paragraphRects.Count)
            {
                paragraphRects[idx].Fill = TransparentYellowBrush;
                paragraphRects[idx].Stroke = SecondaryBrush;
            }
        }

        #endregion



    }
}





