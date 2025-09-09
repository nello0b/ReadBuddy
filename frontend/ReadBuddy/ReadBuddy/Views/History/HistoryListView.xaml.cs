// ReadBuddy\Views\History\HistoryListView.xaml.cs
using ReadBuddy.ViewModels;
using System.Windows.Controls;

namespace ReadBuddy.Views
{
    public partial class HistoryListView : UserControl
    {
        public HistoryListView(HistoryListViewModel vm)
        {
            InitializeComponent();
            DataContext = vm;
        }
    }
}
