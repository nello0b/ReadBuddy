using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Models.Glossary;
using ReadBuddy.Models.Tasks;
using ReadBuddy.Services;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;

namespace ReadBuddy.ViewModels
{
    public partial class FlashcardPreparationViewModel : ObservableObject
    {
        private readonly Action<Glossary> _startCallback;
        private readonly GlossaryManager _glossaryManager;
        private readonly GlossaryHistoryService _historyService;
        private readonly IDialogService _dialogService;

        [ObservableProperty]
        private string selectedCategory = string.Empty;

        [ObservableProperty]
        private string selectedLanguage = "English";

        [ObservableProperty]
        private List<string> availableLanguages = new() { "English", "Hebrew" };

        public ObservableCollection<string> AvailableCategories => _historyService.AvailableCategories;
        public ObservableCollection<object> CombinedItems => _historyService.CombinedItems;

        public FlashcardPreparationViewModel(Action<Glossary> startCallback, GlossaryManager manager, GlossaryHistoryService history, IDialogService dialogService)
        {
            _startCallback = startCallback;
            _glossaryManager = manager;
            _historyService = history;
            _dialogService = dialogService;
            _ = InitializeAsync();
        }

        public FlashcardPreparationViewModel() : this(_ => { },
            App.ServiceProvider.GetRequiredService<GlossaryManager>(),
            App.ServiceProvider.GetRequiredService<GlossaryHistoryService>(),
            App.ServiceProvider.GetRequiredService<IDialogService>())
        { }

        private async Task InitializeAsync()
        {
            await _historyService.RefreshAsync();
            if (AvailableCategories.Count > 0)
                SelectedCategory = AvailableCategories[0];
        }

        [RelayCommand]
        private async Task CreateGlossary()
        {
            if (string.IsNullOrWhiteSpace(SelectedCategory)) return;

            // Convert language to backend format
            string langCode = SelectedLanguage.ToLowerInvariant() switch
            {
                "english" => "en",
                "hebrew" => "he",
                _ => "auto"
            };

            var taskInfo = await _glossaryManager.CreateGlossaryByCategoryAsync(SelectedCategory, langCode);
            if (taskInfo == null || string.IsNullOrEmpty(taskInfo.Task_Id))
            {
                _dialogService.ShowError("Failed to create glossary from backend.");
                return;
            }
            var trackerService = App.ServiceProvider.GetRequiredService<TaskTrackerService>();
            var tracker = new TaskTracker(taskInfo.Task_Id, trackerService);
            _historyService.AddTask(tracker);
        }

        [RelayCommand]
        private void GlossaryClicked(Glossary glossary)
        {
            if (glossary == null)
                return;
            _startCallback(glossary);
        }

        [RelayCommand]
        private async Task DeleteGlossaryAsync(Glossary glossary)
        {
            if (glossary == null) return;

            var result = _dialogService.ShowConfirmation(
                $"Are you sure you want to delete glossary for '{glossary.Category}'?",
                "Confirm Deletion");

            if (!result)
                return;

            bool success = await _glossaryManager.DeleteGlossaryAsync(glossary.Id);
            await _historyService.RefreshAsync();
            if (!success)
            {
                _dialogService.ShowError($"Failed to delete glossary '{glossary.Category}'.");
            }
        }

        // Legacy method kept for potential XAML bindings
        public void StartSelectedGlossary(Glossary glossary)
        {
            _startCallback(glossary);
        }
    }
}
