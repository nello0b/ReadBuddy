namespace ReadBuddy.Models.OCR;

public class Word
{
    public string Content { get; set; }
    public List<int> Polygon { get; set; }
    public double Confidence { get; set; }
    public Span Span { get; set; }
}
