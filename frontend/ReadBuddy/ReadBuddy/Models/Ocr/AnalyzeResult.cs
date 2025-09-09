namespace ReadBuddy.Models.OCR;

public class AnalyzeResult
{
    public string ApiVersion { get; set; }
    public string ModelId { get; set; }
    public string StringIndexType { get; set; }
    public string Content { get; set; }
    public string ContentFormat { get; set; }
    public List<Page> Pages { get; set; }
    public List<Paragraph> Paragraphs { get; set; }
    public List<Style> Styles { get; set; }
}
