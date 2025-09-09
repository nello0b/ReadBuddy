// ReadBuddy\Converters\IndexToNumberConverter.cs
using System;
using System.Globalization;
using System.Windows.Data;

namespace ReadBuddy.Converters
{
    public class IndexToNumberConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is int i && i >= 0)
                return $"{i + 1}.";

            return "?";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) =>
            throw new NotImplementedException();
    }
}
