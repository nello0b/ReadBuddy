using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.IO;

namespace ReadBuddy.Models.TTS
{
    public class AudioChunk
    {
        public string FolderPath { get; set; }
        public string Mp3Path { get; set; }
        public List<WordData> Words { get; set; }
        public List<SentenceData> Sentences { get; set; }
        public Summary Summary { get; set; } // Or define a class if structured
    }
}
