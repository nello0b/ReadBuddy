// ReadBuddy\Models\Quiz\Answer.cs
using ReadBuddy.Models.TTS;
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Quiz
{
    public class Answer
    {
        [JsonPropertyName("id")]
        public string Id { get; private set; }

        [JsonPropertyName("user_id")]
        public string UserId { get; private set; }

        [JsonPropertyName("content")]
        public string Content { get; set; }

        [JsonPropertyName("audio_zip_urls")]
        public List<string> AudioZipUrls { get; private set; }

        public TTSResult? ttsResult { get; set; } = null;

        public Answer(string userId, string content, List<string> audioZipUrls, string id)
        {
            UserId = userId;
            Id = id;
            Content = content;
            AudioZipUrls = audioZipUrls;
        }
    }
}