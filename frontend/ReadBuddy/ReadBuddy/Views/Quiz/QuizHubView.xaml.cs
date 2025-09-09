using ReadBuddy.ViewModels;
using System.Windows.Controls;

namespace ReadBuddy.Views
{
    public partial class QuizHubView : UserControl
    {
        public QuizHubView(QuizHubViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
        }
    }
}
