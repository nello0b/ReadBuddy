using System.Text.Json;
using ReadBuddy.Models.OCR;
using ReadBuddy.Services.Interfaces;

namespace ReadBuddy.Services
{
    public class OcrDeserializer : IOcrDeserializer
    {
        private readonly JsonSerializerOptions _options;

        public OcrDeserializer()
        {
            _options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };
        }

        public AnalyzeResult Deserialize(string json)
        {
            return JsonSerializer.Deserialize<AnalyzeResult>(json, _options)
                   ?? throw new InvalidOperationException("Failed to deserialize OCR response.");
        }
    }
}
