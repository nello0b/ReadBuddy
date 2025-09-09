using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.Models.Quiz;
using ReadBuddy.Services;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Windows.Controls;

namespace ReadBuddy.ViewModels
{
    public partial class QuizHubViewModel : ObservableObject
    {
        [ObservableProperty]
        private UserControl? currentView;

        public Quiz? CurrentQuiz { get; private set; }
        public Dictionary<string, string> UserAnswers { get; } = new();

        private readonly QuizManager _quizManager;

        public QuizHubViewModel(QuizManager quizManager)
        {
            _quizManager = quizManager;
            var history = App.ServiceProvider.GetRequiredService<QuizHistoryService>();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            var prepVM = new QuizPreparationViewModel(StartQuiz, _quizManager, history, dialogs);
            CurrentView = new Views.QuizPreparationView(prepVM);
        }

        public void StartQuiz(Quiz quiz)
        {
            CurrentQuiz = quiz;
            UserAnswers.Clear();

            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            var quizVM = new QuizViewModel(CurrentQuiz, UserAnswers, _quizManager, dialogs);
            quizVM.OnBackToHome += ResetToPreparation;
            quizVM.OnQuizSubmitted += ShowReviewScreen;

            CurrentView = new Views.QuizView(quizVM);
        }

        private void ShowReviewScreen()
        {
            var reviewVM = new QuizReviewViewModel(CurrentQuiz!, UserAnswers);
            reviewVM.OnBackToHome += ResetToPreparation;
            CurrentView = new Views.QuizReviewView(reviewVM);
        }

        private void ResetToPreparation()
        {
            CurrentQuiz = null;
            UserAnswers.Clear();

            var history = App.ServiceProvider.GetRequiredService<QuizHistoryService>();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            var prepVM = new QuizPreparationViewModel(StartQuiz, _quizManager, history, dialogs);
            CurrentView = new Views.QuizPreparationView(prepVM);
        }

    }
}
