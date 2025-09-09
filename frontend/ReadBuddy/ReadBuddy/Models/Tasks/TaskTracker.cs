using CommunityToolkit.Mvvm.ComponentModel;
using ReadBuddy.Services;
using System;
using System.Threading.Tasks;

namespace ReadBuddy.Models.Tasks
{
    /// <summary>
    /// Represents the status of a backend task and provides helper
    /// methods to poll for updates.
    /// </summary>
    public partial class TaskTracker : ObservableObject
    {
        private readonly TaskTrackerService _service;

        private TimeSpan _currentDelay = TimeSpan.FromSeconds(1);
        private DateTime _lastPoll = DateTime.MinValue;

        /// <summary>
        /// Gets the time remaining until the next allowed poll.
        /// </summary>
        public TimeSpan NextDelay
        {
            get
            {
                var remaining = _currentDelay - (DateTime.UtcNow - _lastPoll);
                return remaining > TimeSpan.Zero ? remaining : TimeSpan.Zero;
            }
        }

        [ObservableProperty]
        private string message = "Starting...";

        [ObservableProperty]
        private double progress;

        [ObservableProperty]
        private bool isCompleted;

        [ObservableProperty]
        private string? result;

        public string TaskId { get; }

        public TaskTracker(string taskId, TaskTrackerService service)
        {
            TaskId = taskId;
            _service = service;
        }

        /// <summary>
        /// Polls the backend for the current task status and updates
        /// local properties.
        /// </summary>
        public async Task PullTaskStatusAsync()
        {
            // Respect adaptive delay between polls
            if (DateTime.UtcNow - _lastPoll < _currentDelay)
                return;
            _lastPoll = DateTime.UtcNow;

            var status = await _service.GetTaskStatusAsync(TaskId);
            if (status == null)
            {
                _currentDelay = TimeSpan.FromSeconds(Math.Min(_currentDelay.TotalSeconds + 1, 10));
                return;
            }

            bool changed = false;

            if (status.Info != null)
            {
                var newMsg = status.Info.Description ?? status.State;
                if (Message != newMsg)
                {
                    Message = newMsg;
                    changed = true;
                }
                if (double.TryParse(status.Info.Step, out double step) &&
                    double.TryParse(status.Info.Out_Of, out double outOf) &&
                    outOf > 0)
                {
                    var newProg = Math.Min(step / outOf * 100.0, 100.0);
                    if (Math.Abs(newProg - Progress) > double.Epsilon)
                    {
                        Progress = newProg;
                        changed = true;
                    }
                }
            }
            else
            {
                if (Message != status.State)
                {
                    Message = status.State;
                    changed = true;
                }
            }

            if (!string.IsNullOrEmpty(status.Result))
            {
                Result = status.Result;
                IsCompleted = true;
                Progress = 100.0;
                changed = true;
            }
            else if (status.State == "SUCCESS" || status.State == "FAILURE")
            {
                IsCompleted = true;
                changed = true;
            }

            // adjust delay based on whether anything changed
            _currentDelay = changed
                ? TimeSpan.FromSeconds(1)
                : TimeSpan.FromSeconds(Math.Min(_currentDelay.TotalSeconds + 1, 10));
        }
    }
}
