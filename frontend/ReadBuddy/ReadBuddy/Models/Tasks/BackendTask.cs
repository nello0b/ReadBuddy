using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Tasks
{
    public class BackendTask
    {
        [JsonPropertyName("task_id")]
        public string Task_Id { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; }
    }
}
