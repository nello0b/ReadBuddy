using System.Windows;
using System.Windows.Input;
using ReadBuddy.ViewModels;

namespace ReadBuddy.Views;

// This is the code-behind for the WelcomeView WPF window,
// responsible for initializing the view model when the window loads.

public partial class WelcomeView : Window
{
    public WelcomeView(WelcomeViewModel viewModel)
    {
        InitializeComponent();
        DataContext = viewModel;
    }

    private async void Window_Loaded(object sender, RoutedEventArgs e)
    {
        if (DataContext is WelcomeViewModel vm)
            await vm.InitializeAsync();
    }

    private void Border_MouseDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ChangedButton == MouseButton.Left)
        {
            this.DragMove();
        }
    }

}
