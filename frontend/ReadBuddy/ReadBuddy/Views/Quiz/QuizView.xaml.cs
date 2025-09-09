using ReadBuddy.ViewModels;
using ReadBuddy.Services;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

namespace ReadBuddy.Views
{
    /// <summary>
    /// Interaction logic for QuizView.xaml
    /// </summary>
    public partial class QuizView : UserControl
    {
        private readonly QuizViewModel _viewModel;

        #region Constructor

        /// <summary>
        /// Initializes a new instance of the QuizView class.
        /// </summary>
        /// <param name="viewModel">The QuizViewModel to bind to the view.</param>
        public QuizView(QuizViewModel viewModel)
        {
            InitializeComponent();
            _viewModel = viewModel;
            DataContext = viewModel;
            _viewModel.HighlightRequested += Vm_HighlightRequested;
        }

        #endregion

        private void Vm_HighlightRequested(int index)
        {
            Dispatcher.Invoke(() => UpdateHighlights(index));
        }

        private void UpdateHighlights(int index)
        {
            if (QuestionTextBlock != null)
                QuestionTextBlock.Background = Brushes.Transparent;

            if (AnswersControl?.AnswerListBox != null)
            {
                var listBox = AnswersControl.AnswerListBox;
                for (int i = 0; i < listBox.Items.Count; i++)
                {
                    if (listBox.ItemContainerGenerator.ContainerFromIndex(i) is ListBoxItem item)
                    {
                        var highlight = VisualTreeHelperExtensions.FindNamedVisualChild<Border>(item, "HighlightBorder");
                        if (highlight != null)
                            highlight.Background = Brushes.Transparent;
                    }
                }
            }

            if (index == 0 && QuestionTextBlock != null)
            {
                QuestionTextBlock.Background = (Brush)Application.Current.Resources["TransparentYellowBrush"];
            }
            else if (index > 0 && AnswersControl?.AnswerListBox != null)
            {
                int idx = index - 1;
                var listBox = AnswersControl.AnswerListBox;
                if (listBox.ItemContainerGenerator.ContainerFromIndex(idx) is ListBoxItem item)
                {
                    var highlight = VisualTreeHelperExtensions.FindNamedVisualChild<Border>(item, "HighlightBorder");
                    if (highlight != null)
                        highlight.Background = (Brush)Application.Current.Resources["TransparentYellowBrush"];
                }
            }
        }
    }
}
