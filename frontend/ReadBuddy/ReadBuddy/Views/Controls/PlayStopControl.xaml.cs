// ReadBuddy\Views\Controls\PlayStopControl.xaml.cs
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using MaterialDesignThemes.Wpf;

namespace ReadBuddy.Views.Controls
{
    public partial class PlayStopControl : UserControl
    {
        // Commands
        public static readonly DependencyProperty PlayCommandProperty =
            DependencyProperty.Register(nameof(PlayCommand), typeof(ICommand), typeof(PlayStopControl));

        public static readonly DependencyProperty StopCommandProperty =
            DependencyProperty.Register(nameof(StopCommand), typeof(ICommand), typeof(PlayStopControl));

        // Icon kinds
        public static readonly DependencyProperty PlayIconProperty =
            DependencyProperty.Register(nameof(PlayIcon), typeof(PackIconKind), typeof(PlayStopControl),
                new PropertyMetadata(PackIconKind.Play));

        public static readonly DependencyProperty StopIconProperty =
            DependencyProperty.Register(nameof(StopIcon), typeof(PackIconKind), typeof(PlayStopControl),
                new PropertyMetadata(PackIconKind.Stop));

        public ICommand PlayCommand
        {
            get => (ICommand)GetValue(PlayCommandProperty);
            set => SetValue(PlayCommandProperty, value);
        }

        public ICommand StopCommand
        {
            get => (ICommand)GetValue(StopCommandProperty);
            set => SetValue(StopCommandProperty, value);
        }

        public PackIconKind PlayIcon
        {
            get => (PackIconKind)GetValue(PlayIconProperty);
            set => SetValue(PlayIconProperty, value);
        }

        public PackIconKind StopIcon
        {
            get => (PackIconKind)GetValue(StopIconProperty);
            set => SetValue(StopIconProperty, value);
        }

        public PlayStopControl()
        {
            InitializeComponent();
        }

    }
}
