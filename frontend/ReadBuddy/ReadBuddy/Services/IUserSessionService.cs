using System.Security.Claims;

// Interface for managing the current user's session data,
// including identity and optional access token.

public interface IUserSessionService
{
    ClaimsPrincipal? CurrentUser { get; }
    string? AccessToken { get; }

    // Accepts both user identity and optional token
    void SetUser(ClaimsPrincipal user, string? accessToken = null);

    void Clear();

}
