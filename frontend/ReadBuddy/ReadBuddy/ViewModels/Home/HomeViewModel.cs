// ReadBuddy\ViewModels\Home\HomeViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using ReadBuddy.Models.Tasks;
using ReadBuddy.Services;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Media.Imaging;
using ReadBuddy.Views;

namespace ReadBuddy.ViewModels.Home
{
    public partial class HomeViewModel : ObservableObject
    {
        // ───────────────────────── Fields ─────────────────────────
        private readonly ExtractionRepository _repository;
        private readonly ExtractionHistoryService _historyService;
        private readonly IDialogService _dialogService;

        // ───────────────────────── Events ─────────────────────────
        public event Action<OcrImageViewModel>? OnOcrReady;

        // ───────────────────────── Bindable props ─────────────────
        [ObservableProperty] private bool isLoading;
        [ObservableProperty] private string? capturedImagePath;

        public ObservableCollection<object> CombinedItems => _historyService.CombinedItems;

        // ───────────────────────── Commands ───────────────────────
        public IRelayCommand<string> UploadCommand { get; }
        public IAsyncRelayCommand<ExtractionResultSummary> SummarySelectedCommand { get; }
        private WindowState _prevWindowState;
        private readonly CaptureService _captureService = new(App.ServiceProvider.GetRequiredService<IDialogService>());

        // ───────────────────────── Ctor ───────────────────────────
        public HomeViewModel(ExtractionRepository repository, ExtractionHistoryService historyService, IDialogService dialogService)
        {
            _repository = repository;
            _historyService = historyService;
            _dialogService = dialogService;

            UploadCommand = new RelayCommand<string>(async p => await HandleUploadAsync(p));
            SummarySelectedCommand = new AsyncRelayCommand<ExtractionResultSummary>(LoadSummaryAsync);

            _ = LoadHistoryAsync();
        }

        // ───────────────────────── Capture button ───────────────────
        [RelayCommand]
        private void Capture()
        {
            var mainWin = Application.Current.Windows.OfType<Window>()
                                           .FirstOrDefault(w => w.IsActive);
            mainWin?.Hide();

            var overlay = new CaptureOverlayWindow { Owner = mainWin };

            overlay.ImageCaptured += async (_, path) =>
            {
                CapturedImagePath = path;
                var ocr = new OcrImageViewModel();
                await ProcessImageAndUpdateAsync(path, ocr);

                try { File.Delete(path); } catch { /* ignore */ }
            };

            overlay.Closed += (_, __) =>
            {
                mainWin?.Show();
            };

            overlay.Show();
        }

        // ───────────────────────── Screenshot button ──────────────
        [RelayCommand]
        private void TakeScreenshot()
        {
            var mainWin = Application.Current.Windows.OfType<Window>()
                                           .FirstOrDefault(w => w.IsActive);
            if (mainWin == null)
                return;

            _prevWindowState = mainWin.WindowState;
            mainWin.WindowState = WindowState.Minimized;
            _captureService.StopCapture();
            _captureService.SubscribeImageCaptured(async (_, path) =>
            {
                mainWin.WindowState = _prevWindowState;
                mainWin.Activate();

                CapturedImagePath = path;
                var ocr = new OcrImageViewModel();
                await ProcessImageAndUpdateAsync(path, ocr);

                try { File.Delete(path); } catch { /* ignore */ }
            });

            _captureService.StartCapture(mainWin);
        }

        // ───────────────────────── Public helpers ─────────────────
        public void PublishOcrReady(OcrImageViewModel vm) => OnOcrReady?.Invoke(vm);

        // ───────────────────────── History loading ────────────────
        public async Task LoadHistoryAsync()
        {
            await _historyService.LoadTopNAsync(50);
        }

        // ───────────────────────── Upload handler ─────────────────
        private async Task HandleUploadAsync(string filePath)
        {
            var vm = new OcrImageViewModel();
            await ProcessImageAndUpdateAsync(filePath, vm);
        }

        // ───────────────────────── Sidebar click ──────────────────
        public async Task LoadSummaryAsync(ExtractionResultSummary? summary)
        {
            if (summary == null) return;

            IsLoading = true;
            try
            {
                var result = await _repository.GetImageExtractionResultAsync(summary.ExtractionId);
                if (result == null)
                {
                    _dialogService.ShowError("Could not load extraction from history.");
                    return;
                }

                var vm = new OcrImageViewModel
                {
                    OcrResult = result.TextData,
                    Category = result.Category,
                    ExtractionId = result.Id
                };

                if (!string.IsNullOrWhiteSpace(result.ImagePath) && File.Exists(result.ImagePath))
                    LoadImage(result.ImagePath, vm);

                foreach (var chunk in result.AudioData.AudioChunks)
                    vm.AudioChunks.Add(chunk);

                PublishOcrReady(vm);
            }
            finally { IsLoading = false; }
        }

        // ───────────────────────── Processing core ────────────────
        public async Task<bool> ProcessImageAndUpdateAsync(string file, OcrImageViewModel vm)
        {
            LoadImage(file, vm);

            vm.OcrResult = new AnalyzeResult { Pages = new(), Paragraphs = new() };

            try
            {
                var proc = App.ServiceProvider.GetRequiredService<DocumentProcessor>();
                var statusService = App.ServiceProvider.GetRequiredService<TaskTrackerService>();
                var taskInfo = await proc.ProcessImageAsync(file);

                if (taskInfo != null && !string.IsNullOrEmpty(taskInfo.Task_Id))
                {
                    var task = new TaskTracker(taskInfo.Task_Id, statusService);
                    _historyService.AddTask(task);
                    return true;
                }
                else
                {
                    _dialogService.ShowError("No valid task returned from backend.");
                }
            }
            catch (Exception ex)
            {
                _dialogService.ShowError($"Error during image processing: {ex.Message}");
            }

            return false;
        }

        private static void LoadImage(string path, OcrImageViewModel vm)
        {
            if (!File.Exists(path)) return;
            var bmp = new BitmapImage();
            using var s = File.OpenRead(path);
            bmp.BeginInit();
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.StreamSource = s;
            // Let WPF handle DPI scaling properly
            bmp.DecodePixelWidth = 0;
            bmp.DecodePixelHeight = 0;
            bmp.EndInit();
            bmp.Freeze();
            vm.ImageSource = bmp;
        }

        /// <summary>
        /// Safely disposes of the internal capture service when the
        /// associated view is unloaded.
        /// </summary>
        public void DisposeCaptureService()
        {
            _captureService.Dispose();
        }

    }
}
