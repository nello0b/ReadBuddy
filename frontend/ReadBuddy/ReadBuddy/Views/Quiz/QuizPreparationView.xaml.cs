// ReadBuddy\Views\Quiz\QuizPreparationView.xaml.cs
using System.Windows.Controls;
using System.Windows.Input;
using System.Linq;
using ReadBuddy.ViewModels;

namespace ReadBuddy.Views
{
    public partial class QuizPreparationView : UserControl
    {
        public QuizPreparationView(QuizPreparationViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;
        }

        private void NumberBox_PreviewTextInput(object sender, TextCompositionEventArgs e)
        {
            // Accept only digits (0-9)
            e.Handled = !e.Text.All(char.IsDigit);
        }
    }
}
