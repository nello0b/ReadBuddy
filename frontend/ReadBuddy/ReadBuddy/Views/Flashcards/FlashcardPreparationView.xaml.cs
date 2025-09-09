using ReadBuddy.ViewModels;
using System.Windows.Controls;

namespace ReadBuddy.Views.Flashcards
{
    public partial class FlashcardPreparationView : UserControl
    {
        public FlashcardPreparationView(FlashcardPreparationViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
        }
    }
}
