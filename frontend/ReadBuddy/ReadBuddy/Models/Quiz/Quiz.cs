// ReadBuddy\Models\Quiz\Quiz.cs
using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;

namespace ReadBuddy.Models.Quiz
{
    public class Quiz
    {
        public string Id { get; private set; }

        public string Title { get; private set; }

        public string UserId { get; private set; }

        public string Category { get; private set; }

        public DateTime CreatedAt { get; private set; }

        public List<string> QuestionIds { get; private set; }

        public List<Question?> Questions { get; private set; }

        public Quiz(
            string userId,
            string title,
            string category,
            string id,
            DateTime createdAt,
            List<string> questionIds,
            List<Question?> questions
            )
        {
            UserId = userId;
            Title = title;
            Category = category;
            Id = id;
            CreatedAt = createdAt;
            QuestionIds = questionIds;
            Questions = questions ?? Enumerable.Repeat<Question?>(null, questionIds.Count).ToList();
        }

        public Quiz(QuizSummary quizSummery)
        {
            UserId = quizSummery.UserId;
            Title = quizSummery.Title;
            Category = quizSummery.Category;
            Id = quizSummery.Id;
            CreatedAt = quizSummery.CreatedAt;
            QuestionIds = quizSummery.QuestionIds;
            Questions = Enumerable.Repeat<Question?>(null, quizSummery.QuestionIds.Count).ToList();
        }

        public void AddQuestion(Question question, int i)
        {
            if (question == null)
                throw new ArgumentNullException(nameof(question));
            if (i < 0 || i >= Questions.Count)
                throw new ArgumentOutOfRangeException(nameof(i), "Index is out of range of the Questions list.");
            Questions[i] = question;
        }
    }
}