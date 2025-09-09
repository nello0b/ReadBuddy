// ReadBuddy\ViewModels\Home\OcrHomeViewModel.cs
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Views.Controls;
using ReadBuddy.Views.Summary;
using SummaryModel = ReadBuddy.Models.Summary.Summary;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Services;


namespace ReadBuddy.ViewModels.Home
{
    public partial class OcrHomeViewModel : ObservableObject
    {
        /// <summary>
        /// The loaded OCR view model displayed in OcrImageControl.
        /// </summary>
        [ObservableProperty]
        private OcrImageViewModel? currentOcr;
        [ObservableProperty]
        private string summeryButtonText = "Create Summary";
        [ObservableProperty]
        private bool isSummaryGenerating = false;

        private bool hasSummary = false;

        // Cache the existing summary to avoid fetching it again
        private SummaryModel? existingSummary = null;

        // Track the currently open summary window
        private SummaryWindow? currentSummaryWindow = null;

        private readonly SummaryRepository _summaryRepository;
        private readonly TaskTrackerService _taskTrackerService;
        private readonly IDialogService _dialogService;


        /// <summary>
        /// Triggered when the user presses the Back button.
        /// </summary>
        public event Action? RequestBack;

        public OcrHomeViewModel(SummaryRepository summaryRepository, TaskTrackerService taskTrackerService, IDialogService dialogService)
        {
            _summaryRepository = summaryRepository;
            _taskTrackerService = taskTrackerService;
            _dialogService = dialogService;
            BackCommand = new RelayCommand(OnBack);
            EditCategoryCommand = new RelayCommand(OnEditCategoryRequested);
        }

        public IRelayCommand BackCommand { get; }
        public IRelayCommand EditCategoryCommand { get; }

        /// <summary>
        /// Called by the hub to inject the OCR result to display.
        /// </summary>
        public async void LoadOcr(OcrImageViewModel vm)
        {
            CurrentOcr = vm;
            await CheckForExistingSummary();
        }

        /// <summary>
        /// Checks if a summary exists for the current extraction and updates the button text accordingly.
        /// </summary>
        private async Task CheckForExistingSummary()
        {
            if (CurrentOcr == null || string.IsNullOrEmpty(CurrentOcr.ExtractionId))
            {
                hasSummary = false;
                SummeryButtonText = "Create Summary";
                existingSummary = null;
                return;
            }

            try
            {
                var existingSummaries = await _summaryRepository.GetSummariesBySourceAsync(CurrentOcr.ExtractionId);

                if (existingSummaries != null && existingSummaries.Any())
                {
                    hasSummary = true;
                    SummeryButtonText = "Show Summary";
                    existingSummary = existingSummaries.First(); // Cache the existing summary'
                }
                else
                {
                    hasSummary = false;
                    SummeryButtonText = "Create Summary";
                    existingSummary = null;
                }
            }
            catch (Exception ex)
            {
                // If there's an error checking for summaries, default to "Create Summary"
                hasSummary = false;
                SummeryButtonText = "Create Summary";
                existingSummary = null;
                System.Diagnostics.Debug.WriteLine($"Error checking for existing summary: {ex.Message}");
            }
        }

        /// <summary>
        /// Clears the currently loaded OCR data so the view starts fresh
        /// when returning to the home screen.
        /// </summary>
        public void ClearOcr()
        {
            if (CurrentOcr != null)
            {
                CurrentOcr.ImageSource = null;
                CurrentOcr.OcrResult = null;
                CurrentOcr.AudioChunks.Clear();
                CurrentOcr.Category = string.Empty;
                CurrentOcr.ExtractionId = string.Empty;
            }

            // Close the summary window if it's open
            if (currentSummaryWindow != null)
            {
                currentSummaryWindow.Close();
                currentSummaryWindow = null;
            }

            // Reset summary state
            hasSummary = false;
            existingSummary = null;
            IsSummaryGenerating = false;
            SummeryButtonText = "Create Summary";
        }

        private void OnBack()
        {
            // Close the summary window if it's open
            if (currentSummaryWindow != null)
            {
                currentSummaryWindow.Close();
                currentSummaryWindow = null;
            }
            
            RequestBack?.Invoke();
        }


        [RelayCommand]
        private async Task ShowSummary()
        {
            if (CurrentOcr == null || string.IsNullOrEmpty(CurrentOcr.ExtractionId))
                return;

            // If we have an existing summary, show it
            if (hasSummary && existingSummary != null)
            {
                // Close existing window if one is already open
                if (currentSummaryWindow != null)
                {
                    currentSummaryWindow.Close();
                }

                currentSummaryWindow = new SummaryWindow(existingSummary)
                {
                    Owner = Application.Current.MainWindow
                };
                
                // Handle window closure to clean up reference
                currentSummaryWindow.Closed += (sender, e) => currentSummaryWindow = null;
                
                currentSummaryWindow.Show();
                return;
            }

            // If no existing summary, start generation
            await StartSummaryGeneration();
        }

        private async Task StartSummaryGeneration()
        {
            if (CurrentOcr == null || string.IsNullOrEmpty(CurrentOcr.ExtractionId))
                return;

            try
            {
                // Update UI to show generation in progress
                IsSummaryGenerating = true;
                SummeryButtonText = "Generating Summary...";

                // Start the summary generation task
                var task = await _summaryRepository.CreateFromSourceAsync(CurrentOcr.ExtractionId);

                if (task != null && !string.IsNullOrEmpty(task.Task_Id))
                {
                    // Track the task progress
                    await TrackSummaryGenerationTask(task.Task_Id);
                }
                else
                {
                    // Generation failed to start
                    IsSummaryGenerating = false;
                    SummeryButtonText = "Create Summary";
                    ShowErrorMessage("Failed to Start Generation",
                        "Unable to start summary generation. Please try again later.");
                    System.Diagnostics.Debug.WriteLine("Failed to start summary generation - no task ID received");
                }
            }
            catch (Exception ex)
            {
                // Handle generation error
                IsSummaryGenerating = false;
                SummeryButtonText = "Create Summary";
                ShowErrorMessage("Generation Error",
                    $"An error occurred while starting summary generation:\n\n{ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Error starting summary generation: {ex.Message}");
            }
        }

        private async Task TrackSummaryGenerationTask(string taskId)
        {
            const int maxAttempts = 60; // Max 5 minutes (60 * 5 seconds)
            int attempts = 0;

            while (attempts < maxAttempts)
            {
                try
                {
                    var status = await _taskTrackerService.GetTaskStatusAsync(taskId);

                    if (status == null)
                    {
                        await Task.Delay(5000); // Wait 5 seconds before retry
                        attempts++;
                        continue;
                    }

                    switch (status.State?.ToLower())
                    {
                        case "success":
                            // Task completed successfully, refresh summary data
                            await OnSummaryGenerationCompleted();
                            return;

                        case "failure":
                            // Task failed
                            IsSummaryGenerating = false;
                            SummeryButtonText = "Create Summary";
                            ShowErrorMessage("Summary Generation Failed",
                                GetUserFriendlyErrorMessage(status.Traceback));
                            System.Diagnostics.Debug.WriteLine($"Summary generation failed");
                            return;

                        case "pending":
                        case "started":
                        default:
                            // Task still in progress, update UI if we have progress info
                            if (status.Info != null && !string.IsNullOrEmpty(status.Info.Description))
                            {
                                SummeryButtonText = $"Generating...";
                            }
                            break;
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"Error tracking task {taskId}: {ex.Message}");
                }

                // Wait before next check
                await Task.Delay(5000); // Check every 5 seconds
                attempts++;
            }

            // Timeout - task took too long
            IsSummaryGenerating = false;
            SummeryButtonText = "Create Summary";
            ShowErrorMessage("Generation Timeout",
                "Summary generation is taking longer than expected. Please try again later.");
            System.Diagnostics.Debug.WriteLine($"Summary generation timeout for task {taskId}");
        }

        private async Task OnSummaryGenerationCompleted()
        {
            try
            {
                // Refresh the summary data from the backend
                await CheckForExistingSummary();

                // If we found the new summary, update the UI
                if (hasSummary)
                {
                    IsSummaryGenerating = false;
                    SummeryButtonText = "Show Summary";
                }
                else
                {
                    // Something went wrong - summary should exist but doesn't
                    IsSummaryGenerating = false;
                    SummeryButtonText = "Create Summary";
                    ShowErrorMessage("Generation Completed with Issues",
                        "Summary generation completed but the result could not be retrieved. Please try again.");
                    System.Diagnostics.Debug.WriteLine("Summary generation completed but no summary found");
                }
            }
            catch (Exception ex)
            {
                IsSummaryGenerating = false;
                SummeryButtonText = "Create Summary";
                ShowErrorMessage("Error Retrieving Summary",
                    $"An error occurred while retrieving the generated summary:\n\n{ex.Message}");
                System.Diagnostics.Debug.WriteLine($"Error completing summary generation: {ex.Message}");
            }
        }

        /// <summary>
        /// Shows an error message box to the user.
        /// </summary>
        private void ShowErrorMessage(string title, string message)
        {
            Application.Current.Dispatcher.Invoke(() =>
            {
                _dialogService.ShowError(message, title);
            });
        }

        /// <summary>
        /// Converts technical error messages into user-friendly ones.
        /// </summary>
        private string GetUserFriendlyErrorMessage(string? technicalError)
        {
            if (string.IsNullOrEmpty(technicalError))
                return "An unknown error occurred during summary generation.";

            // Convert common technical errors to user-friendly messages
            var lowerError = technicalError.ToLower();

            if (lowerError.Contains("timeout") || lowerError.Contains("connection"))
                return "Connection timeout. Please check your internet connection and try again.";

            if (lowerError.Contains("authentication") || lowerError.Contains("unauthorized"))
                return "Authentication error. Please log in again.";

            if (lowerError.Contains("rate limit") || lowerError.Contains("too many requests"))
                return "Too many requests. Please wait a moment and try again.";

            if (lowerError.Contains("server error") || lowerError.Contains("internal"))
                return "Server error. Please try again later.";

            if (lowerError.Contains("not found") || lowerError.Contains("404"))
                return "The requested content was not found. Please try again.";

            // For other errors, show a generic message
            return "An error occurred during summary generation. Please try again later.";
        }

        private void OnEditCategoryRequested()
        {
            if (CurrentOcr == null)
                return;

            Application.Current.Dispatcher.Invoke(() =>
            {
                var dialog = new EditCategoryDialog(CurrentOcr.Category, CurrentOcr.ExtractionId);
                dialog.Owner = Application.Current.Windows.OfType<Window>().FirstOrDefault(w => w.IsActive);

                if (dialog.ShowDialog() == true && dialog.DataContext is ViewModels.EditCategoryDialogViewModel vm)
                {
                    CurrentOcr.Category = vm.SelectedCategory;
                }
            });
        }
    }
}
