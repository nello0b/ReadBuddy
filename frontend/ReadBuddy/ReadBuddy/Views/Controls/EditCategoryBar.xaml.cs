// ReadBuddy\Views\Controls\EditCategoryBar.xaml
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace ReadBuddy.Views.Controls
{
    /// <summary>
    /// Interaction logic for EditCategoryBar.xaml
    /// </summary>
    public partial class EditCategoryBar : UserControl
    {
        public EditCategoryBar()
        {
            InitializeComponent();
        }
        public static readonly DependencyProperty CategoryTextProperty =
        DependencyProperty.Register(nameof(CategoryText), typeof(string), typeof(EditCategoryBar));

        public static readonly DependencyProperty EditCommandProperty =
            DependencyProperty.Register(nameof(EditCommand), typeof(ICommand), typeof(EditCategoryBar));

        public string CategoryText
        {
            get => (string)GetValue(CategoryTextProperty);
            set => SetValue(CategoryTextProperty, value);
        }

        public ICommand? EditCommand
        {
            get => (ICommand?)GetValue(EditCommandProperty);
            set => SetValue(EditCommandProperty, value);
        }
    }
}
