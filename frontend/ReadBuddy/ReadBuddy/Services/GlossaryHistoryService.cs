// ReadBuddy\Services\GlossaryHistoryService.cs
using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using ReadBuddy.Models.Glossary;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    public class GlossaryHistoryService : TaskTrackingHistoryService<Glossary>
    {
        private readonly GlossaryManager _glossaryManager;
        private readonly ExtractionRepository _extractionRepository;

        public ObservableCollection<string> AvailableCategories { get; } = new();

        public GlossaryHistoryService(GlossaryManager glossaryManager,
                                      ExtractionRepository extractionRepository,
                                      IDialogService dialogService) : base(dialogService)
        {
            _glossaryManager = glossaryManager;
            _extractionRepository = extractionRepository;
        }

        public async Task RefreshAsync()
        {
            var list = await _glossaryManager.GetAllGlossariesAsync();
            var categories = await _extractionRepository.GetUserCategoriesAsync();

            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<Glossary>();
                if (list != null)
                {
                    foreach (var item in list.OrderByDescending(g => g.LastUpdated))
                        AddSummaryItem(item);
                }

                for (int i = AvailableCategories.Count - 1; i >= 0; i--)
                {
                    if (!categories.Contains(AvailableCategories[i]))
                        AvailableCategories.RemoveAt(i);
                }
                foreach (var c in categories)
                    if (!string.IsNullOrWhiteSpace(c) && !AvailableCategories.Contains(c))
                        AvailableCategories.Add(c);

                SortSummaries();
            });
        }

        public async Task LoadTopNAsync(int n)
        {
            var list = await _glossaryManager.GetAllGlossariesAsync();
            if (list == null) return;

            var sorted = list.OrderByDescending(g => g.LastUpdated).Take(n).ToList();
            App.Current.Dispatcher.Invoke(() =>
            {
                ClearOfType<Glossary>();
                foreach (var item in sorted)
                    AddSummaryItem(item);
                SortSummaries();
            });
        }

        protected override void SortSummaries()
        {
            var tasks = CombinedItems.OfType<TaskTracker>().ToList();
            var glossaries = CombinedItems.OfType<Glossary>()
                .OrderByDescending(g => g.LastUpdated)
                .ToList();

            ClearAllItems();
            foreach (var t in tasks)
                AddTaskItem(t);
            foreach (var g in glossaries)
                AddSummaryItem(g);
        }

        protected override string GetSummaryId(Glossary summary) => summary.Id;

        protected override Task<Glossary?> FetchSummaryByIdAsync(string id)
        {
            return _glossaryManager.GetGlossaryByIdAsync(id);
        }

        private async Task RefreshAvailableCategoriesAsync()
        {
            var categories = await _extractionRepository.GetUserCategoriesAsync();
            App.Current.Dispatcher.Invoke(() =>
            {
                for (int i = AvailableCategories.Count - 1; i >= 0; i--)
                {
                    if (!categories.Contains(AvailableCategories[i]))
                        AvailableCategories.RemoveAt(i);
                }

                foreach (var c in categories)
                    if (!string.IsNullOrWhiteSpace(c) && !AvailableCategories.Contains(c))
                        AvailableCategories.Add(c);
            });
        }

        protected override async Task OnTasksCompletedAsync(List<(TaskTracker Task, Glossary? Summary)> results)
        {
            await base.OnTasksCompletedAsync(results);
            await RefreshAvailableCategoriesAsync();
        }
    }
}
