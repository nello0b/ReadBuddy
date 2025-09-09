using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Tasks
{
    public class BackendTaskInfo
    {
        [JsonPropertyName("step")]
        public string Step { get; set; }

        [JsonPropertyName("out_of")]
        public string Out_Of { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; }

        [JsonPropertyName("user_id")]
        public string User_Id { get; set; }

        [JsonPropertyName("attempt")]
        [JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
        public int Attempt { get; set; }
    }

    public class BackendTaskStatus
    {
        [JsonPropertyName("state")]
        public string State { get; set; }

        [JsonPropertyName("info")]
        public BackendTaskInfo? Info { get; set; }

        [JsonPropertyName("result")]
        public string? Result { get; set; }

        [JsonPropertyName("traceback")]
        public string? Traceback { get; set; }
    }
}
