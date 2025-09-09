// ReadBuddy\Views\Home\HomeHubView.xaml.cs
using System.Windows.Controls;
using ReadBuddy.ViewModels.Home;

namespace ReadBuddy.Views.Home
{
    public partial class HomeHubView : UserControl
    {
        public HomeHubView(HomeHubViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;
        }
    }
}
