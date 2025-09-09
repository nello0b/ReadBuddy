// ReadBuddy\Views\Controls\QuizJumpSidebarControl.xaml.cs
using System.Windows;
using System.Windows.Controls;

namespace ReadBuddy.Views.Controls
{
    /// <summary>
    /// Interaction logic for QuizJumpSidebarControl.xaml
    /// </summary>
    public partial class QuizJumpSidebarControl : UserControl
    {
        public static readonly DependencyProperty HeaderTextProperty =
            DependencyProperty.Register("HeaderText", typeof(string), typeof(QuizJumpSidebarControl),
                new PropertyMetadata("Jump to question"));

        public string HeaderText
        {
            get { return (string)GetValue(HeaderTextProperty); }
            set { SetValue(HeaderTextProperty, value); }
        }

        public QuizJumpSidebarControl()
        {
            InitializeComponent();
        }
    }
}
