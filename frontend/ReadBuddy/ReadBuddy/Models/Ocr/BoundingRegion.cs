namespace ReadBuddy.Models.OCR;

public class BoundingRegion
{
    public int PageNumber { get; set; }
    public List<int> Polygon { get; set; }
}
