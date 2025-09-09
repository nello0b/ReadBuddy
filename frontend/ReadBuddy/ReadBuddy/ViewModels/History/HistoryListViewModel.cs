// ReadBuddy\ViewModels\History\HistoryListViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Services;
using System.Collections.ObjectModel;
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.Tasks;
using System.Linq;
using ReadBuddy.Views.Controls;
using System.Windows;
using System;

namespace ReadBuddy.ViewModels
{
    public partial class HistoryListViewModel : ObservableObject
    {
        private readonly ExtractionRepository _extractionRepository;
        private readonly ExtractionHistoryService _historyService;
        private readonly IDialogService _dialogService;

        public ObservableCollection<object> CombinedItems => _historyService.CombinedItems;

        // Collection shown in the history view. Sorting/filtering should not
        // mutate the shared CombinedItems list, so we expose a separate
        // observable collection.
        public ObservableCollection<object> DisplayItems { get; } = new();

        [ObservableProperty] private bool isDateAscending = false;
        [ObservableProperty] private bool isCategoryAscending = true;

        [ObservableProperty]
        private ObservableCollection<string> categories = new();

        [ObservableProperty]
        private string? selectedCategory;

        [ObservableProperty]
        private string selectedSortField = "Date"; // "Date" or "Category"

        [ObservableProperty]
        private ObservableCollection<string> sortFields = new() { "Date", "Category" };

        [ObservableProperty]
        private string sortDirectionIcon = "ArrowDownThin"; // Optional: UI icon support

        // Determines whether running tasks should be hidden in the history list
        [ObservableProperty]
        private bool hideTasks = false;

        public IRelayCommand EditCategoryCommand { get; }

        public event Action<ExtractionResultSummary>? OnOcrItemSelected;

        public HistoryListViewModel(ExtractionRepository extractionRepository, ExtractionHistoryService historyService, IDialogService dialogService)
        {
            _extractionRepository = extractionRepository;
            _historyService = historyService;
            _dialogService = dialogService;
            EditCategoryCommand = new RelayCommand<ExtractionResultSummary>(OnEditCategoryRequested);
            _historyService.CombinedItems.CollectionChanged += (_, __) => ApplySort();
            _ = LoadHistoryAsync();
            _ = LoadCategoriesAsync();

        }

        public async Task LoadHistoryAsync()
        {
            await _historyService.RefreshAsync();
            ApplySort(); // Default sort
        }

        public async Task LoadCategoriesAsync()
        {
            var list = await _extractionRepository.GetUserCategoriesAsync();
            App.Current.Dispatcher.Invoke(() =>
            {
                Categories.Clear();
                Categories.Add("All");
                foreach (var cat in list)
                    if (!string.IsNullOrWhiteSpace(cat))
                        Categories.Add(cat);
            });

            SelectedCategory = "All";
        }
        partial void OnSelectedCategoryChanged(string? value)
        {
            _ = ReloadForCategoryAsync();
        }

        private async Task ReloadForCategoryAsync()
        {
            await LoadHistoryAsync();
            ApplySort();
        }

        [RelayCommand]
        private async Task ReloadAsync()
        {

            await LoadHistoryAsync();
            await LoadCategoriesAsync();

            // Reset sorting options to defaults
            SelectedSortField = "Date";
            IsDateAscending = false;
            IsCategoryAscending = true;
            SortDirectionIcon = "ArrowDownThin";

            SelectedCategory = "All";
            HideTasks = false;
            ApplySort();
        }



        [RelayCommand]
        private void ToggleSortDirection()
        {
            IsDateAscending = !IsDateAscending;
            IsCategoryAscending = !IsCategoryAscending;

            SortDirectionIcon = IsDateAscending ? "ArrowUpThin" : "ArrowDownThin"; // Just for display
            ApplySort();
        }



        [RelayCommand]
        private void SummarySelected(ExtractionResultSummary? summary)
        {
            if (summary == null) return;
            OnOcrItemSelected?.Invoke(summary);
        }

        partial void OnSelectedSortFieldChanged(string value)
        {
            ApplySort();
        }

        partial void OnHideTasksChanged(bool value)
        {
            ApplySort();
        }


        private void ApplySort()
        {
            var summaries = _historyService.CombinedItems.OfType<ExtractionResultSummary>();
            var tasks = _historyService.CombinedItems.OfType<TaskTracker>().ToList();
            var sorted = summaries.AsEnumerable();

            if (!string.IsNullOrWhiteSpace(SelectedCategory) && SelectedCategory != "All")
                sorted = sorted.Where(x => string.Equals(x.Category, SelectedCategory, StringComparison.OrdinalIgnoreCase));

            if (SelectedSortField == "Date")
            {
                sorted = IsDateAscending ? sorted.OrderBy(x => x.CreatedAt)
                                         : sorted.OrderByDescending(x => x.CreatedAt);
            }
            else if (SelectedSortField == "Category")
            {
                sorted = IsCategoryAscending ? sorted.OrderBy(x => x.Category ?? "")
                                             : sorted.OrderByDescending(x => x.Category ?? "");
            }

            var list = sorted.ToList();

            App.Current.Dispatcher.Invoke(() =>
            {
                DisplayItems.Clear();
                if (!HideTasks)
                    foreach (var t in tasks) DisplayItems.Add(t);
                foreach (var item in list) DisplayItems.Add(item);
            });
        }

        [RelayCommand]
        private async Task DeleteExtractionAsync(ExtractionResultSummary? summary)
        {
            if (summary == null) return;

            var result = _dialogService.ShowConfirmation(
                $"Are you sure you want to delete \"{summary.Title}\"?",
                "Confirm Deletion");

            if (!result)
                return;

            bool success = await _extractionRepository.DeleteImageExtractionResultAsync(summary.ExtractionId);
            await _historyService.RefreshAsync(); // refresh from backend
            await LoadCategoriesAsync();           // also refresh categories

            if (!success)
            {
                _dialogService.ShowError($"Failed to delete \"{summary.Title}\" from the server.");
            }
        }

        private void OnEditCategoryRequested(ExtractionResultSummary? summary)
        {
            if (summary == null)
                return;

            Application.Current.Dispatcher.Invoke(() =>
            {
                var dialog = new EditCategoryDialog(summary.Category ?? "", summary.ExtractionId);
                dialog.Owner = Application.Current.Windows.OfType<Window>().FirstOrDefault(w => w.IsActive);

                if (dialog.ShowDialog() == true && dialog.DataContext is ViewModels.EditCategoryDialogViewModel vm)
                {
                    summary.Category = vm.SelectedCategory;
                    // Refresh the categories list and re-apply sorting to update the UI
                    _ = LoadCategoriesAsync();
                    ApplySort();
                }
            });
        }
    }
}
