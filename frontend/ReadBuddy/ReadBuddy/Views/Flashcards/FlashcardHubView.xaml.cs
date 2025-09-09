using ReadBuddy.ViewModels;
using System.Windows.Controls;

namespace ReadBuddy.Views.Flashcards
{
    public partial class FlashcardHubView : UserControl
    {
        public FlashcardHubView(FlashcardHubViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
        }
    }
}
