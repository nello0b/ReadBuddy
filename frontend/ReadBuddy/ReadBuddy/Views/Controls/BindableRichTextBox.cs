//ReadBuddy\Views\Controls\BindableRichTextBox.cs
using System.Windows.Controls;
using System.Windows;
using System.Windows.Markup;
using System.Windows.Documents;

namespace ReadBuddy.Views.Controls
{
    public class BindableRichTextBox : RichTextBox
    {
        public static readonly DependencyProperty DocumentXamlProperty =
            DependencyProperty.Register(
                nameof(DocumentXaml),
                typeof(string),
                typeof(BindableRichTextBox),
                new PropertyMetadata(null, OnDocumentXamlChanged));

        public string DocumentXaml
        {
            get => (string)GetValue(DocumentXamlProperty);
            set => SetValue(DocumentXamlProperty, value);
        }

        private static void OnDocumentXamlChanged(DependencyObject d, DependencyPropertyChangedEventArgs e)
        {
            if (e.NewValue is string xaml && !string.IsNullOrWhiteSpace(xaml))
            {
                try
                {
                    var doc = (FlowDocument)XamlReader.Parse(xaml);
                    ((BindableRichTextBox)d).Document = doc;
                }
                catch
                {
                    // Optionally handle invalid XAML
                    ((BindableRichTextBox)d).Document = new FlowDocument(new Paragraph(new Run("Error loading summary.")));
                }
            }
        }
    }
}
