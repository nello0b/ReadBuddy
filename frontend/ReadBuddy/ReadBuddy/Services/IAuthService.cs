using System.Security.Claims;
using System.Threading.Tasks;

namespace ReadBuddy.Services
{
    public interface IAuthService
    {
        Task<(bool IsSuccess, ClaimsPrincipal? User, string? AccessToken, string? ErrorMessage)> LoginAsync();
        Task LogoutAsync();
    }
}
