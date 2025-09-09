using ReadBuddy.ViewModels;
using System.Windows;
using ReadBuddy.Animations;
using System.Windows.Media.Animation;
using System.Windows.Controls;

namespace ReadBuddy
{
    public partial class MainWindow : Window
    {
        public MainWindow(MainViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;
            ((MainViewModel)DataContext).PropertyChanged += (s, e) =>
            {
                if (e.PropertyName == nameof(MainViewModel.IsSidebarExpanded))
                {
                    AnimateSidebar(((MainViewModel)DataContext).IsSidebarExpanded);
                }
            };
        }
        private void AnimateSidebar(bool expand)
        {
            var animation = new GridLengthAnimation
            {
                From = SidebarColumn.Width,
                To = new GridLength(expand ? 200 : 60),
                Duration = new Duration(TimeSpan.FromMilliseconds(120))
            };

            SidebarColumn.BeginAnimation(ColumnDefinition.WidthProperty, animation);
        }

    }

}