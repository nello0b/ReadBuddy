// ReadBuddy\ViewModels\Quiz\QuizReviewViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Models.Quiz;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace ReadBuddy.ViewModels
{
    public partial class QuizReviewViewModel : ObservableObject
    {

        public class QuestionReviewItem
        {
            public int Number { get; set; } // New property for question number
            public string QuestionContent { get; set; } = string.Empty;
            public string? SelectedAnswerContent { get; set; }
            public string CorrectAnswerContent { get; set; } = string.Empty;

            public bool IsCorrect => SelectedAnswerContent == CorrectAnswerContent;
            public bool IsAnswered => SelectedAnswerContent != null;
        }


        [ObservableProperty] private int correctCount;
        [ObservableProperty] private int wrongCount;
        [ObservableProperty] private int unansweredCount;

        public ObservableCollection<QuestionReviewItem> Questions { get; } = new();

        public event Action? OnBackToHome;

        public QuizReviewViewModel(Quiz quiz, Dictionary<string, string> userAnswers)
        {
            int questionNumber = 1;
            foreach (var question in quiz.Questions)
            {
                var item = new QuestionReviewItem
                {
                    Number = questionNumber++,
                    QuestionContent = question.Content,
                    CorrectAnswerContent = question.Answers
                        .First(a => a.Id == question.CorrectAnswerId).Content
                };

                if (userAnswers.TryGetValue(question.Id, out var selectedId))
                {
                    item.SelectedAnswerContent = question.Answers
                        .FirstOrDefault(a => a.Id == selectedId)?.Content;

                    if (item.SelectedAnswerContent == item.CorrectAnswerContent)
                        CorrectCount++;
                    else
                        WrongCount++;
                }
                else
                {
                    UnansweredCount++;
                }

                Questions.Add(item);
            }
        }

        [RelayCommand]
        private void BackToHome() => OnBackToHome?.Invoke();
    }
}
