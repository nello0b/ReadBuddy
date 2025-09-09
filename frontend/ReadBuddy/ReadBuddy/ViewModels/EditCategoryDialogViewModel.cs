//  ReadBuddy\ViewModels\EditCategoryDialogViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Services;
using System.Collections.ObjectModel;
using System.Windows;

using System.Linq;
namespace ReadBuddy.ViewModels
{
    public partial class EditCategoryDialogViewModel : ObservableObject
    {
        [ObservableProperty]
        private string selectedCategory;

        public ObservableCollection<string> Categories { get; } = new();

        public IRelayCommand<string> SelectCategoryCommand { get; }
        public IRelayCommand CancelCommand { get; }
        public AsyncRelayCommand SaveCommand { get; }

        private readonly string _extractionId;

        private Window _owner;

        private readonly ExtractionRepository _extractionRepository;
        private readonly IDialogService _dialogService;


        public EditCategoryDialogViewModel(string currentCategory, Window owner, ExtractionRepository extractionRepository, string extractionId, IDialogService dialogService)
        {
            Categories = new ObservableCollection<string>();// in the futher we will get it form the server
            _extractionRepository = extractionRepository;
            SelectedCategory = currentCategory;
            _owner = owner;
            _extractionId = extractionId;
            _dialogService = dialogService;
            SelectCategoryCommand = new RelayCommand<string>(cat => SelectedCategory = cat);
            CancelCommand = new RelayCommand(Cancel);
            SaveCommand = new AsyncRelayCommand(Save); // Instead of RelayCommand
            _ = LoadCategoriesAsync();

        }

        private async Task LoadCategoriesAsync()
        {
            var list = await _extractionRepository.GetUserCategoriesAsync();
            var uniqueCategories = list
                .Where(c => !string.IsNullOrWhiteSpace(c))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .OrderBy(c => c)
                .ToList();

            // Must update ObservableCollection on UI thread
            Application.Current.Dispatcher.Invoke(() =>
            {
                Categories.Clear();
                foreach (var cat in uniqueCategories)
                {
                    Categories.Add(cat);
                }
            });
        }


        private void Cancel()
        {
            _owner.DialogResult = false;
            _owner.Close();
        }

        private async Task Save()
        {
            // Try to update the server
            bool success = await _extractionRepository.UpdateImageExtractionResultCategoryAsync(_extractionId, SelectedCategory);

            if (success)
            {
                _owner.DialogResult = true;
                _owner.Close();
            }
            else
            {
                _dialogService.ShowError("Failed to update the category. Please try again.");
                // Optionally, don't close the window if failed
            }
        }

    }
}
