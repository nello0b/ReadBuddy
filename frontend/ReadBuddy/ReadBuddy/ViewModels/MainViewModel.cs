// ReadBuddy/ViewModels/MainViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Services;
using ReadBuddy.Views;
using ReadBuddy.Views.Home;
using ReadBuddy.Views.Flashcards;
using System.Collections.ObjectModel;
using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;

namespace ReadBuddy.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {

        public partial class NavItem : ObservableObject
        {
            public string Label { get; set; }
            public string Icon { get; set; }
            public IRelayCommand Command { get; set; }

            [ObservableProperty]
            private bool isSelected;
        }


        public ObservableCollection<NavItem> NavigationItems { get; } = new();


        [ObservableProperty]
        private object currentView;

        private readonly IAuthService _authService;
        private readonly IUserSessionService _userSessionService;
        private readonly ExtractionHistoryService _extractionHistoryService;
        private readonly QuizHistoryService _quizHistoryService;
        private readonly GlossaryHistoryService _glossaryHistoryService;

        [ObservableProperty]
        private bool isSidebarExpanded = true;





        public RelayCommand HomeNavCommand { get; }

        public MainViewModel(
            HomeHubView homeView,
            QuizHubView quizhubView,
            FlashcardHubView flashcardHubView,
            HistoryView historyView,
            IAuthService authService,
            IUserSessionService userSessionService,
            ExtractionHistoryService extractionHistoryService,
            QuizHistoryService quizHistoryService,
            GlossaryHistoryService glossaryHistoryService
            )
        {
            _extractionHistoryService = extractionHistoryService;
            _quizHistoryService = quizHistoryService;
            _glossaryHistoryService = glossaryHistoryService;

            HomeNavCommand = AddNavItem("Home", "Home", homeView, async () => await _extractionHistoryService.RefreshAsync());
            var historyNavCommand = AddNavItem("History", "History", historyView, async () => await _extractionHistoryService.RefreshAsync());
            var quizeNavCommand = AddNavItem("Quiz", "School", quizhubView, async () => await _quizHistoryService.RefreshAsync());
            var flashNavCommand = AddNavItem("Flashcards", "Cards", flashcardHubView, async () => await _glossaryHistoryService.RefreshAsync());


            if (historyView.DataContext is HistoryViewModel histVm)
                histVm.RequestHomeNav += () => HomeNavCommand.Execute(null);

            _authService = authService;
            _userSessionService = userSessionService;

            // Invoke the Home navigation command to set the initial view
            HomeNavCommand.Execute(null);
        }

        [RelayCommand]
        private void ToggleSidebar() => IsSidebarExpanded = !IsSidebarExpanded;
        [RelayCommand]
        private async Task LogoutAsync()
        {
            // 1. Tell Auth0 to sign out  
            await _authService.LogoutAsync();

            // 2. Clear any local session state  
            _userSessionService.Clear();

            // 3. Tear down the MainWindow and spin up a fresh WelcomeView  
            Application.Current.Dispatcher.Invoke(() =>
            {
                // show the welcome/login screen again
                var welcome = App.ServiceProvider.GetRequiredService<WelcomeView>();
                welcome.Show();

                // find and close the MainWindow instance
                var main = Application.Current.Windows
                                      .OfType<MainWindow>()
                                      .FirstOrDefault();
                main?.Close();
            });
        }
        private RelayCommand AddNavItem(string label, string icon, UserControl view, Func<Task>? onNavigate = null)
        {
            var item = new NavItem
            {
                Label = label,
                Icon = icon,
            };

            item.Command = new RelayCommand(async () =>
            {
                // Update current view
                CurrentView = view;

                // Update selection
                foreach (var nav in NavigationItems)
                    nav.IsSelected = false;

                item.IsSelected = true;

                if (onNavigate != null)
                    await onNavigate();
            });

            NavigationItems.Add(item);
            return (RelayCommand)item.Command;
        }



    }
}