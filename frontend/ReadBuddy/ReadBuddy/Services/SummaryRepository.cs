// ReadBuddy\Services\SummaryRepository.cs
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using ReadBuddy.Models.Summary;
using ReadBuddy.Models.Tasks;

namespace ReadBuddy.Services
{
    /// <summary>
    /// Repository for creating and retrieving summaries via the backend service.
    /// Caches results to minimize backend calls.
    /// </summary>
    public class SummaryRepository
    {
        private readonly BackendService _backend;

        public List<Summary> CachedSummaries { get; private set; } = new();

        public SummaryRepository(BackendService backend)
        {
            _backend = backend;
        }

        /// <summary>
        /// Creates a summary from a single extraction source.
        /// Returns a <see cref="BackendTask"/> representing the background task.
        /// </summary>
        public async Task<BackendTask?> CreateFromSourceAsync(string sourceId)
        {
            var json = await _backend.CreateSummaryFromSourceAsync(sourceId);
            return DeserializeTask(json);
        }

        /// <summary>
        /// Creates a summary from multiple extraction sources.
        /// Returns a <see cref="BackendTask"/> representing the background task.
        /// </summary>
        public async Task<BackendTask?> CreateFromSourcesAsync(List<string> sourceIds)
        {
            var json = await _backend.CreateSummaryFromSourcesAsync(sourceIds);
            return DeserializeTask(json);
        }

        /// <summary>
        /// Creates a summary from raw text input.
        /// Returns a <see cref="BackendTask"/> representing the background task.
        /// </summary>
        public async Task<BackendTask?> CreateFromTextAsync(string text)
        {
            var json = await _backend.CreateSummaryFromTextAsync(text);
            return DeserializeTask(json);
        }

        /// <summary>
        /// Retrieves all summaries for the current user.
        /// Cached results are returned unless <paramref name="forceRefresh"/> is true.
        /// </summary>
        public async Task<List<Summary>> GetAllSummariesAsync(bool forceRefresh = false)
        {
            if (!forceRefresh && CachedSummaries.Any())
                return CachedSummaries;

            var json = await _backend.GetSummariesAsync();
            var summaries = ParseSummaryList(json);
            CachedSummaries = summaries;
            return summaries;
        }

        /// <summary>
        /// Retrieves summaries that reference a specific extraction source.
        /// </summary>
        public async Task<List<Summary>> GetSummariesBySourceAsync(string sourceId)
        {
            var json = await _backend.GetSummariesBySourceAsync(sourceId);
            return ParseSummaryList(json);
        }

        /// <summary>
        /// Deletes a summary for the current user and removes it from the cache.
        /// </summary>
        public async Task<bool> DeleteSummaryAsync(string summaryId)
        {
            bool success = await _backend.DeleteSummaryAsync(summaryId);
            if (success)
                CachedSummaries.RemoveAll(s => s.Id == summaryId);
            return success;
        }

        /// <summary>
        /// Retrieves a specific summary by its ID and caches it locally.
        /// </summary>
        /// <param name="summaryId">The ID of the summary to retrieve.</param>
        /// <returns>The retrieved <see cref="Summary"/> object, or null if not found.</returns>
        public async Task<Summary?> GetSummaryByIdAsync(string summaryId)
        {
            // Check if the summary is already cached
            var cachedSummary = CachedSummaries.FirstOrDefault(s => s.Id == summaryId);
            if (cachedSummary != null)
                return cachedSummary;

            // Fetch the summary from the backend
            var json = await _backend.GetSummaryByIdAsync(summaryId);
            if (string.IsNullOrEmpty(json))
                return null;

            // Deserialize the summary
            var summary = JsonSerializer.Deserialize<Summary>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            // Cache the summary if successfully retrieved
            if (summary != null)
                CachedSummaries.Add(summary);

            return summary;
        }

        private static BackendTask? DeserializeTask(string? json)
        {
            if (string.IsNullOrEmpty(json))
                return null;

            return JsonSerializer.Deserialize<BackendTask>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
        }

        private static List<Summary> ParseSummaryList(string? json)
        {
            if (string.IsNullOrEmpty(json))
                return new List<Summary>();

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("summaries", out var summariesEl) ||
                summariesEl.ValueKind != JsonValueKind.Array)
                return new List<Summary>();

            var list = summariesEl.Deserialize<List<Summary>>(new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            return list ?? new List<Summary>();
        }
    }
}
