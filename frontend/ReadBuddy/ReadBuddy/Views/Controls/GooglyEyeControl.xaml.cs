// ReadBuddy\Views\Controls\GooglyEyeControl.xaml.cs
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Shapes;
using System.Windows.Threading;
using System.Runtime.InteropServices;

namespace ReadBuddy.Views.Controls;

public partial class GooglyEyeControl : UserControl
{
    private readonly DispatcherTimer _timer;
    private Ellipse Pupil => PupilEllipse;

    public static readonly DependencyProperty EdgePaddingProperty =
        DependencyProperty.Register(
            nameof(EdgePadding),
            typeof(double),
            typeof(GooglyEyeControl),
            new PropertyMetadata(5.0));

    public static readonly DependencyProperty EyeSizeProperty =
        DependencyProperty.Register(
            nameof(EyeSize),
            typeof(double),
            typeof(GooglyEyeControl),
            new PropertyMetadata(40.0));

    public static readonly DependencyProperty PupilSizeProperty =
        DependencyProperty.Register(
            nameof(PupilSize),
            typeof(double),
            typeof(GooglyEyeControl),
            new PropertyMetadata(14.0));

    /// <summary>
    /// Determines how close to the edge of the eye the pupil can move.
    /// </summary>
    public double EdgePadding
    {
        get => (double)GetValue(EdgePaddingProperty);
        set => SetValue(EdgePaddingProperty, value);
    }

    /// <summary>
    /// Size of the eye (both width and height).
    /// </summary>
    public double EyeSize
    {
        get => (double)GetValue(EyeSizeProperty);
        set => SetValue(EyeSizeProperty, value);
    }

    /// <summary>
    /// Size of the pupil (both width and height).
    /// </summary>
    public double PupilSize
    {
        get => (double)GetValue(PupilSizeProperty);
        set => SetValue(PupilSizeProperty, value);
    }

    public GooglyEyeControl()
    {
        InitializeComponent();

        _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(30) };
        _timer.Tick += (_, _) => UpdateWithCursor();
        Loaded += (_, _) => _timer.Start();
        Unloaded += (_, _) => _timer.Stop();
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct POINT
    {
        public int X;
        public int Y;
    }

    [DllImport("user32.dll")]
    private static extern bool GetCursorPos(out POINT lpPoint);

    private void UpdateWithCursor()
    {
        GetCursorPos(out POINT p);
        Point point = PointFromScreen(new Point(p.X, p.Y));
        UpdatePupil(point);
    }

    private void UpdatePupil(Point mousePos)
    {
        var center = new Point(ActualWidth / 2, ActualHeight / 2);
        var offset = mousePos - center;
        double maxRadius = (ActualWidth - Pupil.Width) / 2 - EdgePadding;
        if (maxRadius < 0)
            maxRadius = 0;
        if (offset.Length > maxRadius)
        {
            offset.Normalize();
            offset *= maxRadius;
        }
        Canvas.SetLeft(Pupil, center.X - Pupil.Width / 2 + offset.X);
        Canvas.SetTop(Pupil, center.Y - Pupil.Height / 2 + offset.Y);
    }
}
