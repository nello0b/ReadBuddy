// ReadBuddy\Services\TaskTrackingHistoryService.cs
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Base class for history services that track <see cref="TaskTracker"/> objects
    /// and replace them with summary items once completed.
    /// </summary>
    public abstract class TaskTrackingHistoryService<TSummary>
    {
        private CancellationTokenSource? _taskPollingCts;
        protected readonly HashSet<string> _taskIds = new();
        protected readonly HashSet<string> _summaryIds = new();
        protected readonly IDialogService _dialogService;

        protected TaskTrackingHistoryService(IDialogService dialogService)
        {
            _dialogService = dialogService;
        }

        /// <summary>
        /// Collection mixing <see cref="TaskTracker"/> and summary objects.
        /// </summary>
        public ObservableCollection<object> CombinedItems { get; } = new();

        /// <summary>
        /// Inserts a new task into <see cref="CombinedItems"/> and starts polling
        /// for updates if needed.
        /// </summary>
        public void AddTask(TaskTracker task)
        {
            AddTaskItem(task, insertAtBeginning: true);
            if (_taskPollingCts == null || _taskPollingCts.IsCancellationRequested)
            {
                StartTaskTrackerUpdatesLoop();
            }
        }

        protected void AddTaskItem(TaskTracker task, bool insertAtBeginning = false)
        {
            if (_taskIds.Contains(task.TaskId))
                return;

            if (insertAtBeginning)
                CombinedItems.Insert(0, task);
            else
                CombinedItems.Add(task);

            _taskIds.Add(task.TaskId);
        }

        protected void AddSummaryItem(TSummary summary)
        {
            var id = GetSummaryId(summary);
            if (_summaryIds.Contains(id))
                return;

            CombinedItems.Add(summary);
            _summaryIds.Add(id);
        }

        protected void ClearAllItems()
        {
            CombinedItems.Clear();
            _taskIds.Clear();
            _summaryIds.Clear();
        }

        /// <summary>
        /// Removes all items of the specified type from <see cref="CombinedItems"/>.
        /// </summary>
        public void ClearOfType<T>()
        {
            for (int i = CombinedItems.Count - 1; i >= 0; i--)
            {
                var obj = CombinedItems[i];
                if (obj is T)
                {
                    CombinedItems.RemoveAt(i);
                    if (obj is TaskTracker tt)
                        _taskIds.Remove(tt.TaskId);
                    else if (obj is TSummary summary)
                        _summaryIds.Remove(GetSummaryId(summary));
                }
            }
        }

        /// <summary>
        /// Starts a background loop that polls each <see cref="TaskTracker"/> for
        /// status updates and replaces completed tasks with summaries.
        /// </summary>
        public void StartTaskTrackerUpdatesLoop()
        {
            _taskPollingCts?.Cancel();
            _taskPollingCts = new CancellationTokenSource();
            var token = _taskPollingCts.Token;

            Task.Run(async () =>
            {
                while (!token.IsCancellationRequested)
                {
                    var taskItems = App.Current.Dispatcher.Invoke(() =>
                        CombinedItems.OfType<TaskTracker>().ToList());

                    foreach (var task in taskItems)
                    {
                        if (!task.IsCompleted)
                        {
                            await task.PullTaskStatusAsync();
                        }
                    }

                    var completedTasks = taskItems.Where(t => t.IsCompleted).ToList();
                    var results = new List<(TaskTracker Task, TSummary? Summary)>();

                    foreach (var task in completedTasks)
                    {
                        TSummary? summary = default;
                        if (!string.IsNullOrEmpty(task.Result))
                        {
                            summary = await FetchSummaryByIdAsync(task.Result);
                        }
                        results.Add((task, summary));
                    }

                    if (completedTasks.Any())
                    {
                        await App.Current.Dispatcher.InvokeAsync(() =>
                        {
                            foreach (var (task, summary) in results)
                            {
                                CombinedItems.Remove(task);
                                _taskIds.Remove(task.TaskId);
                                if (summary != null)
                                {
                                    AddSummaryItem(summary);
                                }
                            }

                            SortSummaries();

                            if (!CombinedItems.OfType<TaskTracker>().Any())
                            {
                                _taskPollingCts?.Cancel();
                            }
                        });

                        await OnTasksCompletedAsync(results);
                    }

                    taskItems = App.Current.Dispatcher.Invoke(() =>
                        CombinedItems.OfType<TaskTracker>().ToList());
                    var wait = taskItems.Count > 0
                        ? taskItems.Min(t => t.NextDelay)
                        : TimeSpan.FromSeconds(1);

                    await Task.Delay(wait, token);
                }
            }, token);
        }

        /// <summary>
        /// Called whenever tasks have completed and summaries were inserted. Derived
        /// classes can override to perform additional work.
        /// </summary>
        protected virtual Task OnTasksCompletedAsync(List<(TaskTracker Task, TSummary? Summary)> results)
        {
            foreach (var (task, summary) in results)
            {
                if (summary == null)
                {
                    var message = string.IsNullOrWhiteSpace(task.Message) ||
                                   task.Message.StartsWith("Task is",
                                       StringComparison.OrdinalIgnoreCase)
                        ? GetDefaultFailureMessage()
                        : task.Message;

                    Application.Current.Dispatcher.Invoke(() =>
                    {
                        _dialogService.ShowError(message, GetFailureDialogTitle());
                    });
                }
            }

            return Task.CompletedTask;
        }

        /// <summary>
        /// Title shown in the failure dialog when a task finishes without a summary.
        /// </summary>
        protected virtual string GetFailureDialogTitle() => "Task Failed";

        /// <summary>
        /// Default message displayed in the failure dialog when the task message is empty.
        /// </summary>
        protected virtual string GetDefaultFailureMessage() => "Task failed.";

        /// <summary>
        /// Retrieves the summary object for the completed task ID.
        /// </summary>
        protected abstract Task<TSummary?> FetchSummaryByIdAsync(string id);

        /// <summary>
        /// Retrieves the identifier value from a summary item. Used to prevent
        /// duplicate entries in <see cref="CombinedItems"/>.
        /// </summary>
        protected abstract string GetSummaryId(TSummary summary);

        /// <summary>
        /// Sorts the summary items inside <see cref="CombinedItems"/> while preserving
        /// existing tasks.
        /// </summary>
        protected abstract void SortSummaries();
    }
}

