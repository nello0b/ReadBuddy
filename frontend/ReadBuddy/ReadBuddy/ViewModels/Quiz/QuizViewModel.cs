// ReadBuddy\ViewModels\Quiz\QuizViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ReadBuddy.Models.Quiz;
using ReadBuddy.Models.TTS;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using System.Collections.ObjectModel;
using System.Windows.Media;
using System.IO;
using ReadBuddy.Services;


namespace ReadBuddy.ViewModels
{
    public partial class QuizViewModel : ObservableObject
    {
        // ──────────────────────────────────────────────────
        //  FIELDS & CONSTRUCTOR
        // ──────────────────────────────────────────────────

        #region Fields

        private readonly Quiz _quiz;
        private readonly Dictionary<string, string> _userAnswers;
        private readonly QuizManager _quizManager;
        private readonly IDialogService _dialogService;

        private MediaPlayer _mediaPlayer = new();
        private bool _isPlaying = false;
        private bool _isPaused = false;

        private List<AudioChunk> _audioSequence = new();
        private List<int> _highlightTargets = new();
        private int _currentAudioIndex = 0;

        public event Action? OnQuizSubmitted;
        public event Action? OnBackToHome;
        public event Action<int>? HighlightRequested;

        [ObservableProperty]
        private string playIcon = "Play";

        [ObservableProperty]
        private bool isAudioLoading = false;


        #endregion

        #region Nested Types

        /// <summary>
        /// Represents a preview for jumping to a specific question.
        /// </summary>
        public partial class QuestionJumpPreview : ObservableObject
        {
            public int Number { get; init; }
            public string Preview { get; init; }

            [ObservableProperty]
            private bool isAnswered;

            partial void OnIsAnsweredChanged(bool oldValue, bool newValue)
            {
                System.Diagnostics.Debug.WriteLine($"Q{Number} → IsAnswered: {newValue}");
            }
        }

        #endregion

        #region Constructor

        public QuizViewModel(Quiz quiz, Dictionary<string, string> userAnswers, QuizManager quizManager, IDialogService dialogService)
        {
            _quiz = quiz;

            _userAnswers = userAnswers;
            _quizManager = quizManager;
            _dialogService = dialogService;

            _mediaPlayer.MediaEnded += OnMediaEnded;
            _mediaPlayer.MediaFailed += OnMediaFailed;

            CurrentQuestionIndex = 0;
            CurrentQuestion = _quiz.Questions[CurrentQuestionIndex];

            QuestionJumpList = new ObservableCollection<QuestionJumpPreview>(
                _quiz.Questions.Select((q, idx) => new QuestionJumpPreview
                {
                    Number = idx + 1,
                    Preview = Truncate(q.Content, 15),
                    IsAnswered = _userAnswers.ContainsKey(q.Id)
                }));
        }

        #endregion

        #region Properties

        public ObservableCollection<QuestionJumpPreview> QuestionJumpList { get; }

        [ObservableProperty]
        private Question? currentQuestion;

        [ObservableProperty]
        private int currentQuestionIndex;

        [ObservableProperty]
        private Answer? selectedAnswer;

        /// <summary>
        /// Gets the progress text for the current quiz state.
        /// </summary>
        public string ProgressText =>
            $"Question {CurrentQuestionIndex + 1} of {_quiz.Questions.Count}";

        #endregion

        #region Property Change Handlers

        partial void OnCurrentQuestionIndexChanged(int value)
        {
            Stop();
            LoadCurrentQuestion();
        }

        partial void OnSelectedAnswerChanged(Answer? value)
        {
            if (value != null && CurrentQuestion != null)
            {
                _userAnswers[CurrentQuestion.Id] = value.Id;
                QuestionJumpList[CurrentQuestionIndex].IsAnswered = true;
            }

        }

        #endregion

        #region Commands

        [RelayCommand]
        private void SubmitQuiz()
        {

            bool isUnanswered = false;

            foreach (var question in _quiz.Questions)
            {
                if (!_userAnswers.TryGetValue(question.Id, out var selectedId))
                {
                    isUnanswered = true;
                    break;
                }
            }

            if (isUnanswered)
            {
                var result = _dialogService.ShowConfirmation(
                    $"There are unanswered questions.\nAre you sure you want to submit?",
                    "Confirm Submission");

                if (!result)
                    return;
            }

            Stop();
            OnQuizSubmitted?.Invoke(); // notify QuizHub to switch to review
        }

        [RelayCommand]
        private void BackToHome()
        {
            var result = _dialogService.ShowConfirmation(
                "Are you sure you want to quit the quiz and go back?",
                "Exit Quiz");

            if (result)
            {
                Stop();
                OnBackToHome?.Invoke();
            }
        }


        [RelayCommand(CanExecute = nameof(CanGoPrev))]
        private void Prev()
        {
            if (CurrentQuestionIndex == 0) return;
            CurrentQuestionIndex--;
        }

        [RelayCommand(CanExecute = nameof(CanGoNext))]
        private void Next()
        {
            if (CurrentQuestionIndex >= _quiz.Questions.Count - 1) return;
            CurrentQuestionIndex++;
        }

        [RelayCommand]
        private async Task PlayPause()
        {
            if (IsAudioLoading)
                return;

            if (_isPlaying)
            {
                _mediaPlayer.Pause();
                _isPlaying = false;
                _isPaused = true;
                PlayIcon = "PlayPause";
                return;
            }

            if (_isPaused)
            {
                _mediaPlayer.Play();
                _isPaused = false;
                _isPlaying = true;
                PlayIcon = "Pause";
                return;
            }

            if (CurrentQuestion == null)
                return;

            if (!CurrentQuestion.withAudio)
            {
                IsAudioLoading = true;
                var loaded = await _quizManager.LoadQuestion(_quiz, CurrentQuestionIndex, true);
                IsAudioLoading = false;

                if (!loaded)
                {
                    _dialogService.ShowError("Failed to load audio for the question.");
                    return;
                }

                if (!_quiz.Questions[CurrentQuestionIndex]!.withAudio)
                {
                    _dialogService.ShowInfo("Audio being processed at the moment, please try again later");
                    return;
                }

                // refresh question reference
                CurrentQuestion = _quiz.Questions[CurrentQuestionIndex];
            }

            BuildAudioSequence();

            if (_audioSequence.Count == 0)
            {
                _dialogService.ShowInfo("Audio being processed at the moment, please try again later");
                return;
            }

            _currentAudioIndex = 0;
            PlayCurrentAudioChunk();
        }

        [RelayCommand]
        private void Stop()
        {
            if (_isPlaying || _isPaused)
            {
                _mediaPlayer.Stop();
                _isPlaying = false;
                _isPaused = false;
                PlayIcon = "Play";
                _currentAudioIndex = 0;
                _audioSequence.Clear();
                HighlightRequested?.Invoke(-1);
            }
        }

        private void OnMediaEnded(object? sender, EventArgs e)
        {
            _currentAudioIndex++;

            if (_currentAudioIndex < _audioSequence.Count)
            {
                HighlightRequested?.Invoke(_highlightTargets[_currentAudioIndex]);
                Application.Current.Dispatcher.InvokeAsync(PlayCurrentAudioChunk);
            }
            else
            {
                _isPlaying = false;
                _isPaused = false;
                _currentAudioIndex = 0;
                PlayIcon = "Play";
                HighlightRequested?.Invoke(-1);
            }
        }

        private void OnMediaFailed(object? sender, ExceptionEventArgs e)
        {
            _dialogService.ShowError($"Failed to play audio: {e.ErrorException.Message}");
            _isPlaying = false;
            _isPaused = false;
            PlayIcon = "Play";
            HighlightRequested?.Invoke(-1);
        }

        private void PlayCurrentAudioChunk()
        {
            if (_audioSequence.Count == 0 || _currentAudioIndex >= _audioSequence.Count)
            {
                _dialogService.ShowInfo("No audio to play.");
                _isPlaying = false;
                _isPaused = false;
                PlayIcon = "Play";
                HighlightRequested?.Invoke(-1);
                return;
            }

            var chunk = _audioSequence[_currentAudioIndex];

            if (!File.Exists(chunk.Mp3Path))
            {
                _dialogService.ShowInfo($"Missing audio file: {chunk.Mp3Path}");
                _isPlaying = false;
                _isPaused = false;
                PlayIcon = "Play";
                HighlightRequested?.Invoke(-1);
                return;
            }

            _mediaPlayer.Stop();
            _mediaPlayer.Close();
            _mediaPlayer.Open(new Uri(chunk.Mp3Path, UriKind.Absolute));
            _mediaPlayer.Play();
            _isPlaying = true;
            _isPaused = false;
            PlayIcon = "Pause";
            HighlightRequested?.Invoke(_highlightTargets[_currentAudioIndex]);
        }

        #endregion

        #region Command CanExecute Methods

        private bool CanGoPrev() => CurrentQuestionIndex > 0;
        private bool CanGoNext() => CurrentQuestionIndex < _quiz.Questions.Count - 1;

        #endregion

        #region Core Logic

        /// <summary>
        /// Loads the current question and updates related state.
        /// </summary>
        private void LoadCurrentQuestion()
        {
            CurrentQuestion = _quiz.Questions[CurrentQuestionIndex];

            if (_userAnswers.TryGetValue(CurrentQuestion.Id, out var answerId))
            {
                SelectedAnswer = CurrentQuestion.Answers.FirstOrDefault(a => a.Id == answerId);
                QuestionJumpList[CurrentQuestionIndex].IsAnswered = true;
            }
            else
            {
                SelectedAnswer = null;
                QuestionJumpList[CurrentQuestionIndex].IsAnswered = false;
            }

            OnPropertyChanged(nameof(ProgressText));
            PrevCommand.NotifyCanExecuteChanged();
            NextCommand.NotifyCanExecuteChanged();

            _mediaPlayer.Stop();
            _isPlaying = false;
            _isPaused = false;
            PlayIcon = "Play";
            _currentAudioIndex = 0;
            HighlightRequested?.Invoke(-1);

            BuildAudioSequence();
        }

        #endregion

        #region Helpers

        /// <summary>
        /// Truncates a string to a maximum length, adding ellipsis if needed.
        /// </summary>
        private static string Truncate(string text, int max)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            if (text.Length <= max) return text;
            return text.Substring(0, max) + "...";
        }

        private void BuildAudioSequence()
        {
            _audioSequence.Clear();
            _highlightTargets.Clear();

            if (CurrentQuestion?.ttsResult?.AudioChunks != null)
            {
                _audioSequence.AddRange(CurrentQuestion.ttsResult.AudioChunks);
                _highlightTargets.AddRange(Enumerable.Repeat(0, CurrentQuestion.ttsResult.AudioChunks.Count));
            }

            if (CurrentQuestion?.Answers != null)
            {
                int idx = 1;
                foreach (var ans in CurrentQuestion.Answers)
                {
                    if (ans.ttsResult?.AudioChunks != null)
                    {
                        _audioSequence.AddRange(ans.ttsResult.AudioChunks);
                        _highlightTargets.AddRange(Enumerable.Repeat(idx, ans.ttsResult.AudioChunks.Count));
                    }
                    idx++;
                }
            }
        }



        #endregion
    }
}
