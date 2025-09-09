// ReadBuddy\Views\History\HistoryView.xaml.cs
using System.Windows.Controls;
using ReadBuddy.ViewModels;

namespace ReadBuddy.Views
{
    public partial class HistoryView : UserControl
    {
        public HistoryView(HistoryViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;
        }
    }
}
