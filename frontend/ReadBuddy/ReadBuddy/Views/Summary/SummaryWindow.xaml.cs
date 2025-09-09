// ReadBuddy\Views\Summary\SummaryWindow.xaml.cs
using ReadBuddy.ViewModels.Summary;
using System;
using System.ComponentModel;
using System.Windows;
using System.Windows.Documents;
using System.Windows.Media;
using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Services;
using SummaryModel = ReadBuddy.Models.Summary.Summary;

namespace ReadBuddy.Views.Summary
{
    public partial class SummaryWindow : Window
    {
        private readonly SummaryViewModel _viewModel;

        public SummaryWindow(SummaryModel summary)
        {
            InitializeComponent();
            var dialogs = App.ServiceProvider.GetRequiredService<IDialogService>();
            _viewModel = new SummaryViewModel(summary, dialogs);
            DataContext = _viewModel;
            SummaryRichTextBox.Document = _viewModel.SummaryDocument;
            _viewModel.HighlightRequested += Vm_HighlightRequested;
            _viewModel.PropertyChanged += ViewModel_PropertyChanged;

            // Subscribe to the Closed event to stop audio when window is closed
            Closed += SummaryWindow_Closed;
        }

        private void SummaryWindow_Closed(object? sender, EventArgs e)
        {
            // Stop audio playback when the window is closed
            if (DataContext is SummaryViewModel viewModel)
            {
                viewModel.StopCommand.Execute(null);
                // StopCommand already resets state and raises highlight event
            }
        }

        private void Vm_HighlightRequested(int index)
        {
            Dispatcher.Invoke(() => HighlightRun(index));
        }

        private void HighlightRun(int index)
        {
            // Check if we have runs available
            if (_viewModel.Runs == null || _viewModel.Runs.Count == 0)
            {
                System.Diagnostics.Debug.WriteLine("No runs available for highlighting");
                return;
            }

            System.Diagnostics.Debug.WriteLine($"Highlighting run {index} of {_viewModel.Runs.Count}");

            // Reset all runs to default background
            foreach (var run in _viewModel.Runs)
            {
                run.Background = Brushes.Transparent;
            }

            // Highlight the specified run
            if (index >= 0 && index < _viewModel.Runs.Count)
            {
                _viewModel.Runs[index].Background = Brushes.Yellow;
                System.Diagnostics.Debug.WriteLine($"Successfully highlighted run {index}");
            }
            else
            {
                System.Diagnostics.Debug.WriteLine($"Index {index} is out of range for {_viewModel.Runs.Count} runs");
            }
        }

        private void ViewModel_PropertyChanged(object? sender, System.ComponentModel.PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(_viewModel.SummaryDocument))
            {
                Dispatcher.Invoke(() =>
                {
                    SummaryRichTextBox.Document = _viewModel.SummaryDocument;
                });
            }
        }
    }
}
