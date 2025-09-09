// ReadBuddy\Views\CaptureOverlayWindow.xaml.cs
using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Animation;
using MaterialDesignThemes.Wpf;
using ReadBuddy.Services;
using System.Windows.Media;
using Microsoft.Extensions.DependencyInjection;


namespace ReadBuddy.Views
{
    public partial class CaptureOverlayWindow : Window
    {
        private readonly CaptureService _captureService = new(App.ServiceProvider.GetRequiredService<IDialogService>());

        private bool _isDocked = false;
        private DockSide? _dockedSide;
        private double _prevLeft;
        private double _prevTop;
        private double _prevWidth;
        private double _prevHeight;

        // Track state before capture for auto-docking
        private bool _wasDockedBeforeCapture = false;
        private DockSide? _dockedSideBeforeCapture;

        private enum DockSide { Left, Right }

        // Raised when a snip has been captured and written to disk.
        public event EventHandler<string>? ImageCaptured;

        public CaptureOverlayWindow()
        {
            InitializeComponent();
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            _captureService.SubscribeImageCaptured((_, path) =>
            {
                Dispatcher.Invoke(() =>
                {
                    if (!_wasDockedBeforeCapture)
                        RestoreWindow();

                    ImageCaptured?.Invoke(this, path);
                    Activate();
                });
            });
        }


        /// <summary>
        /// Enables dragging the window from any blank area.
        /// </summary>
        private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
                DragMove();
        }



        /// <summary>
        /// Handler for the "Capture" button.
        /// Launches the Windows Snipping Tool and automatically docks the window based on its position.
        /// </summary>
        private void CaptureSnip_Click(object sender, RoutedEventArgs e)
        {
            _wasDockedBeforeCapture = _isDocked;
            _dockedSideBeforeCapture = _dockedSide;

            if (!_isDocked)
            {
                DockSide sideToUse = DetermineDockSide();
                DockWindow(sideToUse, TimeSpan.Zero);
            }

            _captureService.StartCapture(this);
        }

        /// <summary>
        /// Handles native Windows messages, particularly clipboard updates.
        /// If a new image is detected, it stops listening and processes the image.
        /// </summary>

        /// <summary>
        /// Handles the custom "close" button click.
        /// </summary>
        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void DockLeftButton_Click(object sender, RoutedEventArgs e)
        {
            if (_isDocked)
            {
                RestoreWindow();
            }
            else
            {
                DockWindow(DockSide.Left);
            }
        }

        private void DockRightButton_Click(object sender, RoutedEventArgs e)
        {
            if (_isDocked)
            {
                RestoreWindow();
            }
            else
            {
                DockWindow(DockSide.Right);
            }
        }

        private void DockWindow(DockSide side)
        {
            DockWindow(side, TimeSpan.FromMilliseconds(200)); // Default animation duration
        }

        private void DockWindow(DockSide side, TimeSpan animationDuration)
        {
            _prevLeft = Left;
            _prevTop = Top;
            _prevWidth = Width;
            _prevHeight = Height;

            double targetWidth = 100;
            double targetHeight = 100;
            double margin = 10;
            double targetLeft = side == DockSide.Left ? SystemParameters.WorkArea.Left + margin : SystemParameters.WorkArea.Right - targetWidth - margin;
            double targetTop = SystemParameters.WorkArea.Bottom - targetHeight - margin;

            if (animationDuration.TotalMilliseconds == 0)
            {
                // Instant docking - no animation
                Left = targetLeft;
                Top = targetTop;
                Width = targetWidth;
                Height = targetHeight;
            }
            else
            {
                // Animated docking
                var widthAnim = new DoubleAnimation(targetWidth, animationDuration)
                {
                    FillBehavior = FillBehavior.Stop
                };
                widthAnim.Completed += (_, _) => Width = targetWidth;
                BeginAnimation(WidthProperty, widthAnim);

                var heightAnim = new DoubleAnimation(targetHeight, animationDuration)
                {
                    FillBehavior = FillBehavior.Stop
                };
                heightAnim.Completed += (_, _) => Height = targetHeight;
                BeginAnimation(HeightProperty, heightAnim);
                BeginAnimation(LeftProperty, new DoubleAnimation(targetLeft, animationDuration));
                BeginAnimation(TopProperty, new DoubleAnimation(targetTop, animationDuration));
            }

            MainBorder.Visibility = Visibility.Collapsed;
            LeftEye.Visibility = Visibility.Collapsed;
            RightEye.Visibility = Visibility.Collapsed;

            if (side == DockSide.Left)
            {
                DockRightButton.Visibility = Visibility.Collapsed;
                DockLeftIcon.Data = Geometry.Parse("M0,0 L0,20 L20,20 L20,0 Z");
            }
            else
            {
                DockLeftButton.Visibility = Visibility.Collapsed;
                DockRightIcon.Data = Geometry.Parse("M0,0 L0,20 L20,20 L20,0 Z");
            }

            _isDocked = true;
            _dockedSide = side;
        }

        private void RestoreWindow()
        {
            if (!_isDocked || _dockedSide == null)
                return;

            var duration = TimeSpan.FromMilliseconds(200);

            var restoreWidthAnim = new DoubleAnimation(_prevWidth, duration)
            {
                FillBehavior = FillBehavior.Stop
            };
            restoreWidthAnim.Completed += (_, _) => Width = _prevWidth;
            BeginAnimation(WidthProperty, restoreWidthAnim);

            var restoreHeightAnim = new DoubleAnimation(_prevHeight, duration)
            {
                FillBehavior = FillBehavior.Stop
            };
            restoreHeightAnim.Completed += (_, _) => Height = _prevHeight;
            BeginAnimation(HeightProperty, restoreHeightAnim);

            BeginAnimation(LeftProperty, new DoubleAnimation(_prevLeft, duration));
            BeginAnimation(TopProperty, new DoubleAnimation(_prevTop, duration));

            MainBorder.Visibility = Visibility.Visible;
            LeftEye.Visibility = Visibility.Visible;
            RightEye.Visibility = Visibility.Visible;

            DockLeftIcon.Data = Geometry.Parse("M0,0 L0,20 L20,20");
            DockRightIcon.Data = Geometry.Parse("M20,0 L20,20 L0,20");
            DockLeftButton.Visibility = Visibility.Visible;
            DockRightButton.Visibility = Visibility.Visible;

            _isDocked = false;
            _dockedSide = null;
        }

        /// <summary>
        /// Determines which side to dock the window based on its current position.
        /// Returns Left if the window is closer to the left side of the screen, Right otherwise.
        /// </summary>
        private DockSide DetermineDockSide()
        {
            double screenWidth = SystemParameters.WorkArea.Width;
            double windowCenterX = Left + (Width / 2);
            double screenCenterX = screenWidth / 2;

            return windowCenterX < screenCenterX ? DockSide.Left : DockSide.Right;
        }


        protected override void OnClosed(EventArgs e)
        {
            _captureService.StopCapture();
            _captureService.Dispose();
            base.OnClosed(e);
        }
    }
}
