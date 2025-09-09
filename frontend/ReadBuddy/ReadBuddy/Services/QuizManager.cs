// ReadBuddy\Services\QuizManager.cs
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.Quiz;
using ReadBuddy.Models.Tasks;
using ReadBuddy.Models.TTS;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;


namespace ReadBuddy.Services
{
    public class QuizManager
    {
        private readonly BackendService _backend;

        public QuizManager(BackendService backendService)
        {
            _backend = backendService;
        }


        /// <summary>
        /// Creates a new quiz for the specified category by communicating with the backend service.
        /// </summary>
        /// <param name="category">The category for which to create the quiz.</param>
        /// <param name="withEvaluation">Whether to evaluate questions before returning.</param>
        /// <returns>
        /// A <see cref="QuizSummary"/> object representing the created quiz, or null if creation failed.
        /// </returns>
        public async Task<BackendTask?> CreateQuizByCategoryAsync(string category, int numberOfQuestions, string lang = "auto", bool withEvaluation = true)
        {
            var json = await _backend.CreateQuizByCategoryAsync(category, numberOfQuestions, lang, withEvaluation);
            if (string.IsNullOrEmpty(json))
                return null;

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

            return JsonSerializer.Deserialize<BackendTask>(json, options);
        }

        /// <summary>
        /// Creates a new quiz from a list of extraction IDs by communicating with the backend service.
        /// </summary>
        /// <param name="extractionIds">List of extraction IDs to create the quiz from.</param>
        /// <param name="withEvaluation">Whether to evaluate questions before returning.</param>
        /// <returns>
        /// A <see cref="QuizSummary"/> object representing the created quiz, or null if creation failed.
        /// </returns>
        public async Task<BackendTask?> CreateQuizFromExtractionsAsync(List<string> extractionIds, int numberOfQuestions, string lang = "auto", bool withEvaluation = true)
        {
            var json = await _backend.CreateQuizFromExtractionsAsync(extractionIds, numberOfQuestions, lang, withEvaluation);
            if (string.IsNullOrEmpty(json))
                return null;

            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };

            return JsonSerializer.Deserialize<BackendTask>(json, options);
        }

        /// <summary>
        /// Retrieves a quiz summary by its unique identifier by communicating with the backend service.
        /// </summary>
        /// <param name="quizId">The unique identifier of the quiz to retrieve.</param>
        /// <returns>
        /// A <see cref="QuizSummary"/> object representing the quiz, or null if retrieval failed.
        /// </returns>
        public async Task<QuizSummary?> GetQuizByIdAsync(string quizId)
        {
            var json = await _backend.GetQuizByIdAsync(quizId);
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("quiz", out var quizElement))
                return null;

            var quizSummery = quizElement.Deserialize<QuizSummary>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            return quizSummery;
        }

        /// <summary>
        /// Convenience method to retrieve a quiz summary by ID. This wraps <see cref="GetQuizByIdAsync"/>.
        /// </summary>
        /// <param name="quizId">Quiz identifier.</param>
        public Task<QuizSummary?> GetQuizSummaryByIdAsync(string quizId)
        {
            return GetQuizByIdAsync(quizId);
        }

        /// <summary>
        /// Retrieves all quizzes for the current user by communicating with the backend service.
        /// </summary>
        /// <returns>
        /// A list of <see cref="QuizSummary"/> objects representing all quizzes for the user, or null if retrieval failed.
        /// </returns>
        public async Task<List<QuizSummary>?> GetAllQuizzesAsync()
        {
            var json = await _backend.GetAllQuizzesAsync();
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("quizzes", out var quizzesElement) || quizzesElement.ValueKind != JsonValueKind.Array)
                return null;

            var quizzes = quizzesElement.Deserialize<List<QuizSummary>>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            return quizzes;
        }

        /// <summary>
        /// Retrieves all quizzes for the specified category by communicating with the backend service.
        /// </summary>
        /// <param name="category">The category to filter quizzes by.</param>
        /// <returns>
        /// A list of <see cref="QuizSummary"/> objects representing quizzes for the specified category, or null if retrieval failed.
        /// </returns>
        public async Task<List<QuizSummary>?> GetQuizByCategoryAsync(string category)
        {
            var json = await _backend.GetQuizByCategoryAsync(category);
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("quizzes", out var quizzesElement) || quizzesElement.ValueKind != JsonValueKind.Array)
                return null;

            var quizzes = quizzesElement.Deserialize<List<QuizSummary>>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            return quizzes;
        }

        /// <summary>
        /// Retrieves a question by its unique identifier by communicating with the backend service.
        /// </summary>
        /// <param name="questionId">The unique identifier of the question to retrieve.</param>
        /// <returns>
        /// A <see cref="Question"/> object representing the question, or null if retrieval failed.
        /// </returns>
        private async Task<Question?> GetQuestionByIdAsync(string questionId, bool withAudio = false)
        {
            var json = await _backend.GetQuestionByIdAsync(questionId);
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("question", out var questionElement))
                return null;

            var question = questionElement.Deserialize<Question>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (withAudio && !await PrepareTTSResultQuestion(question))
            {
                // If preparation fails, return null
                return null;
            }

            return question;
        }

        /// <summary>
        /// Retrieves a list of questions by their unique identifiers by communicating with the backend service.
        /// </summary>
        /// <param name="questionIds">List of question IDs to retrieve.</param>
        /// <returns>
        /// A list of <see cref="Question"/> objects representing the questions, or null if retrieval failed.
        /// </returns>
        private async Task<List<Question>?> GetQuestionsByIdsAsync(List<string> questionIds, bool withAudio = false)
        {
            var json = await _backend.GetQuestionsByIdsAsync(questionIds);
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("questions", out var questionsElement) || questionsElement.ValueKind != JsonValueKind.Array)
                return null;

            var questions = questionsElement.Deserialize<List<Question>>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (questions == null || questions.Count == 0)
            {
                // If no questions were retrieved, return an empty list
                return new List<Question>();
            }

            foreach (var question in questions)
            {
                // Prepare each question by ensuring it has valid audio zip URLs
                if (withAudio && !await PrepareTTSResultQuestion(question))
                {
                    // If preparation fails, remove the question from the list
                    questions.Remove(question);
                }
            }

            return questions;
        }

        /// <summary>
        /// Prepares a Question object by initializing its TTSResult and the TTSResult for each of its answers.
        /// Ensures that audio files are available for both the question and its answers.
        /// </summary>
        /// <param name="question">The question to prepare.</param>
        /// <returns>True if preparation succeeds and audio is available; otherwise, false.</returns>
        private async Task<bool> PrepareTTSResultQuestion(Question? question)
        {
            if (question == null || question.AudioZipUrls == null || question.AudioZipUrls.Count == 0)
            {
                // If the question is null or has no audio zip URLs, return false
                return false;
            }

            // Create a TTSResult instance for the question
            question.ttsResult = await TTSResult.CreateAsync(question.AudioZipUrls, _backend);
            if (question.ttsResult == null || question.ttsResult.AudioChunks == null || question.ttsResult.AudioChunks.Count == 0)
            {
                // If TTSResult creation failed or has no audio files, return false
                return false;
            }

            // Create the TTSResult for the Answers
            foreach (var answer in question.Answers)
            {
                if (answer.AudioZipUrls != null && answer.AudioZipUrls.Count > 0)
                {
                    answer.ttsResult = await TTSResult.CreateAsync(answer.AudioZipUrls, _backend);
                    if (answer.ttsResult == null || answer.ttsResult.AudioChunks == null || answer.ttsResult.AudioChunks.Count == 0)
                    {
                        // If TTSResult creation failed or has no audio files, return false
                        return false;
                    }
                }
            }

            return true;
        }

        /// <summary>
        /// Creates a Quiz object from a QuizSummery object.
        /// Loads and preloads the specified number of questions (with TTS) from the backend.
        /// </summary>
        /// <param name="quizSummery">The quiz summary to convert.</param>
        /// <param name="questionsToPreload">Number of questions to preload (with TTS).</param>
        /// <returns>A Quiz object with preloaded questions, or null if quizSummery is null.</returns>
        public async Task<Quiz?> LoadQuizAsync(QuizSummary quizSummery, int questionsToPreload = 1, bool withAudio = false)
        {
            if (quizSummery == null)
                return null;

            var quiz = new Quiz(quizSummery);

            if (quizSummery.QuestionIds == null || quizSummery.QuestionIds.Count == 0)
                return quiz;

            if (questionsToPreload <= 0)
            {
                // If no questions to preload, return the quiz with no questions
                return quiz;
            }

            // Limit the number of questions to preload
            List<string> preloadIds = quizSummery.QuestionIds.Take(questionsToPreload).ToList();

            List<Question>? questions = await GetQuestionsByIdsAsync(preloadIds, withAudio);

            if (questions == null || questions.Count == 0)
            {
                // If no questions were loaded, return the quiz with no questions
                return quiz;
            }

            for (int i = 0; i < questions.Count; i++)
            {
                if (questions[i] != null)
                {
                    quiz.AddQuestion(questions[i], i);
                }
            }

            return quiz;
        }

        /// <summary>
        /// Loads the next set of questions for the given quiz, preloading TTS audio as needed.
        /// </summary>
        /// <param name="quiz">The quiz to load questions into.</param>
        /// <param name="questionsToLoad">The number of questions to load.</param>
        /// <returns>
        /// True if questions were loaded; false if there are no more questions or loading failed.
        /// </returns>
        public async Task<bool> LoadQuestion(Quiz quiz, int i, bool withAudio)
        {
            if (i < 0 && i < quiz.Questions.Count)
            {
                // If the index is out of range, return false
                return false;
            }

            // Load the question from the backend
            string idToLoad = quiz.QuestionIds[i];

            Question? question = await GetQuestionByIdAsync(idToLoad, withAudio);

            if (question == null)
            {
                // If no questions were loaded, return false
                return false;
            }

            quiz.AddQuestion(question, i);

            return true;
        }

        /// <summary>
        /// Deletes a quiz for the current user via the backend service.
        /// </summary>
        /// <param name="quizId">The ID of the quiz to delete.</param>
        /// <returns>True if the deletion succeeded; otherwise, false.</returns>
        public async Task<bool> DeleteQuizAsync(string quizId)
        {
            if (string.IsNullOrWhiteSpace(quizId))
                return false;

            bool success = await _backend.DeleteQuizAsync(quizId);

            return success;
        }
    }
}
