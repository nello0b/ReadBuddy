namespace ReadBuddy.Services
{
    /// <summary>
    /// Provides methods for showing user dialogs.
    /// </summary>
    public interface IDialogService
    {
        void ShowError(string message, string? title = null);
        void ShowInfo(string message, string? title = null);
        bool ShowConfirmation(string message, string? title = null);
    }
}
