// ReadBuddy\Views\Quiz\QuizReviewView.xaml.cs
using ReadBuddy.ViewModels;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace ReadBuddy.Views
{
    public partial class QuizReviewView : UserControl
    {
        public QuizReviewView(QuizReviewViewModel viewModel)
        {
            InitializeComponent();
            DataContext = viewModel;

            Loaded += (_, __) => AdjustTextBlockWidthsAfterLayout();
            SizeChanged += (_, __) => AdjustTextBlockWidthsAfterLayout();
        }

        private void AdjustTextBlockWidthsAfterLayout()
        {
            Dispatcher.BeginInvoke(new Action(AdjustWidths),
                                   System.Windows.Threading.DispatcherPriority.Loaded);
        }

        private void AdjustWidths()
        {
            double targetWidth = ReviewItemsControl.ActualWidth - 200;

            foreach (var item in ReviewItemsControl.Items)
            {
                // ItemsControl generates ContentPresenter containers
                if (ReviewItemsControl.ItemContainerGenerator.ContainerFromItem(item)
                    is not ContentPresenter container)
                    continue;

                SetMaxWidthOnChild<TextBlock>(container, "QuestionContentText", targetWidth);
                SetMaxWidthOnChild<TextBlock>(container, "CorrectAnswerText", targetWidth);
                SetMaxWidthOnChild<TextBlock>(container, "UserAnswerText", targetWidth);
            }
        }

        private void SetMaxWidthOnChild<T>(DependencyObject parent, string childName, double width) where T : FrameworkElement
        {
            var child = FindChild<T>(parent, childName);
            if (child != null)
                child.MaxWidth = width;
        }

        private T? FindChild<T>(DependencyObject parent, string childName) where T : FrameworkElement
        {
            for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
            {
                var child = VisualTreeHelper.GetChild(parent, i);
                if (child is T typed && typed.Name == childName)
                    return typed;

                var result = FindChild<T>(child, childName);
                if (result != null)
                    return result;
            }
            return null;
        }
    }
}

