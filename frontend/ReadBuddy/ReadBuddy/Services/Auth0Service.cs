using Auth0.OidcClient;
using Duende.IdentityModel.Client;
using Duende.IdentityModel.OidcClient;
using System.Configuration;
using System.Security.Claims;
using System.Threading.Tasks;

namespace ReadBuddy.Services
{
    public class Auth0Service : IAuthService
    {
        private readonly Auth0Client _auth0Client;
        private readonly string _clientId;
        private readonly string _domain;
        private readonly string _audience;
        private readonly string _redirectUri;

        public Auth0Service()
        {
            _domain = ConfigurationManager.AppSettings["Auth0:Domain"]!;
            _clientId = ConfigurationManager.AppSettings["Auth0:ClientId"]!;
            _audience = ConfigurationManager.AppSettings["Auth0:Audience"]!;
            _redirectUri = ConfigurationManager.AppSettings["Auth0:RedirectUri"]!;

            if (string.IsNullOrWhiteSpace(_domain) ||
                string.IsNullOrWhiteSpace(_clientId) ||
                string.IsNullOrWhiteSpace(_audience) ||
                string.IsNullOrWhiteSpace(_redirectUri))
            {
                throw new InvalidOperationException("Missing Auth0 settings in App.config");
            }

            _auth0Client = new Auth0Client(new Auth0ClientOptions
            {
                Domain = _domain,
                ClientId = _clientId,
                Scope = "openid profile email offline_access", // Scope defined here
                Browser = new WebViewBrowser(),
                RedirectUri = _redirectUri,
                PostLogoutRedirectUri = _redirectUri
            });
        }

        public async Task<(bool IsSuccess, ClaimsPrincipal? User, string? AccessToken, string? ErrorMessage)> LoginAsync()
        {
            try
            {
                var loginResult = await _auth0Client.LoginAsync(new
                {
                    audience = _audience
                });

                if (loginResult.IsError)
                    return (false, null, null, loginResult.Error);

                return (true, loginResult.User, loginResult.AccessToken, null);
            }
            catch (Exception ex)
            {
                return (false, null, null, ex.Message);
            }
        }


        public async Task LogoutAsync()
        {
            await _auth0Client.LogoutAsync();
        }
    }
}