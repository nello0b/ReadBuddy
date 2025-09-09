// ReadBuddy\Models\Extraction\ExtractionResultSummary.cs
using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Extraction
{
    public class ExtractionResultSummary
    {
        [JsonPropertyName("extraction_id")]
        public string ExtractionId { get; set; }

        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; set; }

        [JsonPropertyName("category")]
        public string? Category { get; set; }

        private string? _title;

        [JsonPropertyName("title")]
        public string? Title
        {
            get => _title;
            set => _title = value != null && value.Length > 20 ? value.Substring(0, 20) : value;
        }

        public ExtractionResultSummary() { }

        public ExtractionResultSummary(string extractionId, DateTime createdAt, string? category = null, string? title = null)
        {
            ExtractionId = extractionId;
            CreatedAt = createdAt;
            Category = category;
            Title = title;
        }

        public object ToDictionary()
        {
            return new
            {
                extraction_id = ExtractionId,
                created_at = CreatedAt,
                category = Category,
                title = Title
            };
        }
    }
}
