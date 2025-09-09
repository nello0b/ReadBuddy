// ReadBuddy\Services\DocumentProcessor.cs
using ReadBuddy.Models.Extraction;
using ReadBuddy.Models.Tasks;
using ReadBuddy.Services;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using ReadBuddy.Models.TTS;
using System.Diagnostics;

namespace ReadBuddy.Services
{
    public class DocumentProcessor
    {
        private readonly BackendService _backendService;

        public DocumentProcessor(BackendService backendService)
        {
            _backendService = backendService;
        }

        public async Task<BackendTask?> ProcessImageAsync(string filePath)
        {
            string json = await _backendService.UploadImageAsync(filePath);
            if (json == null) return null;

            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            var task = JsonSerializer.Deserialize<BackendTask>(json, options);

            return task;
        }

    }

}