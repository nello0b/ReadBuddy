namespace ReadBuddy.Models.OCR;

public class AzureOcrResponse
{
    public string Status { get; set; }
    public DateTime CreatedDateTime { get; set; }
    public DateTime LastUpdatedDateTime { get; set; }
    public AnalyzeResult AnalyzeResult { get; set; }
}
