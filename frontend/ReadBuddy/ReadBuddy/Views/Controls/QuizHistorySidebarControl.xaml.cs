using System.Windows;
using System.Windows.Controls;

namespace ReadBuddy.Views.Controls
{
    /// <summary>
    /// Interaction logic for QuizHistorySidebarControl.xaml
    /// </summary>
    public partial class QuizHistorySidebarControl : UserControl
    {
        public QuizHistorySidebarControl()
        {
            InitializeComponent();
        }

        public static readonly DependencyProperty ItemsSourceProperty =
            DependencyProperty.Register(
                nameof(ItemsSource),
                typeof(System.Collections.IEnumerable),
                typeof(QuizHistorySidebarControl),
                new PropertyMetadata(null));

        public System.Collections.IEnumerable? ItemsSource
        {
            get => (System.Collections.IEnumerable?)GetValue(ItemsSourceProperty);
            set => SetValue(ItemsSourceProperty, value);
        }

        public static readonly DependencyProperty ShowDeleteButtonProperty =
            DependencyProperty.Register(
                nameof(ShowDeleteButton),
                typeof(bool),
                typeof(QuizHistorySidebarControl),
                new PropertyMetadata(false));

        public bool ShowDeleteButton
        {
            get => (bool)GetValue(ShowDeleteButtonProperty);
            set => SetValue(ShowDeleteButtonProperty, value);
        }
    }
}
