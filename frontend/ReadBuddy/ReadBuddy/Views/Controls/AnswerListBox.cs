// ReadBuddy\Views\Controls\AnswerListBox.cs
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows;

namespace ReadBuddy.Views.Controls
{
    public class AnswerListBox : ListBox
    {
        protected override void PrepareContainerForItemOverride(
            DependencyObject element, object item)
        {
            base.PrepareContainerForItemOverride(element, item);

            if (element is ListBoxItem container &&
                FindVisualChild<TextBlock>(container) is { } tb)
            {
                double maxWidth = ActualWidth - 100;
                tb.MaxWidth = maxWidth > 0 ? maxWidth : 0;
            }
        }

        private static T? FindVisualChild<T>(DependencyObject parent) where T : DependencyObject
        {
            for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
            {
                var child = VisualTreeHelper.GetChild(parent, i);
                if (child is T typed) return typed;

                var descendant = FindVisualChild<T>(child);
                if (descendant != null) return descendant;
            }
            return null;
        }
    }
}
