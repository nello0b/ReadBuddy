// ReadBuddy\Views\Controls\EditCategoryDialog.xaml.cs
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Services;
using System.Windows;
using System.Windows.Input;

namespace ReadBuddy.Views.Controls
{
    public partial class EditCategoryDialog : Window
    {
        public EditCategoryDialog(string currentCategory, string extractionId)
        {
            InitializeComponent();
            var repo = App.ServiceProvider.GetRequiredService<ExtractionRepository>();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            DataContext = new ViewModels.EditCategoryDialogViewModel(currentCategory, this, repo, extractionId, dialogs);
        }
        private void Border_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                this.DragMove();
            }
        }

    }
}
