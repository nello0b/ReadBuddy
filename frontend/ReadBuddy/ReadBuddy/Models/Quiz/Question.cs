// ReadBuddy\Models\Quiz\Question.cs
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.TTS;
using ReadBuddy.Services;
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace ReadBuddy.Models.Quiz
{
    public class Question
    {
        [JsonPropertyName("id")]
        public string Id { get; private set; }

        [JsonPropertyName("user_id")]
        public string UserId { get; private set; }

        [JsonPropertyName("content")]
        public string Content { get; private set; }

        [JsonPropertyName("answers")]
        public List<Answer> Answers { get; private set; }

        [JsonPropertyName("correct_answer_id")]
        public string CorrectAnswerId { get; private set; }

        [JsonPropertyName("audio_zip_urls")]
        public List<string> AudioZipUrls { get; private set; }

        public TTSResult? ttsResult { get; set; } = null;

        public bool withAudio => this.ttsResult != null && this.ttsResult.AudioZipUrls.Count > 0;

        public Question(
            string userId,
            string content,
            List<Answer> answers,
            string correctAnswerId,
            List<string> audioZipUrls,
            string id)
        {
            UserId = userId;
            Id = id;
            Content = content;
            Answers = answers;
            CorrectAnswerId = correctAnswerId;
            AudioZipUrls = audioZipUrls;
        }
    }
}