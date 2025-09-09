namespace ReadBuddy.Services
{
    public static class GeometryHelper
    {
        public static double GetRegionHeight(List<int> polygon)
        {
            double left = Math.Abs(polygon[7] - polygon[1]);
            double right = Math.Abs(polygon[5] - polygon[3]);
            return (left + right) / 2.0;
        }

        public static double GetRegionWidth(List<int> polygon)
        {
            double top = Math.Abs(polygon[2] - polygon[0]);
            double bottom = Math.Abs(polygon[6] - polygon[4]);
            return (top + bottom) / 2.0;
        }
    }
}
