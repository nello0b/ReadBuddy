namespace ReadBuddy.Models.OCR;

public class Paragraph
{
    public List<Span> Spans { get; set; }
    public List<BoundingRegion> BoundingRegions { get; set; }
    public string Content { get; set; }
}
