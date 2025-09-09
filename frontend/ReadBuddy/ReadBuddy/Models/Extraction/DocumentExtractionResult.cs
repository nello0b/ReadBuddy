using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace ReadBuddy.Models.Extraction
{
    public class DocumentExtractionResult : ExtractionResult
    {
        public DocumentExtractionResult(AnalyzeResult textData, TTSResult audioData, string Category, string Id, DateTime createdAt)
            : base(textData, audioData, Category, Id, createdAt) { }
    }
}
