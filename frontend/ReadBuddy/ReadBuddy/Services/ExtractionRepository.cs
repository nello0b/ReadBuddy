// ReadBuddy\Services\ExtractionRepository.cs
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using ReadBuddy.Models.Extraction;

namespace ReadBuddy.Services
{
    public class ExtractionRepository
    {
        private readonly BackendService _backend;

        public List<ExtractionResultSummary> CachedHistory { get; private set; } = new();

        public List<ImageExtractionResult> CachedImageExtractionResults { get; private set; } = new();

        public ExtractionRepository(BackendService backend)
        {
            _backend = backend;
        }

        /// <summary>  
        /// Retrieves the history of extractions in a Summery format.
        /// <paramref name="toPullAgain"/> is used to determine if the history should be pulled 
        ///                                again from the backend or use cached data.
        ///                                ignored if the chached history is empty.
        /// </summary>  
        public async Task<List<ExtractionResultSummary>> GetHistoryAsync(bool toPullAgain = false)
        {
            if (!toPullAgain && this.CachedHistory.Any())
            {
                // Return cached history if available and not pulling again
                return this.CachedHistory;
            }

            var json = await _backend.GetExtractionHistoryAsync();
            if (string.IsNullOrEmpty(json)) return new();

            var dict = JsonSerializer.Deserialize<Dictionary<string, ExtractionResultSummary>>(json,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            // Set the cached history
            this.CachedHistory = dict?.Values.ToList() ?? new List<ExtractionResultSummary>();

            return this.CachedHistory;
        }

        /// <summary>  
        /// Retrieves the top N recent (by the CreatedAt value) extractions in Summary format.
        /// <paramref name="toPullAgain"/> is used to determine if the top N history should be pulled
        ///                                from the backend or use cached data.
        ///                                it ignored if the cached history has less than N items.
        /// </summary>  
        public async Task<List<ExtractionResultSummary>> GetTopNHistoryAsync(int n, bool toPullAgain = false)
        {
            if (!toPullAgain && this.CachedHistory.Count >= n)
            {
                // Return top N most recent history (by CreatedAt) without changing the cache order
                return this.CachedHistory
                    .OrderByDescending(x => x.CreatedAt)
                    .Take(n)
                    .ToList();
            }

            var json = await _backend.GetRecentExtractionHistoryAsync(n);
            if (string.IsNullOrEmpty(json))
                return new List<ExtractionResultSummary>();

            var dict = JsonSerializer.Deserialize<Dictionary<string, ExtractionResultSummary>>(json,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            // add only the new items to the cached history
            if (dict != null)
            {
                var existingIds = new HashSet<string>(this.CachedHistory.Select(x => x.ExtractionId));
                var newItems = dict.Values.Where(x => !existingIds.Contains(x.ExtractionId)).ToList();
                if (newItems.Any())
                {
                    this.CachedHistory.AddRange(newItems);
                }
            }

            return dict?.Values.ToList() ?? new();
        }

        /// <summary>
        /// Retrieves a single extraction result summary by its ID.
        /// This method fetches the latest history list and returns the matching summary if available.
        /// </summary>
        /// <param name="extractionId">The extraction identifier.</param>
        /// <returns>The <see cref="ExtractionResultSummary"/> if found; otherwise null.</returns>
        public async Task<ExtractionResultSummary?> GetExtractionSummaryByIdAsync(string extractionId)
        {
            if (string.IsNullOrWhiteSpace(extractionId))
                return null;

            var history = await GetHistoryAsync(true);
            return history.FirstOrDefault(h => h.ExtractionId == extractionId);
        }

        public async Task<ImageExtractionResult> GetImageExtractionResultAsync(string extractionId)
        {
            // Check if the result is already cached
            var cachedResult = this.CachedImageExtractionResults.FirstOrDefault(x => x.Id == extractionId);
            if (cachedResult != null)
            {
                return cachedResult;
            }
            // If not cached, fetch from backend
            var json = await _backend.GetImageExtractionResultByIdAsync(extractionId);
            if (string.IsNullOrEmpty(json)) return null;
            var dto = JsonSerializer.Deserialize<ExtractionDto>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            if (dto == null) return null;
            // Create the ImageExtractionResult and cache it
            var result = await ImageExtractionResult.CreateAsync(dto.Text_Data,
                                                                 dto.Audio_Zip_Urls,
                                                                 dto.Category,
                                                                 dto.Id,
                                                                 dto.File_Path,
                                                                 dto.Created_At,
                                                                 _backend);
            this.CachedImageExtractionResults.Add(result);
            return result;
        }

        public async Task<List<ImageExtractionResult>> GetImageExtractionResultsAsync(List<string> extractionIds)
        {
            if (extractionIds == null || extractionIds.Count == 0)
                return new List<ImageExtractionResult>();

            // Get cached results
            var cached = this.CachedImageExtractionResults
                .Where(x => extractionIds.Contains(x.Id))
                .ToList();

            // Find which IDs are not cached
            var missingIds = extractionIds
                .Except(cached.Select(x => x.Id))
                .ToList();

            var results = new List<ImageExtractionResult>(cached);

            if (missingIds.Any())
            {
                // Fetch missing results from backend
                var json = await _backend.GetImageExtractionResultsByIdsAsync(missingIds);
                if (!string.IsNullOrEmpty(json))
                {
                    var dtos = JsonSerializer.Deserialize<List<ExtractionDto>>(json, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });

                    if (dtos != null)
                    {
                        foreach (var dto in dtos)
                        {
                            var result = await ImageExtractionResult.CreateAsync(
                                dto.Text_Data,
                                dto.Audio_Zip_Urls,
                                dto.Category,
                                dto.Id,
                                dto.File_Path,
                                dto.Created_At,
                                _backend);

                            this.CachedImageExtractionResults.Add(result);
                            results.Add(result);
                        }
                    }
                }
            }

            // Return results in the same order as extractionIds
            return extractionIds
                .Select(id => results.FirstOrDefault(x => x.Id == id))
                .Where(x => x != null)
                .Select(x => x!) // This casts from ImageExtractionResult? to ImageExtractionResult
                .ToList();

        }


        public async Task<List<ImageExtractionResult>> GetImageExtractionResultsByCategoryAsync(string category)
        {
            if (string.IsNullOrEmpty(category))
                return new List<ImageExtractionResult>();
            // Get cached results for the specified category
            var cachedResults = this.CachedImageExtractionResults
                .Where(x => x.Category.Equals(category, StringComparison.OrdinalIgnoreCase))
                .ToList();
            if (cachedResults.Any())
            {
                return cachedResults;
            }
            // If no cached results, fetch from backend
            var json = await _backend.GetImageExtractionResultsByCategoryAsync(category);
            if (string.IsNullOrEmpty(json)) return new List<ImageExtractionResult>();
            var dtos = JsonSerializer.Deserialize<List<ExtractionDto>>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
            if (dtos == null || !dtos.Any()) return new List<ImageExtractionResult>();
            var results = new List<ImageExtractionResult>();
            foreach (var dto in dtos)
            {
                var result = await ImageExtractionResult.CreateAsync(
                    dto.Text_Data,
                    dto.Audio_Zip_Urls,
                    dto.Category,
                    dto.Id,
                    dto.File_Path,
                    dto.Created_At,
                    _backend);
                this.CachedImageExtractionResults.Add(result);
                results.Add(result);
            }
            return results;
        }

        public async Task<List<string>> GetUserCategoriesAsync()
        {
            var json = await _backend.GetUserCategoriesAsync(); // This calls GET /api/categories/{user_id}
            if (string.IsNullOrEmpty(json))
                return new List<string>();

            try
            {
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                if (root.TryGetProperty("categories", out var categoriesElement) && categoriesElement.ValueKind == JsonValueKind.Array)
                {
                    return categoriesElement.EnumerateArray()
                        .Select(c => c.GetString())
                        .Where(c => !string.IsNullOrEmpty(c))
                        .Select(c => c!) // null-forgiving operator
                        .ToList();
                }
            }
            catch (JsonException ex)
            {
                Console.WriteLine($"Failed to parse categories: {ex.Message}");
            }

            return new List<string>();
        }

        /// <summary>
        /// Updates the category of a specific image extraction result for the current user.
        /// Also updates the cached result if present.
        /// </summary>
        /// <param name="extractionId">The extraction result ID to update.</param>
        /// <param name="newCategory">The new category to set.</param>
        /// <returns>True if the update succeeded, false otherwise.</returns>
        public async Task<bool> UpdateImageExtractionResultCategoryAsync(string extractionId, string newCategory)
        {
            if (string.IsNullOrWhiteSpace(extractionId) || string.IsNullOrWhiteSpace(newCategory))
                return false;

            var response = await _backend.UpdateImageExtractionResultsCategoryAsync(extractionId, newCategory);
            if (string.IsNullOrEmpty(response))
                return false;

            // Update cache for ImageExtractionResult
            var cachedResult = CachedImageExtractionResults.FirstOrDefault(x => x.Id == extractionId);
            if (cachedResult != null)
                cachedResult.Category = newCategory;

            // Update cache for ExtractionResultSummary
            var cachedSummary = CachedHistory.FirstOrDefault(x => x.ExtractionId == extractionId);
            if (cachedSummary != null)
                cachedSummary.Category = newCategory;

            return true;
        }

        /// <summary>
        /// Deletes an image extraction result for the current user and updates cached data.
        /// </summary>
        /// <param name="extractionId">The ID of the extraction result to delete.</param>
        /// <returns>True if the deletion succeeded; otherwise, false.</returns>
        public async Task<bool> DeleteImageExtractionResultAsync(string extractionId)
        {
            if (string.IsNullOrWhiteSpace(extractionId))
                return false;

            bool success = await _backend.DeleteImageExtractionResultAsync(extractionId);

            if (success)
            {
                // Remove from cached history
                CachedHistory.RemoveAll(x => x.ExtractionId == extractionId);

                // Remove from cached image extraction results
                var cached = CachedImageExtractionResults.FirstOrDefault(x => x.Id == extractionId);
                if (cached != null)
                    CachedImageExtractionResults.Remove(cached);
            }

            return success;
        }


    }

}
