// ReadBuddy\Views\Home\OcrHomeView.xaml.cs
using System.Windows.Controls;
using ReadBuddy.ViewModels.Home;

namespace ReadBuddy.Views.Home
{
    public partial class OcrHomeView : UserControl
    {
        private readonly OcrHomeViewModel _viewModel;

        public OcrHomeView(OcrHomeViewModel viewModel)
        {
            InitializeComponent();
            _viewModel = viewModel;
            DataContext = _viewModel;

            _viewModel.PropertyChanged += (_, e) =>
            {
                if (e.PropertyName == nameof(OcrHomeViewModel.CurrentOcr) &&
                    _viewModel.CurrentOcr != null)
                {
                    OcrControl.ReplaceWith(_viewModel.CurrentOcr);
                }
            };

            _viewModel.RequestBack += OnRequestBack;
        }

        private void OnRequestBack()
        {
            if (OcrControl.StopCommand.CanExecute(null))
            {
                OcrControl.StopCommand.Execute(null);
            }
        }
    }
}
