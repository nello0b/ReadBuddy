// ReadBuddy/Animations/GridLengthAnimation.cs
using System;
using System.Windows;
using System.Windows.Media.Animation;

namespace ReadBuddy.Animations
{
    public class GridLengthAnimation : AnimationTimeline
    {
        public override Type TargetPropertyType => typeof(GridLength);

        public GridLength From { get; set; }
        public GridLength To { get; set; }

        public override object GetCurrentValue(object defaultOriginValue, object defaultDestinationValue, AnimationClock animationClock)
        {
            double fromValue = From.Value;
            double toValue = To.Value;

            if (fromValue > toValue)
            {
                return new GridLength((1 - animationClock.CurrentProgress.Value) * (fromValue - toValue) + toValue, GridUnitType.Pixel);
            }
            else
            {
                return new GridLength(animationClock.CurrentProgress.Value * (toValue - fromValue) + fromValue, GridUnitType.Pixel);
            }
        }

        protected override Freezable CreateInstanceCore()
        {
            return new GridLengthAnimation { From = this.From, To = this.To, Duration = this.Duration };
        }
    }
}
