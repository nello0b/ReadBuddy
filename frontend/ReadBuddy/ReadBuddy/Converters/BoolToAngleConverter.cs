using System;
using System.Globalization;
using System.Windows.Data;

namespace ReadBuddy.Converters
{
    public class BoolToAngleConverter : IValueConverter
    {
        public double TrueAngle { get; set; } = 0;
        public double FalseAngle { get; set; } = 180;

        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is bool b)
                return b ? TrueAngle : FalseAngle;
            return TrueAngle;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) =>
            throw new NotImplementedException();
    }
}
