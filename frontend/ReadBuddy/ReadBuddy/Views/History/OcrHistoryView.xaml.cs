// ReadBuddy\Views\History\OcrHistoryView.xaml.cs
using System.Windows.Controls;
using ReadBuddy.ViewModels;

namespace ReadBuddy.Views
{
    public partial class OcrHistoryView : UserControl
    {
        private readonly OcrHistoryViewModel _vm;

        public OcrHistoryView(OcrHistoryViewModel vm)
        {
            InitializeComponent();
            _vm = vm;
            DataContext = _vm;

            // Whenever CurrentOcr changes, copy it into the control
            _vm.PropertyChanged += (_, e) =>
            {
                if (e.PropertyName == nameof(OcrHistoryViewModel.CurrentOcr) &&
                    _vm.CurrentOcr != null)
                {
                    OcrControl.ReplaceWith(_vm.CurrentOcr);
                }
            };
        }
    }
}
