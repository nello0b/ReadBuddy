using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace ReadBuddy.Converters
{
    public class BoolToVisibilityConverter : IValueConverter
    {
        public bool Invert { get; set; } = false;

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool flag)
                return (flag ^ Invert) ? Visibility.Visible : Visibility.Collapsed;

            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is Visibility vis)
                return (vis == Visibility.Visible) ^ Invert;

            return false;
        }
    }
}
