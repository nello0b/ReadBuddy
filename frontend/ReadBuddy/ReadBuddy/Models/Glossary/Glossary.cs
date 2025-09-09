// ReadBuddy\Models\Glossary\Glossary.cs
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Glossary
{
    public class Glossary
    {
        [JsonPropertyName("id")]
        public string Id { get; private set; }

        [JsonPropertyName("category")]
        public string Category { get; private set; }

        [JsonPropertyName("user_id")]
        public string UserId { get; private set; }

        [JsonPropertyName("last_updated")]
        public DateTime LastUpdated { get; private set; }

        [JsonPropertyName("entries")]
        public List<GlossaryEntry> Entries { get; private set; }

        public Glossary(string category, string userId, string id, DateTime lastUpdated, List<GlossaryEntry> entries)
        {
            Category = category;
            UserId = userId;
            Id = id;
            LastUpdated = lastUpdated;
            Entries = entries ?? new List<GlossaryEntry>();
        }
    }
}
