// ReadBuddy\Services\QuizHistoryService.cs
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using ReadBuddy.Models.Quiz;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Provides a shared observable collection of quiz history
    /// and helper methods for keeping it in sync with the backend.
    /// </summary>
    public class QuizHistoryService : TaskTrackingHistoryService<QuizSummary>
    {
        private readonly QuizManager _quizManager;
        private readonly ExtractionRepository _extractionRepository;

        public ObservableCollection<string> AvailableTopics { get; } = new();

        public QuizHistoryService(QuizManager quizManager, ExtractionRepository extractionRepository, IDialogService dialogService) : base(dialogService)
        {
            _quizManager = quizManager;
            _extractionRepository = extractionRepository;
        }

        public async Task LoadTopNAsync(int n)
        {
            var list = await _quizManager.GetAllQuizzesAsync();
            if (list == null) return;

            var sorted = list
                .OrderByDescending(q => q.CreatedAt)
                .Take(n)
                .ToList();
            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<QuizSummary>();
                foreach (var item in sorted)
                    AddSummaryItem(item);

                // Ensure quizzes appear in the expected order
                SortSummaries();
            });
        }


        public async Task RefreshAsync()
        {
            var list = await _quizManager.GetAllQuizzesAsync();
            var topics = await _extractionRepository.GetUserCategoriesAsync();

            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<QuizSummary>();
                if (list != null)
                {
                    foreach (var item in list.OrderByDescending(q => q.CreatedAt))
                        AddSummaryItem(item);
                }

                // Update topics in place to preserve existing selections
                for (int i = AvailableTopics.Count - 1; i >= 0; i--)
                {
                    if (!topics.Contains(AvailableTopics[i]))
                        AvailableTopics.RemoveAt(i);
                }
                foreach (var t in topics)
                    if (!string.IsNullOrWhiteSpace(t) && !AvailableTopics.Contains(t))
                        AvailableTopics.Add(t);

                SortSummaries();
            });
        }

        private async Task RefreshAvailableTopicsAsync()
        {
            var topics = await _extractionRepository.GetUserCategoriesAsync();
            App.Current.Dispatcher.Invoke(() =>
            {
                // Update topics in place to preserve existing selections
                for (int i = AvailableTopics.Count - 1; i >= 0; i--)
                {
                    if (!topics.Contains(AvailableTopics[i]))
                        AvailableTopics.RemoveAt(i);
                }
                foreach (var t in topics)
                    if (!string.IsNullOrWhiteSpace(t) && !AvailableTopics.Contains(t))
                        AvailableTopics.Add(t);
            });
        }



        /// <summary>
        /// Sorts the <see cref="QuizSummary"/> items in <see cref="CombinedItems"/>
        /// by <see cref="QuizSummary.CreatedAt"/> descending while preserving
        /// existing <see cref="TaskTracker"/> items.
        /// </summary>
        protected override void SortSummaries()
        {
            var tasks = CombinedItems.OfType<TaskTracker>().ToList();
            var quizzes = CombinedItems.OfType<QuizSummary>()
                .OrderByDescending(q => q.CreatedAt)
                .ToList();

            ClearAllItems();
            foreach (var t in tasks)
                AddTaskItem(t);
            foreach (var q in quizzes)
                AddSummaryItem(q);
        }

        protected override string GetSummaryId(QuizSummary summary)
        {
            return summary.Id;
        }

        protected override Task<QuizSummary?> FetchSummaryByIdAsync(string id)
        {
            return _quizManager.GetQuizSummaryByIdAsync(id);
        }

        protected override async Task OnTasksCompletedAsync(List<(TaskTracker Task, QuizSummary? Summary)> results)
        {
            await base.OnTasksCompletedAsync(results);
            await RefreshAvailableTopicsAsync();
        }

        protected override string GetFailureDialogTitle() => "Quiz Generation Failed";

        protected override string GetDefaultFailureMessage() => "Quiz generation failed.";

    }
}
