using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.Models.Glossary;
using ReadBuddy.Services;
using Microsoft.Extensions.DependencyInjection;
using System;
using System.Windows.Controls;

namespace ReadBuddy.ViewModels
{
    public partial class FlashcardHubViewModel : ObservableObject
    {
        [ObservableProperty]
        private UserControl? currentView;

        public Glossary? CurrentGlossary { get; private set; }
        private readonly GlossaryManager _glossaryManager;

        public FlashcardHubViewModel(GlossaryManager glossaryManager)
        {
            _glossaryManager = glossaryManager;
            var history = App.ServiceProvider.GetRequiredService<GlossaryHistoryService>();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            var prepVM = new FlashcardPreparationViewModel(StartSession, _glossaryManager, history, dialogs);
            CurrentView = new Views.Flashcards.FlashcardPreparationView(prepVM);
        }

        public void StartSession(Glossary glossary)
        {
            CurrentGlossary = glossary;
            var vm = new FlashcardViewModel(CurrentGlossary);
            vm.OnBackToHome += ResetToPreparation;
            CurrentView = new Views.Flashcards.FlashcardView(vm);
        }

        private void ResetToPreparation()
        {
            CurrentGlossary = null;
            var history = App.ServiceProvider.GetRequiredService<GlossaryHistoryService>();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            var prepVM = new FlashcardPreparationViewModel(StartSession, _glossaryManager, history, dialogs);
            CurrentView = new Views.Flashcards.FlashcardPreparationView(prepVM);
        }
    }
}
