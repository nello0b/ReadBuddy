using System.Text.Json;
using System.Threading.Tasks;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Service for retrieving the status of background tasks from the backend.
    /// </summary>
    public class TaskTrackerService
    {
        private readonly BackendService _backendService;

        public TaskTrackerService(BackendService backendService)
        {
            _backendService = backendService;
        }

        public async Task<BackendTaskStatus?> GetTaskStatusAsync(string taskId)
        {
            var json = await _backendService.GetTaskStatusAsync(taskId);
            if (string.IsNullOrEmpty(json))
                return null;

            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            try
            {
                return JsonSerializer.Deserialize<BackendTaskStatus>(json, options);
            }
            catch (JsonException)
            {
                return null;
            }
        }
    }
}
