using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;

namespace ReadBuddy.Models.Quiz
{
    public class QuizSummary
    {
        [JsonPropertyName("id")]
        public string Id { get; private set; }

        [JsonPropertyName("title")]
        public string Title { get; private set; }

        [JsonPropertyName("user_id")]
        public string UserId { get; private set; }

        [JsonPropertyName("category")]
        public string Category { get; private set; }

        [JsonPropertyName("question_ids")]
        public List<string> QuestionIds { get; private set; }

        [JsonPropertyName("created_at")]
        public DateTime CreatedAt { get; private set; }

        [JsonIgnore]
        public int QuestionCount => QuestionIds?.Count ?? 0;

        public QuizSummary(
            string userId,
            string title,
            string category,
            List<string> questionIds,
            string id,
            DateTime createdAt)
        {
            UserId = userId;
            Title = title;
            Category = category;
            Id = id;
            CreatedAt = createdAt;
            QuestionIds = questionIds;
        }
    }
}