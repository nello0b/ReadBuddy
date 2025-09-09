// ReadBuddy\Services\ExtractionHistoryService.cs
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Provides a shared observable collection of extraction history
    /// and helper methods for keeping it in sync with the backend.
    /// </summary>
    public class ExtractionHistoryService : TaskTrackingHistoryService<ExtractionResultSummary>
    {
        private readonly ExtractionRepository _repository;

        public ExtractionHistoryService(ExtractionRepository repository, IDialogService dialogService) : base(dialogService)
        {
            _repository = repository;
        }




        public async Task RefreshAsync()
        {
            var list = await _repository.GetHistoryAsync(true);
            var sorted = list.OrderByDescending(x => x.CreatedAt).ToList();
            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<ExtractionResultSummary>();
                foreach (var item in sorted)
                    AddSummaryItem(item);
            });
        }

        public async Task LoadTopNAsync(int n)
        {
            var list = await _repository.GetTopNHistoryAsync(n, true);
            var sorted = list.OrderByDescending(x => x.CreatedAt).ToList();
            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<ExtractionResultSummary>();
                foreach (var item in sorted)
                    AddSummaryItem(item);
            });
        }


        /// <summary>
        /// Sorts the <see cref="ExtractionResultSummary"/> items in
        /// <see cref="CombinedItems"/> by <see cref="ExtractionResultSummary.CreatedAt"/>
        /// descending while preserving existing <see cref="TaskTracker"/> items.
        /// </summary>
        protected override void SortSummaries()
        {
            var tasks = CombinedItems.OfType<TaskTracker>().ToList();
            var summaries = CombinedItems.OfType<ExtractionResultSummary>()
                .OrderByDescending(x => x.CreatedAt)
                .ToList();

            ClearAllItems();
            foreach (var t in tasks)
                AddTaskItem(t);
            foreach (var s in summaries)
                AddSummaryItem(s);
        }

        protected override Task<ExtractionResultSummary?> FetchSummaryByIdAsync(string id)
        {
            return _repository.GetExtractionSummaryByIdAsync(id);
        }

        protected override string GetSummaryId(ExtractionResultSummary summary)
        {
            return summary.ExtractionId;
        }

        protected override string GetFailureDialogTitle() => "Extraction Failed";

        protected override string GetDefaultFailureMessage() => "Extraction failed.";
    }

}
