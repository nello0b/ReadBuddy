using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace ReadBuddy.Views.Controls
{
    public partial class CustomMessageBox : Window
    {
        public CustomMessageBox(string message, string title, MessageBoxButton buttons)
        {
            InitializeComponent();
            TitleText.Text = title;
            MessageText.Text = message;
            CreateButtons(buttons);
        }

        private void CreateButtons(MessageBoxButton buttons)
        {
            var style = (Style)FindResource("MessageBoxActionButtonStyle");
            if (buttons == MessageBoxButton.YesNo)
            {
                var yes = new Button { Content = "Yes", Style = style };
                yes.Click += (s, e) => { DialogResult = true; };
                var no = new Button { Content = "No", Style = style };
                no.Click += (s, e) => { DialogResult = false; };
                ButtonPanel.Children.Add(yes);
                ButtonPanel.Children.Add(no);
            }
            else
            {
                var ok = new Button { Content = "OK", Style = style, Margin = new Thickness(0) };
                ok.Click += (s, e) => { DialogResult = true; };
                ButtonPanel.Children.Add(ok);
            }
        }

        private void Border_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }
    }
}
