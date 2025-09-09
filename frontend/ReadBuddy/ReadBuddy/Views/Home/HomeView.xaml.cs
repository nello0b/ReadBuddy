// CReadBuddy\Views\Home\HomeView.xaml.cs
using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using ReadBuddy.ViewModels.Home;
using ReadBuddy.Models.OCR;
using ReadBuddy.ViewModels;
using ReadBuddy.Views.Controls;

namespace ReadBuddy.Views.Home
{
    public partial class HomeView : UserControl
    {
        private readonly HomeViewModel _vm;

        public HomeView(HomeViewModel vm)
        {
            InitializeComponent();
            _vm = vm;
            DataContext = _vm;
            Unloaded += (_, _) => _vm.DisposeCaptureService();

        }

        // -------------------- Upload (unchanged) --------------------------
        private async void UploadControl_FileUploaded(object sender, FileUploadedEventArgs e)
        {
            await ShowAndRunAsync(async () =>
            {
                var ocr = new OcrImageViewModel();
                await _vm.ProcessImageAndUpdateAsync(e.FilePath, ocr);
            });
        }

        // -------------------- Capture logic moved to ViewModel --------------

        // -------------------- helper to show / hide overlay --------------
        private Task ShowAndRunAsync(Func<Task> action)
        {
            // Overlay removed; simply run the action
            return action();
        }
    }
}
