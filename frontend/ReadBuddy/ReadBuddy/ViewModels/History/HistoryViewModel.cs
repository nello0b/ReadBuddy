// ReadBuddy\ViewModels\History\HistoryViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.ViewModels; // for the two sub-VMs
using ReadBuddy.ViewModels.Home;

using ReadBuddy.Views;                // for the two sub-views
using System;
using System.Windows.Controls;

namespace ReadBuddy.ViewModels
{
    /// <summary>
    /// Acts as the navigation hub between HistoryList and OCR-detail screens.
    /// </summary>
    public partial class HistoryViewModel : ObservableObject
    {
        // Sub-view-models (DI)
        private readonly HistoryListViewModel _historyListVm;
        private readonly HomeViewModel _homeViewModel;

        /// <summary>Raised when a history item requests navigation to home.</summary>
        public event Action? RequestHomeNav;

        // Sub-views
        private readonly UserControl _historyListView;

        // The ContentControl in HistoryView binds to this.
        [ObservableProperty] private UserControl currentView;

        // ------------------------------------------------------------------
        public HistoryViewModel(HistoryListViewModel historyListVm,
                                HomeViewModel homeViewModel)
        {
            _historyListVm = historyListVm;
            _homeViewModel = homeViewModel;

            // Create the two visual elements once and reuse
            _historyListView = new HistoryListView(_historyListVm);

            // --- Wire events ----------------------------------------------
            _historyListVm.OnOcrItemSelected += async summary =>
            {
                await _homeViewModel.LoadSummaryAsync(summary);
                RequestHomeNav?.Invoke();
            };

            // Default view
            CurrentView = _historyListView;
        }
    }
}
