using ReadBuddy.ViewModels;
using System.Windows.Controls;

namespace ReadBuddy.Views.Flashcards
{
    public partial class FlashcardView : UserControl
    {
        public FlashcardView(FlashcardViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
        }
    }
}
