// ViewModel for the WelcomeView.
// Handles the user login process using Auth0, manages session state,
// sends the access token to the backend, and transitions to the UserInfo screen.

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using ReadBuddy.Services;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using Microsoft.Extensions.DependencyInjection;

namespace ReadBuddy.ViewModels;

public partial class WelcomeViewModel : ObservableObject
{
    private readonly IAuthService _authService;
    private readonly IUserSessionService _userSessionService;
    private readonly BackendService _backendService;
    private readonly IDialogService _dialogService;

    public WelcomeViewModel(IAuthService authService, IUserSessionService userSessionService, BackendService backendService, IDialogService dialogService)
    {
        _authService = authService;
        _userSessionService = userSessionService;
        _backendService = backendService;
        _dialogService = dialogService;
    }

    [ObservableProperty]
    private bool isLoading = true;

    [ObservableProperty]
    private string statusMessage = "Initializing login...";

    [RelayCommand]
    public async Task InitializeAsync()
    {
        IsLoading = true;
        StatusMessage = "Logging in...";

        var (success, user, accessToken, error) = await _authService.LoginAsync();

        if (success && user != null)
        {
            // Store the authenticated user's claims and token
            _userSessionService.SetUser(user, accessToken);

            StatusMessage = "Sending authentication token...";
            // Send the token to the backend
            var sent = await _backendService.SendTokenAsync(accessToken!);
#if DEBUG
            System.Diagnostics.Debug.WriteLine($"SendTokenAsync returned: {sent}");
#endif
            if (!sent)
            {
                var retry = _dialogService.ShowConfirmation("Failed to send token to backend. Try again?", "Backend Error");
                if (retry)
                {
                    await InitializeAsync(); // Retry
                    return;
                }
                else
                {
                    Application.Current.Shutdown(); // Exit app
                    return;
                }
            }

            StatusMessage = "Opening application...";
            OpenMainWindow();
        }
        else
        {
            var result = _dialogService.ShowConfirmation(
                $"Login failed.\n\n{error ?? "Unknown error"}\n\nTry again?",
                "Login Error");

            if (result)
            {
                await InitializeAsync(); // Retry login
            }
            else
            {
                Application.Current.Shutdown(); // Exit application
            }
        }

        IsLoading = false;
    }

    private void OpenMainWindow()
    {
        Application.Current.Dispatcher.Invoke(() =>
        {
            var mainWindow = App.ServiceProvider.GetRequiredService<MainWindow>();
            mainWindow.Show();

            Application.Current.Windows
                .OfType<Window>()
                .FirstOrDefault(w => w.DataContext == this)
                ?.Close();
        });
    }
}
