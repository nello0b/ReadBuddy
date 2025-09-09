// ReadBuddy\Services\BackendService.cs
using System;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Reflection.Metadata;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// This class handles communication with the backend server.
    /// It sends the Auth0 access token to the backend for validation or storage,
    /// and uploads files for OCR + TTS processing.
    /// </summary>
    public class BackendService
    {
        private readonly HttpClient _httpClient;
        private readonly string _backendUrl;
        private readonly IUserSessionService _userSessionService;

        /// <summary>
        /// Constructor initializes the service and loads the backend URL from config.
        /// </summary>
        public BackendService(HttpClient httpClient, IUserSessionService userSessionService)
        {
            _httpClient = httpClient;
            _userSessionService = userSessionService ?? throw new ArgumentNullException(nameof(userSessionService));
            _backendUrl = ConfigurationManager.AppSettings["Backend:BaseUrl"]
                          ?? throw new InvalidOperationException("Backend:BaseUrl is not set in App.config");
        }

        /// <summary>
        /// Helper method to extract current user's ID from session.
        /// </summary>
        private string? GetCurrentUserId()
        {
            return _userSessionService.CurrentUser?
                .Claims.FirstOrDefault(c => c.Type == "sub" || c.Type == "user_id")?.Value;
        }

        /// <summary>
        /// Sends the Auth0 access token to the backend via POST request.
        /// </summary>
        public async Task<bool> SendTokenAsync(string accessToken)
        {
            try
            {
                var request = new HttpRequestMessage(HttpMethod.Post, $"{_backendUrl}/api/auth/token");
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

                var response = await _httpClient.SendAsync(request);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to send token to backend: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Uploads an image file to the backend server and receives extracted text and audio response.
        /// </summary>
        public async Task<string?> UploadImageAsync(string filePath)
        {
            try
            {
                using var form = new MultipartFormDataContent();
                var fileBytes = await File.ReadAllBytesAsync(filePath);
                var fileContent = new ByteArrayContent(fileBytes);
                fileContent.Headers.ContentType = new MediaTypeHeaderValue("image/png");
                form.Add(fileContent, "file", Path.GetFileName(filePath));

                var userId = GetCurrentUserId();

                if (string.IsNullOrEmpty(userId))
                {
                    Console.WriteLine("User ID is missing.");
                    return null;
                }

                var url = $"{_backendUrl}/api/process-image/{userId}";

                var response = await _httpClient.PostAsync(url, form);

                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to upload image: {ex.Message}");
                return null;
            }
        }


        /// <summary>
        /// Downloads a file (any type) from the backend using either a relative or absolute URL.
        /// Optionally deletes the file from the backend after download.
        /// </summary>
        /// <param name="relativeOrFullUrl">The URL to download, relative or full.</param>
        /// <param name="toDelete">Indicates whether the file should be deleted after download.</param>
        /// <returns>Byte array of the downloaded file, or null on error.</returns>
        public async Task<byte[]?> DownloadFileAsync(string relativeOrFullUrl, bool toDelete = false)
        {
            try
            {
                // Ensure full URL
                string fullUrl = relativeOrFullUrl.StartsWith("http", StringComparison.OrdinalIgnoreCase)
                    ? relativeOrFullUrl
                    : $"{_backendUrl.TrimEnd('/')}/{relativeOrFullUrl.TrimStart('/')}";

                // Download the file
                byte[] fileBytes = await _httpClient.GetByteArrayAsync(fullUrl);

                // Optionally delete the file after download
                if (toDelete)
                {
                    try
                    {
                        string deleteUrl = fullUrl.Split('?')[0]; // Strip query parameters
                        HttpResponseMessage deleteResponse = await _httpClient.DeleteAsync(deleteUrl);

                        if (!deleteResponse.IsSuccessStatusCode)
                        {
                            Console.WriteLine($"Warning: Failed to delete file at {deleteUrl}. Status: {deleteResponse.StatusCode}");
                        }
                    }
                    catch (Exception deleteEx)
                    {
                        Console.WriteLine($"Warning: Error while deleting file at {fullUrl}: {deleteEx.Message}");
                    }
                }

                return fileBytes;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: Failed to download file from {relativeOrFullUrl}: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// History - Gets all extraction summaries for the current user.
        /// </summary>
        public async Task<string?> GetExtractionHistoryAsync()
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            var url = $"{_backendUrl}/history/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to retrieve extraction history: {ex.Message}");
                return null;
            }
        }


        /// <summary>
        /// Gets the most recent extraction summaries for a user.
        /// </summary>
        public async Task<string?> GetRecentExtractionHistoryAsync(int n)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            if (n <= 0)
            {
                Console.WriteLine("Invalid value for 'n'. Must be a positive integer.");
                return null;
            }

            var url = $"{_backendUrl}/history/recent/{userId}?n={n}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to retrieve recent extraction history: {ex.Message}");
                return null;
            }
        }


        /// <summary>
        /// Gets a specific image extraction result by extraction ID and user ID.
        /// </summary>
        public async Task<string?> GetImageExtractionResultByIdAsync(string extractionId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            var url = $"{_backendUrl}/api/image-extraction-result/{extractionId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get extraction result by ID: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets multiple image extraction results by user ID and a list of extraction IDs.
        /// </summary>
        public async Task<string?> GetImageExtractionResultsByIdsAsync(List<string> extractionIds)
        {
            var userId = GetCurrentUserId();

            if (string.IsNullOrEmpty(userId) || extractionIds == null || extractionIds.Count == 0)
            {
                Console.WriteLine("Invalid userId or empty extraction ID list.");
                return null;
            }

            var payload = new { extraction_ids = extractionIds };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/image-extraction-results/{userId}";
            try
            {
                var response = await _httpClient.PostAsync(url, content);

                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get extraction results by IDs: {ex.Message}");
                return null;
            }
        }



        /// <summary>
        /// Gets image extraction results by category and user ID.
        /// </summary>
        public async Task<string?> GetImageExtractionResultsByCategoryAsync(string category)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            var url = $"{_backendUrl}/api/image-extraction-results/category/{category}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get extraction results by category: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Helper method to handle HTTP responses.
        /// </summary>
        private async Task<string?> HandleResponseAsync(HttpResponseMessage response)
        {
            if (!response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Request failed: {response.StatusCode}");
                return null;
            }

            return await response.Content.ReadAsStringAsync();
        }

        /// <summary>
        /// Updates the category of image extraction results for the current user.
        /// </summary>
        /// <param name="extractionId">The ID of the extraction to update</param>
        /// <param name="newCategory">The new category name</param>
        /// <returns>Response body or null if failed</returns>
        public async Task<string> UpdateImageExtractionResultsCategoryAsync(string extractionId, string newCategory)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            var url = $"{_backendUrl}/api/image-extraction-result/update-category/{extractionId}/{userId}";

            var payload = new { new_category = newCategory };
            var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

            try
            {
                var response = await _httpClient.PutAsync(url, content);

                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to update category: {ex.Message}");
                return null;
            }
        }


        /// <summary>
        /// Gets the user categories for the current user.
        /// </summary>
        /// <returns></returns>
        public async Task<string> GetUserCategoriesAsync()
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
            {
                Console.WriteLine("User ID could not be determined.");
                return null;
            }

            var url = $"{_backendUrl}/api/categories/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get user categories: {ex.Message}");
                return null;
            }
        }


        /// <summary>
        /// Creates a new quiz by category for the current user.
        /// </summary>
        /// <param name="category">The category to create the quiz for</param>
        /// <param name="withEvaluation">Whether to evaluate questions before returning.</param>
        /// <returns>A JSON string containing the created quiz ID or null if failed</returns>
        public async Task<string?> CreateQuizByCategoryAsync(string category, int numberOfQuestions, string lang = "auto", bool withEvaluation = true)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/quiz/create/{category}/{userId}/{numberOfQuestions}/{lang}?with_evaluation={withEvaluation.ToString().ToLower()}";
            try
            {
                var response = await _httpClient.PostAsync(url, null);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create quiz from extractions: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Creates a quiz from a list of extraction IDs for the current user.
        /// </summary>
        /// <param name="extractionIds">List of extraction IDs to create the quiz from</param>
        /// <param name="withEvaluation">Whether to evaluate questions before returning.</param>
        /// <returns>A JSON string containing the created quiz ID or null if failed</returns>
        public async Task<string?> CreateQuizFromExtractionsAsync(List<string> extractionIds, int numberOfQuestions, string lang = "auto", bool withEvaluation = true)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || extractionIds == null || extractionIds.Count == 0)
                return null;

            var payload = new { extraction_ids = extractionIds };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/quiz/create-from-extractions/{userId}/{numberOfQuestions}/{lang}?with_evaluation={withEvaluation.ToString().ToLower()}";
            try
            {
                var response = await _httpClient.PostAsync(url, content);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create quiz from extractions: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets a quiz by its ID for the current user.
        /// </summary>
        /// <param name="quizId">The ID of the quiz to retrieve</param>
        /// <returns>A JSON string containing the quiz or null if failed</returns>
        public async Task<string?> GetQuizByIdAsync(string quizId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/quiz/{quizId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get quiz by ID: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets all quizzes for the current user.
        /// </summary>
        /// <returns>A JSON string containing all quizzes or null if failed</returns>
        public async Task<string?> GetAllQuizzesAsync()
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/quizzes/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get all quizzes: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets quizzes by category for the current user.
        /// </summary>
        /// <param name="category">The category to filter quizzes by</param>
        /// <returns>A JSON string containing quizzes for the specified category or null if failed</returns>
        public async Task<string?> GetQuizByCategoryAsync(string category)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/quizzes/by-category/{category}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get quizzes by category: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets a question by its ID for the current user.
        /// </summary>
        /// <param name="questionId">The ID of the question to retrieve</param>
        /// <returns>A JSON string containing the question or null if failed</returns>
        public async Task<string?> GetQuestionByIdAsync(string questionId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/question/{questionId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get question by ID: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets multiple questions by their IDs for the current user.
        /// </summary>
        /// <param name="questionIds">List of question IDs to retrieve</param>
        /// <returns>A JSON string containing the questions or null if failed</returns>
        public async Task<string?> GetQuestionsByIdsAsync(List<string> questionIds)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || questionIds == null || questionIds.Count == 0)
                return null;

            var payload = new { question_ids = questionIds };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/questions/batch/{userId}";
            try
            {
                var response = await _httpClient.PostAsync(url, content);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get questions by IDs: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Deletes an image extraction result for the current user.
        /// </summary>
        /// <param name="extractionId">ID of the extraction result to delete</param>
        /// <returns>True if deletion succeeded, false otherwise</returns>
        public async Task<bool> DeleteImageExtractionResultAsync(string extractionId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return false;

            var url = $"{_backendUrl}/api/image-extraction-result/{extractionId}/{userId}";

            try
            {
                var response = await _httpClient.DeleteAsync(url);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to delete image extraction result: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Deletes a quiz for the current user.
        /// </summary>
        /// <param name="quizId">ID of the quiz to delete</param>
        /// <returns>True if deletion succeeded, false otherwise</returns>
        public async Task<bool> DeleteQuizAsync(string quizId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return false;

            var url = $"{_backendUrl}/api/quiz/{quizId}/{userId}";

            try
            {
                var response = await _httpClient.DeleteAsync(url);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to delete quiz: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Deletes a glossary for the current user.
        /// </summary>
        /// <param name="glossaryId">ID of the glossary to delete</param>
        /// <returns>True if deletion succeeded, false otherwise</returns>
        public async Task<bool> DeleteGlossaryAsync(string glossaryId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return false;

            var url = $"{_backendUrl}/api/glossary/{glossaryId}/{userId}";

            try
            {
                var response = await _httpClient.DeleteAsync(url);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to delete glossary: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Creates a glossary for the specified category.
        /// </summary>
        public async Task<string?> CreateGlossaryByCategoryAsync(string category, string lang = "auto")
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/glossary/create/{category}/{userId}/{lang}";            
            try
            {
                var response = await _httpClient.PostAsync(url, null);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create glossary by category: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Creates a glossary from specific extraction IDs.
        /// </summary>
        public async Task<string?> CreateGlossaryFromExtractionsAsync(List<string> extractionIds, string lang = "auto")
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || extractionIds == null || extractionIds.Count == 0)
                return null;

            var payload = new { extraction_ids = extractionIds };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/glossary/create-from-extractions/{userId}/{lang}";
            try
            {
                var response = await _httpClient.PostAsync(url, content);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create glossary from extractions: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Retrieves a glossary by ID for the current user.
        /// </summary>
        public async Task<string?> GetGlossaryByIdAsync(string glossaryId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(glossaryId))
                return null;

            var url = $"{_backendUrl}/api/glossary/by-id/{glossaryId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get glossary by ID: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Retrieves all glossaries for the current user.
        /// </summary>
        public async Task<string?> GetAllGlossariesAsync()
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/glossary/all/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get all glossaries: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Gets the status of a background task.
        /// </summary>
        /// <param name="taskId">The ID of the task to check</param>
        /// <returns>A JSON string with the task status or null if failed</returns>
        public async Task<string?> GetTaskStatusAsync(string taskId)
        {
            var url = $"{_backendUrl}/task-status/{taskId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get task status: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Requests the backend to stop a running task.
        /// </summary>
        /// <param name="taskId">The ID of the task to stop</param>
        /// <param name="terminate">If true, forcefully terminate the task</param>
        /// <returns>Response body or null if failed</returns>
        public async Task<string?> StopTaskAsync(string taskId, bool terminate = false)
        {
            var url = $"{_backendUrl}/task-stop/{taskId}?terminate={terminate.ToString().ToLower()}";
            try
            {
                var response = await _httpClient.PostAsync(url, null);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to stop task: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Creates a summary from a single source extraction.
        /// </summary>
        public async Task<string?> CreateSummaryFromSourceAsync(string sourceId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(sourceId))
                return null;

            var url = $"{_backendUrl}/api/summary/from-source/{sourceId}/{userId}";

            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create summary from source: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Creates a summary from multiple source extractions.
        /// </summary>
        public async Task<string?> CreateSummaryFromSourcesAsync(List<string> sourceIds)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || sourceIds == null || sourceIds.Count == 0)
                return null;

            var payload = new { source_ids = sourceIds };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/summary/from-sources/{userId}";
            try
            {
                var response = await _httpClient.PostAsync(url, content);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create summary from sources: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Creates a summary from raw text.
        /// </summary>
        public async Task<string?> CreateSummaryFromTextAsync(string text)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(text))
                return null;

            var payload = new { text = text };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var url = $"{_backendUrl}/api/summary/from-text/{userId}";

            try
            {
                var response = await _httpClient.PostAsync(url, content);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to create summary from text: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Retrieves all summaries for the current user.
        /// </summary>
        public async Task<string?> GetSummariesAsync()
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId))
                return null;

            var url = $"{_backendUrl}/api/summaries/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get summaries: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Retrieves summaries referencing a specific source extraction.
        /// </summary>
        public async Task<string?> GetSummariesBySourceAsync(string sourceId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(sourceId))
                return null;

            var url = $"{_backendUrl}/api/summaries/by-source/{sourceId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get summaries by source: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Deletes a summary for the current user.
        /// </summary>
        public async Task<bool> DeleteSummaryAsync(string summaryId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(summaryId))
                return false;

            var url = $"{_backendUrl}/api/summaries/{summaryId}/{userId}";

            try
            {
                var response = await _httpClient.DeleteAsync(url);
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to delete summary: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Retrieves a specific summary by its ID for the current user.
        /// </summary>
        /// <param name="summaryId">The ID of the summary to retrieve</param>
        /// <returns>A JSON string containing the summary or null if failed</returns>
        public async Task<string?> GetSummaryByIdAsync(string summaryId)
        {
            var userId = GetCurrentUserId();
            if (string.IsNullOrEmpty(userId) || string.IsNullOrEmpty(summaryId))
            {
                Console.WriteLine("Invalid user ID or summary ID.");
                return null;
            }

            var url = $"{_backendUrl}/api/summary/{summaryId}/{userId}";
            try
            {
                var response = await _httpClient.GetAsync(url);
                return await HandleResponseAsync(response);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Failed to get summary by ID: {ex.Message}");
                return null;
            }
        }
    }
}
