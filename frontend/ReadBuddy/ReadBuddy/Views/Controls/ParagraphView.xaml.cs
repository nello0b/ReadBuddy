//ReadBuddy\Views\Controls\ParagraphView.xaml.cs
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace ReadBuddy.Views.Controls
{
    public partial class ParagraphView : UserControl
    {
        public ParagraphView()
        {
            InitializeComponent();
        }

        public static readonly DependencyProperty CopyCommandProperty =
            DependencyProperty.Register(nameof(CopyCommand), typeof(ICommand), typeof(ParagraphView));

        public static readonly DependencyProperty PlayCommandProperty =
            DependencyProperty.Register(nameof(PlayCommand), typeof(ICommand), typeof(ParagraphView));

        public static readonly DependencyProperty MouseEnterCommandProperty =
    DependencyProperty.Register(nameof(MouseEnterCommand), typeof(ICommand), typeof(ParagraphView));

        public static readonly DependencyProperty MouseLeaveCommandProperty =
            DependencyProperty.Register(nameof(MouseLeaveCommand), typeof(ICommand), typeof(ParagraphView));


        public ICommand? MouseEnterCommand
        {
            get => (ICommand?)GetValue(MouseEnterCommandProperty);
            set => SetValue(MouseEnterCommandProperty, value);
        }

        public ICommand? MouseLeaveCommand
        {
            get => (ICommand?)GetValue(MouseLeaveCommandProperty);
            set => SetValue(MouseLeaveCommandProperty, value);
        }
        public ICommand? CopyCommand
        {
            get => (ICommand?)GetValue(CopyCommandProperty);
            set => SetValue(CopyCommandProperty, value);
        }

        public ICommand? PlayCommand
        {
            get => (ICommand?)GetValue(PlayCommandProperty);
            set => SetValue(PlayCommandProperty, value);
        }

        private void OnMouseEnterHandler(object sender, MouseEventArgs e)
        {
            if (MouseEnterCommand?.CanExecute(DataContext) == true)
                MouseEnterCommand.Execute(DataContext);
        }

        private void OnMouseLeaveHandler(object sender, MouseEventArgs e)
        {
            if (MouseLeaveCommand?.CanExecute(DataContext) == true)
                MouseLeaveCommand.Execute(DataContext);
        }

    }
}
