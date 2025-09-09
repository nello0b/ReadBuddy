// ReadBuddy\Views\Controls\NewTag.xaml.cs
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media.Animation;

namespace ReadBuddy.Views.Controls
{
    public partial class NewTag : UserControl
    {
        public NewTag()
        {
            InitializeComponent();
        }

        private void UserControl_Loaded(object sender, RoutedEventArgs e)
        {
            var storyboard = (Storyboard)Resources["BackgroundAnimation"];
            storyboard.Begin();
        }
    }
}
