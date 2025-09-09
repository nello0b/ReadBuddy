// ReadBuddy\Views\Controls\AnswerListControl.xaml.cs
using System;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using ReadBuddy.Models.Quiz;

namespace ReadBuddy.Views.Controls
{
    public partial class AnswerListControl : UserControl
    {
        public AnswerListControl()
        {
            InitializeComponent();
        }

        // ─────────────────── dependency properties ────────────────────────
        public static readonly DependencyProperty AnswersProperty =
            DependencyProperty.Register(nameof(Answers),
                                        typeof(IEnumerable<Answer>),
                                        typeof(AnswerListControl));

        public static readonly DependencyProperty SelectedAnswerProperty =
            DependencyProperty.Register(nameof(SelectedAnswer),
                                        typeof(Answer),
                                        typeof(AnswerListControl));

        public IEnumerable<Answer> Answers
        {
            get => (IEnumerable<Answer>)GetValue(AnswersProperty);
            set => SetValue(AnswersProperty, value);
        }

        public Answer SelectedAnswer
        {
            get => (Answer)GetValue(SelectedAnswerProperty);
            set => SetValue(SelectedAnswerProperty, value);
        }

        // ─────────────────── event handlers ───────────────────────────────
        private void AnswerListControl_Loaded(object sender, RoutedEventArgs e) =>
            AdjustAnswerWidthsAfterLayout();

        // Run after layout pass
        private void AdjustAnswerWidthsAfterLayout() =>
            Dispatcher.BeginInvoke(new Action(AdjustAnswerWidths),
                                   System.Windows.Threading.DispatcherPriority.Loaded);

        // ─────────────────── core logic ───────────────────────────────────
        private void AdjustAnswerWidths()
        {
            if (AnswerListBox == null || AnswerListBox.ActualWidth <= 0) return;

            double targetWidth = Math.Max(0, AnswerListBox.ActualWidth - 100); // 50 = padding/margin

            foreach (var item in AnswerListBox.Items)
            {
                if (AnswerListBox.ItemContainerGenerator.ContainerFromItem(item) is not ListBoxItem container)
                    continue;

                // Find the TextBlock inside this container
                if (FindVisualChild<TextBlock>(container) is { } tb &&
                    Math.Abs(tb.MaxWidth - targetWidth) > 1)
                {
                    tb.MaxWidth = targetWidth;
                }
            }
        }

        private static T? FindVisualChild<T>(DependencyObject parent) where T : DependencyObject
        {
            for (int i = 0; i < VisualTreeHelper.GetChildrenCount(parent); i++)
            {
                DependencyObject child = VisualTreeHelper.GetChild(parent, i);
                if (child is T typed) return typed;

                if (FindVisualChild<T>(child) is T descendant) return descendant;
            }
            return null;
        }
    }
}
