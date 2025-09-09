namespace ReadBuddy.Models.OCR;

public class Page
{
    public int PageNumber { get; set; }
    public double Angle { get; set; }
    public int Width { get; set; }
    public int Height { get; set; }
    public string Unit { get; set; }
    public List<Word> Words { get; set; }
    public List<Line> Lines { get; set; }
    public List<Span> Spans { get; set; }
}
