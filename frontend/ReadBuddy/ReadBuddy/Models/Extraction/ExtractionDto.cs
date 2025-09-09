using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Text.Json.Serialization;
using ReadBuddy.Models.OCR;

namespace ReadBuddy.Models.Extraction
{
    public class ExtractionDto
    {
        public AnalyzeResult Text_Data { get; set; }
        public List<string> Audio_Zip_Urls { get; set; }
        public string Category { get; set; }
        public string Id { get; set; }

        public string File_Path { get; set; }

        [JsonPropertyName("created_at")]
        public DateTime Created_At { get; set; }
    }
}
