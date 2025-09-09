using System.Security.Claims;

// This service stores the current user's session data in memory,
// including their identity and Auth0 access token.


public class UserSessionService : IUserSessionService
{
    public ClaimsPrincipal? CurrentUser { get; private set; }

    public string? AccessToken { get; private set; }

    // Stores the user's identity and optionally the access token
    public void SetUser(ClaimsPrincipal user, string? accessToken = null)
    {
        CurrentUser = user;
        AccessToken = accessToken;
    }
    public void Clear()
    {
        CurrentUser = null;
        AccessToken = null;
    }

}
