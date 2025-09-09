// ReadBuddy\ViewModels\OcrImageViewModel.cs 
using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Windows.Media;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using System.Linq;


namespace ReadBuddy.ViewModels
{
    /// <summary>
    /// Holds the OCR image, result, and audio data shown inside OcrImageControl.
    /// </summary>
    public partial class OcrImageViewModel : ObservableObject
    {
        #region Fields & Properties

        [ObservableProperty]
        private ImageSource? imageSource;

        [ObservableProperty]
        private AnalyzeResult? ocrResult;

        [ObservableProperty]
        private ObservableCollection<AudioChunk> audioChunks = new();
        [ObservableProperty]
        private string category;
        [ObservableProperty]
        private string extractionId;
        [ObservableProperty]
        private string playIcon = "Play";




        public IRelayCommand CopyAllCommand { get; }
        public IRelayCommand<string> CopyParagraphCommand { get; }
        #endregion

        public OcrImageViewModel()
        {
            CopyAllCommand = new RelayCommand(OnCopyAll);
            CopyParagraphCommand = new RelayCommand<string>(OnCopyParagraph);

        }


        private void OnCopyAll()
        {
            if (OcrResult?.Paragraphs is { Count: > 0 })
            {
                var allText = string.Join("\n", OcrResult.Paragraphs.Select(p => p.Content));
                Clipboard.SetText(allText);
            }
        }

        private void OnCopyParagraph(string? text)
        {
            if (!string.IsNullOrWhiteSpace(text))
            {
                Clipboard.SetText(text);
            }
        }


    }
}
