using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace ReadBuddy.Converters
{
    public class IsNewToVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is DateTime created)
            {
                var diff = DateTime.UtcNow - created.ToUniversalTime();
                return diff < TimeSpan.FromMinutes(30) ? Visibility.Visible : Visibility.Collapsed;
            }
            return Visibility.Collapsed;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
