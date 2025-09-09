using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ReadBuddy.Models.TTS
{
    public class Summary
    {
        public string JobID { get; set; }
        public string Status { get; set; }
        public List<SummaryResult> Results { get; set; }
    }

    public class SummaryResult
    {
        public List<string> Contents { get; set; }
        public string Status { get; set; }
        public string AudioFileName { get; set; }
        public string WordBoundaryFileName { get; set; }
        public string SentenceBoundaryFileName { get; set; }
        public SummaryProperties Properties { get; set; }
    }

    public class SummaryProperties
    {
        public string SizeInBytes { get; set; }
        public string DurationInMilliseconds { get; set; }
    }
}

