// ReadBuddy\Views\Controls\UploadControl.xaml.cs
using Microsoft.Win32;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Services;


namespace ReadBuddy.Views.Controls
{
    public partial class UploadControl : UserControl
    {
        public static readonly DependencyProperty FileUploadedCommandProperty =
    DependencyProperty.Register(nameof(FileUploadedCommand),
                                typeof(ICommand),
                                typeof(UploadControl),
                                new PropertyMetadata(null));

        public ICommand FileUploadedCommand
        {
            get => (ICommand)GetValue(FileUploadedCommandProperty);
            set => SetValue(FileUploadedCommandProperty, value);
        }
        // Allowed file types (common image formats)
        private static readonly string[] AllowedExtensions = { ".png", ".jpg", ".jpeg", ".bmp", ".gif" };
        private readonly IDialogService _dialogService = App.ServiceProvider.GetRequiredService<IDialogService>();

        public UploadControl()
        {
            InitializeComponent();

            // Register drag and drop event handlers
            Drop += OnDrop;
            DragEnter += OnDragEnter;
            DragLeave += OnDragLeave;
            DragOver += OnDragOver;

            // Register click handler for the browse button
            Loaded += OnControlLoaded;
        }

        private void OnControlLoaded(object sender, RoutedEventArgs e)
        {
            // Unregister first to prevent multiple registrations
            Loaded -= OnControlLoaded;
            
            if (FindName("BrowseButton") is Button browseButton)
            {
                // Remove any existing handler first to prevent duplicates
                browseButton.Click -= OnBrowseClicked;
                browseButton.Click += OnBrowseClicked;
            }
        }

        // Highlight drop zone when valid file is dragged over
        private void OnDragEnter(object sender, DragEventArgs e)
        {
            if (IsDataValid(e))
            {
                if (FindName("DropBorder") is Border dropBorder)
                {
                    dropBorder.Tag = "DragOver";
                }
                e.Handled = true;
            }
        }


        // Keep allowing copy operation on valid drag
        private void OnDragOver(object sender, DragEventArgs e)
        {
            if (IsDataValid(e))
            {
                e.Effects = DragDropEffects.Copy;
                e.Handled = true;
            }
        }

        // Reset border when dragging leaves the area
        private void OnDragLeave(object sender, DragEventArgs e)
        {
            if (FindName("DropBorder") is Border dropBorder)
            {
                dropBorder.Tag = null;
            }
        }


        // Handle file drop
        private void OnDrop(object sender, DragEventArgs e)
        {
            if (FindName("DropBorder") is Border dropBorder)
            {
                dropBorder.Tag = null;
            }

            if (!IsDataValid(e)) return;

            if (e.Data.GetData(DataFormats.FileDrop) is string[] droppedFiles && droppedFiles.Length > 0)
            {
                HandleFile(droppedFiles[0]);
            }
        }


        // Handle browse button click and file dialog selection
        private void OnBrowseClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "Image Files|*.png;*.jpg;*.jpeg;*.bmp;*.gif",
                Multiselect = false // Only one file allowed
            };

            if (dlg.ShowDialog() == true)
            {
                HandleFile(dlg.FileName);
            }
        }

        // Validate and notify file upload
        private void HandleFile(string filePath)
        {
            var ext = Path.GetExtension(filePath).ToLower();

            // Check if extension is allowed
            if (!AllowedExtensions.Contains(ext))
            {
                _dialogService.ShowError("Unsupported file type.", "Upload Error");
                return;
            }

            // Raise the routed event (for legacy/event-based handling)
            RaiseEvent(new FileUploadedEventArgs(FileUploadedEvent, filePath));

            // Execute the bound command (for MVVM binding)
            if (FileUploadedCommand?.CanExecute(filePath) == true)
            {
                FileUploadedCommand.Execute(filePath);
            }
        }


        // Validate drag data contains a single allowed file
        private bool IsDataValid(DragEventArgs e)
        {
            if (!e.Data.GetDataPresent(DataFormats.FileDrop)) return false;

            if (e.Data.GetData(DataFormats.FileDrop) is not string[] files) return false;

            if (files.Length != 1) return false;

            var ext = Path.GetExtension(files[0]).ToLower();

            return AllowedExtensions.Contains(ext);
        }

        // Routed event definition for file upload
        public static readonly RoutedEvent FileUploadedEvent = EventManager.RegisterRoutedEvent(
            nameof(FileUploaded), RoutingStrategy.Bubble, typeof(EventHandler<FileUploadedEventArgs>), typeof(UploadControl));

        // CLR event wrapper (for XAML/event binding)
        public event EventHandler<FileUploadedEventArgs> FileUploaded
        {
            add { AddHandler(FileUploadedEvent, value); }
            remove { RemoveHandler(FileUploadedEvent, value); }
        }
    }

    // Custom RoutedEventArgs class to pass the file path to parent
    public class FileUploadedEventArgs : RoutedEventArgs
    {
        public string FilePath { get; }

        public FileUploadedEventArgs(RoutedEvent routedEvent, string filePath)
            : base(routedEvent)
        {
            FilePath = filePath;
        }
    }
}
