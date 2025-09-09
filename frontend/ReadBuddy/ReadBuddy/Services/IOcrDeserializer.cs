using ReadBuddy.Models.OCR;

namespace ReadBuddy.Services.Interfaces
{
    public interface IOcrDeserializer
    {
        AnalyzeResult Deserialize(string json);
    }
}
