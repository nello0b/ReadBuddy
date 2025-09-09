// ReadBuddy\ViewModels\Quiz\QuizPreparationViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Models.Quiz;
using ReadBuddy.Services;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using ReadBuddy.Models.Tasks;
using System.Windows;


namespace ReadBuddy.ViewModels
{
    public partial class QuizPreparationViewModel : ObservableObject
    {
        private readonly Action<Quiz> _startQuizCallback;
        private readonly QuizManager _quizManager;
        private readonly QuizHistoryService _historyService;
        private readonly IDialogService _dialogService;

        [ObservableProperty]
        private int numberOfQuestions = 1;

        [ObservableProperty]
        private string selectedTopic = string.Empty;

        [ObservableProperty]
        private bool isAdvancedOptionsEnabled = false;

        public ObservableCollection<string> AvailableTopics => _historyService.AvailableTopics;

        public bool HasAvailableTopics => AvailableTopics.Count > 0;

        public ObservableCollection<object> CombinedItems => _historyService.CombinedItems;
        [ObservableProperty]
        private string selectedLanguage = "English";

        [ObservableProperty]
        private List<string> availableLanguages = new() { "English", "Hebrew" };

        /// <summary>
        /// Parameterless constructor for XAML designers. It resolves services
        /// using <see cref="App.ServiceProvider"/> and performs no action when
        /// the quiz is started.
        /// </summary>
        public QuizPreparationViewModel() :
            this(_ => { },
                 App.ServiceProvider.GetRequiredService<QuizManager>(),
                 App.ServiceProvider.GetRequiredService<QuizHistoryService>(),
                 App.ServiceProvider.GetRequiredService<IDialogService>())
        {
        }




        public QuizPreparationViewModel(Action<Quiz> startQuizCallback,
                                        QuizManager quizManager,
                                        QuizHistoryService historyService,
                                        IDialogService dialogService)
        {
            _startQuizCallback = startQuizCallback;
            _quizManager = quizManager;
            _historyService = historyService;
            _dialogService = dialogService;

            _historyService.AvailableTopics.CollectionChanged += (_, __) =>
                OnPropertyChanged(nameof(HasAvailableTopics));
            OnPropertyChanged(nameof(HasAvailableTopics));

            _ = InitializeAsync();
        }

        private async Task InitializeAsync()
        {
            await _historyService.RefreshAsync();
            if (AvailableTopics.Count > 0)
                SelectedTopic = AvailableTopics[0];
        }

        partial void OnSelectedTopicChanged(string value)
        {
            CreateQuizCommand.NotifyCanExecuteChanged();
        }

        private bool CanCreateQuiz() => !string.IsNullOrWhiteSpace(SelectedTopic);

        [RelayCommand(CanExecute = nameof(CanCreateQuiz))]
        private async Task CreateQuiz()
        {
            var taskInfo = await _quizManager.CreateQuizByCategoryAsync(
                SelectedTopic,
                NumberOfQuestions,
                SelectedLanguage,
                IsAdvancedOptionsEnabled);
            if (taskInfo == null || string.IsNullOrEmpty(taskInfo.Task_Id))
            {
                _dialogService.ShowError("Failed to create quiz from backend.");
                return;
            }

            var trackerService = App.ServiceProvider.GetRequiredService<TaskTrackerService>();
            var tracker = new TaskTracker(taskInfo.Task_Id, trackerService);
            _historyService.AddTask(tracker);
        }




        public static void ScrambleQuiz(Quiz quiz)
        {
            var random = new Random();

            foreach (var question in quiz.Questions)
            {
                // Shuffle answers in-place using Fisher–Yates algorithm
                for (int i = question.Answers.Count - 1; i > 0; i--)
                {
                    int j = random.Next(i + 1);
                    (question.Answers[i], question.Answers[j]) = (question.Answers[j], question.Answers[i]);
                }

                // Add prefix 1. to 5. to each answer content
                for (int i = 0; i < question.Answers.Count; i++)
                {
                    int number = i + 1;
                    question.Answers[i].Content = $"{number}. {StripPrefix(question.Answers[i].Content)}";
                }
            }
        }

        // Optional helper to remove old prefixes like "A. " or "1. " if any
        private static string StripPrefix(string content)
        {
            int prefixEnd = content.IndexOf(". ");
            return (prefixEnd == 1 || prefixEnd == 2) ? content.Substring(prefixEnd + 2) : content;
        }





        /// <summary>
        /// Creates a test quiz with sample math addition questions.
        /// </summary>
        /// <returns>A Quiz object with sample questions.</returns>
        public static Quiz make_test_quiz_classes(int QuestionsCount)
        {
            var random = new Random();
            var questions = new List<Question>();
            for (int i = 1; i <= QuestionsCount; i++)
            {
                int a = random.Next(1, 10);
                int b = random.Next(1, 10);
                int correct = a + b;
                var answers = new List<Answer>();
                var correctAnswerId = ((char)('a' + random.Next(0, 5))).ToString();
                for (int j = 0; j < 5; j++)
                {
                    int answerValue;
                    if (((char)('a' + j)).ToString() == correctAnswerId)
                    {
                        answerValue = correct;
                    }
                    else
                    {
                        // Ensure wrong answer is not equal to correct
                        do
                        {
                            answerValue = random.Next(correct - 3, correct + 4);
                        } while (answerValue == correct || answers.Any(ans => ans.Content == answerValue.ToString()));
                    }
                    answers.Add(new Answer("testuser", answerValue.ToString(), new List<string>(), ((char)('a' + j)).ToString()));
                }
                questions.Add(new Question(
                    userId: "testuser",
                    content: $"What is {a} + {b}?",
                    answers: answers,
                    correctAnswerId: correctAnswerId,
                    audioZipUrls: new List<string>(),
                    id: $"q{i}"
                ));
            }

            var questionIds = questions.Select(q => q.Id).ToList();

            return new Quiz(
                userId: "testuser",
                title: "Simple Math Addition Quiz",
                category: "Math",
                id: "quiz1",
                createdAt: DateTime.UtcNow,
                questionIds: questionIds,
                questions: questions
            );
        }

        [RelayCommand]
        private async Task QuizSummaryClicked(QuizSummary summary)
        {
            if (summary == null)
                return;

            var quiz = await _quizManager.LoadQuizAsync(summary, summary.QuestionCount);
            if (quiz == null)
            {
                _dialogService.ShowError("Failed to load quiz questions.");
                return;
            }

            //ScrambleQuiz(quiz);
            _startQuizCallback.Invoke(quiz);
        }

        [RelayCommand]
        private async Task DeleteQuizAsync(QuizSummary summary)
        {
            if (summary == null) return;

            var result = _dialogService.ShowConfirmation(
                $"Are you sure you want to delete \"{summary.Title}\"?",
                "Confirm Deletion");
            if (!result)
                return;

            bool success = await _quizManager.DeleteQuizAsync(summary.Id);
            await _historyService.RefreshAsync();
            if (!success)
            {
                _dialogService.ShowError($"Failed to delete \"{summary.Title}\" from the server.");
            }
        }




    }
}
