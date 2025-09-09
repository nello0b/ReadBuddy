// ReadBuddy\Models\Glossary\GlossaryEntry.cs
using System.Collections.Generic;
using System.Text.Json.Serialization;
using ReadBuddy.Models.TTS;

namespace ReadBuddy.Models.Glossary
{
    public class GlossaryEntry
    {
        [JsonPropertyName("id")]
        public string Id { get; private set; }

        [JsonPropertyName("user_id")]
        public string UserId { get; private set; }

        [JsonPropertyName("term")]
        public string Term { get; set; }

        [JsonPropertyName("definition")]
        public string Definition { get; set; }

        [JsonPropertyName("term_audio_zip_urls")]
        public List<string> TermAudioZipUrls { get; private set; }

        [JsonPropertyName("definition_audio_zip_urls")]
        public List<string> DefinitionAudioZipUrls { get; private set; }

        public TTSResult? TermTTS { get; set; } = null;
        public TTSResult? DefinitionTTS { get; set; } = null;

        public GlossaryEntry(string userId, string term, string definition,
                             List<string> termAudioZipUrls, List<string> definitionAudioZipUrls, string id)
        {
            UserId = userId;
            Term = term;
            Definition = definition;
            TermAudioZipUrls = termAudioZipUrls ?? new List<string>();
            DefinitionAudioZipUrls = definitionAudioZipUrls ?? new List<string>();
            Id = id;
        }
    }
}
