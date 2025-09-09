using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Models.Extraction;
using ReadBuddy.Services;
using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows.Media.Imaging;

namespace ReadBuddy.ViewModels
{
    /// <summary>
    /// Wraps a single OCR extraction for the detail screen and lets the hub know when to go back.
    /// </summary>
    public partial class OcrHistoryViewModel : ObservableObject
    {
        private readonly ExtractionRepository _repo;

        // The VM already used by OcrImageControl
        [ObservableProperty] private OcrImageViewModel? currentOcr;

        /// <summary>Raised when the user presses Back.</summary>
        public event Action? RequestBack;

        // --- ctor ----------------------------------------------------------
        public OcrHistoryViewModel(ExtractionRepository repo)
        {
            _repo = repo;
        }

        // --- Public API called from the hub --------------------------------
        public async Task LoadItemAsync(ExtractionResultSummary summary)
        {
            // Reuse (and slightly refactor) the loading logic you had in HomeViewModel
            var extraction = await _repo.GetImageExtractionResultAsync(summary.ExtractionId);
            if (extraction == null) return;

            var vm = new OcrImageViewModel
            {
                Category = extraction.Category,
                ExtractionId = extraction.Id,
                OcrResult = extraction.TextData
            };

            // Load image if present
            if (!string.IsNullOrWhiteSpace(extraction.ImagePath))
                LoadImage(extraction.ImagePath, vm);

            // Audio chunks
            foreach (var chunk in extraction.AudioData.AudioChunks)
                vm.AudioChunks.Add(chunk);

            CurrentOcr = vm;   // triggers PropertyChanged
        }

        // --- Commands ------------------------------------------------------
        [RelayCommand]
        private void Back() => RequestBack?.Invoke();

        public void LoadImage(string filePath, OcrImageViewModel targetVm)
        {
            if (!File.Exists(filePath)) return;

            var bitmap = new BitmapImage();
            using (var stream = File.OpenRead(filePath))
            {
                bitmap.BeginInit();
                bitmap.CacheOption = BitmapCacheOption.OnLoad;
                bitmap.StreamSource = stream;
                bitmap.EndInit();
                bitmap.Freeze();
            }
            targetVm.ImageSource = bitmap;
        }
    }
}
