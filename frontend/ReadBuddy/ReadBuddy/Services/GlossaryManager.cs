// ReadBuddy\Services\GlossaryManager.cs
using ReadBuddy.Models.Glossary;
using ReadBuddy.Models.Tasks;
using ReadBuddy.Models.TTS;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace ReadBuddy.Services
{
    public class GlossaryManager
    {
        private readonly BackendService _backend;

        public GlossaryManager(BackendService backendService)
        {
            _backend = backendService;
        }

        public async Task<BackendTask?> CreateGlossaryByCategoryAsync(string category, string lang = "auto")
        {
            var json = await _backend.CreateGlossaryByCategoryAsync(category, lang);
            if (string.IsNullOrEmpty(json))
                return null;

            return JsonSerializer.Deserialize<BackendTask>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        }

        public async Task<BackendTask?> CreateGlossaryFromExtractionsAsync(List<string> extractionIds, string lang = "auto")
        {
            var json = await _backend.CreateGlossaryFromExtractionsAsync(extractionIds, lang);
            if (string.IsNullOrEmpty(json))
                return null;

            return JsonSerializer.Deserialize<BackendTask>(json, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        }

        public async Task<Glossary?> GetGlossaryByIdAsync(string glossaryId)
        {
            var json = await _backend.GetGlossaryByIdAsync(glossaryId);
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("glossary", out var glossElement))
                return null;

            var glossary = glossElement.Deserialize<Glossary>(new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (glossary == null)
                return null;

            await PrepareTTSAsync(glossary);
            return glossary;
        }

        public async Task<List<Glossary>?> GetAllGlossariesAsync()
        {
            var json = await _backend.GetAllGlossariesAsync();
            if (string.IsNullOrEmpty(json))
                return null;

            using var doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("glossaries", out var glossariesEl) || glossariesEl.ValueKind != JsonValueKind.Array)
                return null;

            var glossaries = glossariesEl.Deserialize<List<Glossary>>(new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            return glossaries;
        }

        public async Task<bool> DeleteGlossaryAsync(string glossaryId)
        {
            if (string.IsNullOrWhiteSpace(glossaryId))
                return false;

            return await _backend.DeleteGlossaryAsync(glossaryId);
        }

        private async Task PrepareTTSAsync(Glossary glossary)
        {
            foreach (var entry in glossary.Entries)
            {
                if (entry.TermAudioZipUrls != null && entry.TermAudioZipUrls.Count > 0)
                {
                    entry.TermTTS = await TTSResult.CreateAsync(entry.TermAudioZipUrls, _backend);
                }
                if (entry.DefinitionAudioZipUrls != null && entry.DefinitionAudioZipUrls.Count > 0)
                {
                    entry.DefinitionTTS = await TTSResult.CreateAsync(entry.DefinitionAudioZipUrls, _backend);
                }
            }
        }
    }
}
