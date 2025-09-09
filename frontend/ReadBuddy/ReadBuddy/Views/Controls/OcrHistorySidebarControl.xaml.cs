// ReadBuddy\Views\Controls\OcrHistorySidebarControl.xaml.cs
using System.Windows;
using System.Windows.Controls;

namespace ReadBuddy.Views.Controls
{
    public partial class OcrHistorySidebarControl : UserControl
    {
        public OcrHistorySidebarControl()
        {
            InitializeComponent();
        }

        // ItemsSource so parent views can provide a custom collection
        public static readonly DependencyProperty ItemsSourceProperty =
            DependencyProperty.Register(
                nameof(ItemsSource),
                typeof(System.Collections.IEnumerable),
                typeof(OcrHistorySidebarControl),
                new PropertyMetadata(null));

        public System.Collections.IEnumerable? ItemsSource
        {
            get => (System.Collections.IEnumerable?)GetValue(ItemsSourceProperty);
            set => SetValue(ItemsSourceProperty, value);
        }

        // Dependency property to control delete button visibility
        public static readonly DependencyProperty ShowDeleteButtonProperty =
            DependencyProperty.Register(
                nameof(ShowDeleteButton),
                typeof(bool),
                typeof(OcrHistorySidebarControl),
                new PropertyMetadata(false));

        public bool ShowDeleteButton
        {
            get => (bool)GetValue(ShowDeleteButtonProperty);
            set => SetValue(ShowDeleteButtonProperty, value);
        }
    }
}
