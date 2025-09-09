using System.Windows;
using ReadBuddy.Views.Controls;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Default implementation of <see cref="IDialogService"/> using
    /// <see cref="MessageBox"/>.
    /// </summary>
    public class DialogService : IDialogService
    {
        public void ShowError(string message, string? title = null)
        {
            ShowBox(message, title ?? "Error", MessageBoxButton.OK);
        }

        public void ShowInfo(string message, string? title = null)
        {
            ShowBox(message, title ?? "Info", MessageBoxButton.OK);
        }

        public bool ShowConfirmation(string message, string? title = null)
        {
            return ShowBox(message, title ?? "Confirmation", MessageBoxButton.YesNo);
        }

        private bool ShowBox(string message, string title, MessageBoxButton buttons)
        {
            var box = new CustomMessageBox(message, title, buttons)
            {
                Owner = Application.Current.MainWindow
            };
            return box.ShowDialog() == true;
        }
    }
}
