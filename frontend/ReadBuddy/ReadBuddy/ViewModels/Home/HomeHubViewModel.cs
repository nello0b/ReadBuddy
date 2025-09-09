// ReadBuddy\ViewModels\Home\HomeHubViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.Views.Home;
using ReadBuddy.ViewModels.Home;
using System.Windows.Controls;
using System;

namespace ReadBuddy.ViewModels.Home
{
    /// <summary>
    /// Hub ViewModel that swaps between HomeView and OcrHomeView.
    /// </summary>
    public partial class HomeHubViewModel : ObservableObject
    {
        // Sub-viewmodels
        private readonly HomeViewModel _homeViewModel;
        private readonly OcrHomeViewModel _ocrHomeViewModel;

        // Sub-views
        private readonly UserControl _homeView;
        private readonly UserControl _ocrHomeView;

        [ObservableProperty]
        private UserControl currentView;

        public HomeHubViewModel(HomeViewModel homeViewModel, OcrHomeViewModel ocrHomeViewModel)
        {
            _homeViewModel = homeViewModel;
            _ocrHomeViewModel = ocrHomeViewModel;

            _homeView = new HomeView(_homeViewModel);
            _ocrHomeView = new OcrHomeView(_ocrHomeViewModel);

            // Hook up events
            _homeViewModel.OnOcrReady += vm =>
            {
                _ocrHomeViewModel.LoadOcr(vm);
                CurrentView = _ocrHomeView;
            };

            _ocrHomeViewModel.RequestBack += async () =>
            {
                CurrentView = _homeView;
                _ocrHomeViewModel.ClearOcr();
                DeleteTempSnip();
                await _homeViewModel.LoadHistoryAsync();
            };

            // Default view is the home upload/start screen
            CurrentView = _homeView;
        }

        private void DeleteTempSnip()
        {
            try
            {
                string tempPath = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "ReadBuddy_Snip.png");
                if (System.IO.File.Exists(tempPath))
                    System.IO.File.Delete(tempPath);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to delete temp snip: {ex.Message}");
            }
        }
    }
}
