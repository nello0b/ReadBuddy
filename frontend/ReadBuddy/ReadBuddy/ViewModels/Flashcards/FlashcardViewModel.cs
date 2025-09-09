using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Models.Glossary;
using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;

namespace ReadBuddy.ViewModels
{
    public partial class FlashcardViewModel : ObservableObject
    {
        private readonly Glossary _glossary;

        public ObservableCollection<CardJumpPreview> QuestionJumpList { get; }

        [ObservableProperty]
        private int currentQuestionIndex = 0;

        public partial class CardJumpPreview : ObservableObject
        {
            public int Number { get; init; }
            public string Preview { get; init; } = string.Empty;
            [ObservableProperty]
            private bool isAnswered = false;
        }

        public event Action? OnBackToHome;

        public FlashcardViewModel(Glossary glossary)
        {
            _glossary = glossary;

            QuestionJumpList = new ObservableCollection<CardJumpPreview>();
            for (int i = 0; i < _glossary.Entries.Count; i++)
            {
                QuestionJumpList.Add(new CardJumpPreview
                {
                    Number = i + 1,
                    Preview = Truncate(_glossary.Entries[i].Term, 15)
                });
            }

            if (_glossary.Entries.Count > 0)
            {
                CurrentQuestionIndex = 0;
                CurrentEntry = _glossary.Entries[0];
            }
        }

        [ObservableProperty]
        private GlossaryEntry? currentEntry;

        [ObservableProperty]
        private bool isDefinitionVisible = false;

        public string ProgressText => $"Card {CurrentQuestionIndex + 1} of {_glossary.Entries.Count}";

        public string FlipButtonText => "Flip Card";

        public string DisplayedText => IsDefinitionVisible ? CurrentEntry?.Definition ?? "" : CurrentEntry?.Term ?? "";

        partial void OnCurrentQuestionIndexChanged(int value)
        {
            if (value >= 0 && value < _glossary.Entries.Count)
            {
                CurrentEntry = _glossary.Entries[value];
                IsDefinitionVisible = false; // Reset to show term when moving between cards
                OnPropertyChanged(nameof(ProgressText));
                OnPropertyChanged(nameof(FlipButtonText));
                OnPropertyChanged(nameof(DisplayedText));
                PrevCardCommand.NotifyCanExecuteChanged();
                NextCardCommand.NotifyCanExecuteChanged();
            }
        }

        partial void OnIsDefinitionVisibleChanged(bool value)
        {
            OnPropertyChanged(nameof(FlipButtonText));
            OnPropertyChanged(nameof(DisplayedText));
        }

        [RelayCommand]
        private async Task FlipCard()
        {
            // Wait for 0.15 seconds (when card is invisible) before changing the content
            await Task.Delay(150);
            IsDefinitionVisible = !IsDefinitionVisible;
        }

        [RelayCommand(CanExecute = nameof(CanGoNext))]
        private void NextCard()
        {
            if (CurrentQuestionIndex < _glossary.Entries.Count - 1)
                CurrentQuestionIndex++;
        }

        [RelayCommand(CanExecute = nameof(CanGoPrev))]
        private void PrevCard()
        {
            if (CurrentQuestionIndex > 0)
                CurrentQuestionIndex--;
        }

        [RelayCommand]
        private void Back()
        {
            OnBackToHome?.Invoke();
        }

        private bool CanGoPrev() => CurrentQuestionIndex > 0;
        private bool CanGoNext() => CurrentQuestionIndex < _glossary.Entries.Count - 1;

        private static string Truncate(string text, int max)
        {
            if (string.IsNullOrWhiteSpace(text)) return "";
            if (text.Length <= max) return text;
            return text.Substring(0, max) + "...";
        }
    }
}
