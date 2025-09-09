// ReadBuddy\Converters\InverseVisibilityConverter.cs
using System;
using System.Globalization;
using System.Windows.Data;

namespace ReadBuddy.Converters
{
    public class IndexToLetterConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is int i && i >= 0 && i < 26)
                return $"{(char)('A' + i)}.";

            return "?";
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) =>
            throw new NotImplementedException();
    }
}
