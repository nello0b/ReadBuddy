// ReadBuddy\ViewModels\Summary\SummaryViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using System.Linq;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Windows.Media;
using System.Windows.Documents;
using System.IO;
using ReadBuddy.Models.TTS;
using ReadBuddy.Services;
using Microsoft.Extensions.DependencyInjection;
using SummaryModel = ReadBuddy.Models.Summary.Summary;

namespace ReadBuddy.ViewModels.Summary
{
    public partial class SummaryViewModel : ObservableObject
    {
        private readonly SummaryModel _summary;

        private readonly BackendService _backend;
        private readonly IDialogService _dialogService;

        private MediaPlayer _mediaPlayer = new();
        private bool _isPlaying = false;
        private bool _isPaused = false;
        private int _currentAudioIndex = 0;

        private readonly List<Run> _runs = new();

        public IReadOnlyList<Run> Runs => _runs;

        public event Action<int>? HighlightRequested;

        [ObservableProperty]
        private ObservableCollection<AudioChunk> audioChunks = new();

        [ObservableProperty]
        private string playIcon = "Play";

        // Holds the text displayed inside the FlowDocument's single <Run> tag.
        [ObservableProperty]
        private string summaryText = "This is a test AI-generated summary. It highlights the most important points of the content for easier review.";

        [ObservableProperty]
        private FlowDocument summaryDocument = new();


        public SummaryViewModel(SummaryModel summary, IDialogService dialogService)
        {
            _summary = summary ?? new SummaryModel();
            _backend = App.ServiceProvider.GetRequiredService<BackendService>();
            _dialogService = dialogService;
            InitializeSummaryText();
            _mediaPlayer.MediaEnded += OnMediaEnded;
            LoadAudio();
        }

        public SummaryViewModel() : this(new SummaryModel(), App.ServiceProvider.GetRequiredService<IDialogService>()) { }

        private void InitializeSummaryText()
        {
            if (_summary.Content != null && _summary.Content.Any())
            {
                SummaryText = FormatSummaryContent(_summary.Content);
            }
            else
            {
                SummaryText = "No summary content available.";
            }

            BuildSummaryDocument();
        }

        private string FormatSummaryContent(IEnumerable<string> content)
        {
            // Join content lines while preserving bullet points - don't trim to keep formatting
            return string.Join("\n", content.Where(c => !string.IsNullOrWhiteSpace(c)));
        }

        private void BuildSummaryDocument()
        {
            var doc = new FlowDocument();
            _runs.Clear();

            var paragraph = new Paragraph();

            // Always build from the original summary text to preserve formatting like bullet points
            var lines = SummaryText.Split('\n');
            for (int i = 0; i < lines.Length; i++)
            {
                var line = lines[i];
                if (string.IsNullOrWhiteSpace(line)) continue;

                // Keep the line exactly as is - don't strip bullet points
                var run = new Run(line);
                paragraph.Inlines.Add(run);
                _runs.Add(run);

                // Add a line break between runs (except for the last one)
                if (i < lines.Length - 1 && !string.IsNullOrWhiteSpace(line))
                {
                    paragraph.Inlines.Add(new LineBreak());
                }
            }

            doc.Blocks.Add(paragraph);
            SummaryDocument = doc;

            System.Diagnostics.Debug.WriteLine($"BuildSummaryDocument completed with {_runs.Count} runs from summary text");
        }

        [RelayCommand]
        private void Play()
        {
            if (_isPlaying)
            {
                _mediaPlayer.Pause();
                _isPaused = true;
                _isPlaying = false;
                PlayIcon = "PlayPause";
            }
            else if (_isPaused)
            {
                _mediaPlayer.Play();
                _isPaused = false;
                _isPlaying = true;
                PlayIcon = "Pause";
            }
            else
            {
                _currentAudioIndex = 0;
                PlayCurrentAudioChunk();
            }
        }

        [RelayCommand]
        private void Stop()
        {
            if (_mediaPlayer != null)
            {
                _mediaPlayer.Stop();
                _isPlaying = false;
                _isPaused = false;
                PlayIcon = "Play";
                _currentAudioIndex = 0;
                HighlightRequested?.Invoke(-1);
            }
        }

        [RelayCommand]
        private void Copy()
        {
            try
            {
                Clipboard.SetText(SummaryText);
            }
            catch
            {
                // ignore clipboard errors
            }
        }

        private async void LoadAudio()
        {
            if (_summary.AudioZipUrls == null || _summary.AudioZipUrls.Count == 0)
                return;

            try
            {
                if (_backend == null)
                    return;

                var result = await TTSResult.CreateAsync(_summary.AudioZipUrls, _backend);
                foreach (var chunk in result.AudioChunks)
                    AudioChunks.Add(chunk);

                System.Diagnostics.Debug.WriteLine($"Loaded {AudioChunks.Count} audio chunks");

                // Rebuild the document now that we have audio chunks
                BuildSummaryDocument();
            }
            catch (Exception ex)
            {
                _dialogService.ShowError($"Failed to load summary audio: {ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Failed to load summary audio: {ex.Message}");
            }
        }

        private void PlayCurrentAudioChunk()
        {
            if (AudioChunks == null || AudioChunks.Count == 0 || _currentAudioIndex >= AudioChunks.Count)
            {
                _dialogService.ShowInfo("No audio to play.");
                _isPlaying = false;
                PlayIcon = "Play";
                HighlightRequested?.Invoke(-1);
                return;
            }

            var chunk = AudioChunks[_currentAudioIndex];
            HighlightRequested?.Invoke(_currentAudioIndex);
            string mp3Path = chunk.Mp3Path;

            if (!File.Exists(mp3Path))
            {
                _dialogService.ShowInfo($"Missing audio file: {mp3Path}");
                _isPlaying = false;
                PlayIcon = "Play";
                HighlightRequested?.Invoke(-1);
                return;
            }

            _mediaPlayer.Stop();
            _mediaPlayer.Close();
            _mediaPlayer.Open(new Uri(mp3Path, UriKind.RelativeOrAbsolute));
            _mediaPlayer.Play();
            _isPlaying = true;
            _isPaused = false;
            PlayIcon = "Pause";
        }

        private void OnMediaEnded(object? sender, EventArgs e)
        {
            if (!_isPlaying) return;

            _currentAudioIndex++;

            HighlightRequested?.Invoke(_currentAudioIndex);

            if (_currentAudioIndex < AudioChunks.Count)
            {
                Application.Current.Dispatcher.InvokeAsync(PlayCurrentAudioChunk);
            }
            else
            {
                Application.Current.Dispatcher.Invoke(() =>
                {
                    _isPlaying = false;
                    _isPaused = false;
                    _currentAudioIndex = 0;
                    PlayIcon = "Play";
                    HighlightRequested?.Invoke(-1);
                });
            }
        }

        public Run? GetRunByIndex(int index)
        {
            if (index < 0 || index >= _runs.Count)
                return null;
            return _runs[index];
        }
    }
}
