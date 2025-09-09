using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using ReadBuddy.Services;

namespace ReadBuddy.Models.Extraction
{
    public abstract class ExtractionResult
    {
        public AnalyzeResult TextData { get; set; }
        public TTSResult AudioData { get; set; }
        public string Category { get; set; }
        public string Id { get; set; }
        public DateTime CreatedAt { get; set; }

        protected ExtractionResult(AnalyzeResult textData, TTSResult audioData, string Category, string Id, DateTime createdAt)
        {
            TextData = textData;
            AudioData = audioData;
            this.Category = Category;
            this.Id = Id;
            this.CreatedAt = createdAt;
        }
    }
}
