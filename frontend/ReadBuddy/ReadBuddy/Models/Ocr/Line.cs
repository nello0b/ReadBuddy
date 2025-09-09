namespace ReadBuddy.Models.OCR;

public class Line
{
    public string Content { get; set; }
    public List<int> Polygon { get; set; }
    public List<Span> Spans { get; set; }
}
