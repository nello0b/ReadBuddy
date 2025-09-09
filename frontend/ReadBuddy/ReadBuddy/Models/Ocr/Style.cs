namespace ReadBuddy.Models.OCR;

public class Style
{
    public string Name { get; set; }
    public double Confidence { get; set; }
    public List<Span> Spans { get; set; }
}
