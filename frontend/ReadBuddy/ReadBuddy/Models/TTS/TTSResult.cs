using Microsoft.Extensions.DependencyInjection;
using ReadBuddy.Models.Extraction;
using ReadBuddy.Services;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

namespace ReadBuddy.Models.TTS
{
    public class TTSResult
    {
        public List<string> AudioZipUrls { get; private set; } = new();
        public List<AudioChunk> AudioChunks { get; private set; } = new();

        private readonly BackendService? _backendService;

        // Private constructor: use CreateAsync() instead
        private TTSResult(List<string> audioZipUrls, BackendService backendService)
        {
            AudioZipUrls = audioZipUrls;
            _backendService = backendService;
        }

        // Constructor that accepts pre-processed audio chunks
        public TTSResult(List<string> audioZipUrls, List<AudioChunk> audioChunks)
        {
            AudioZipUrls = audioZipUrls;
            AudioChunks = audioChunks;
        }


        /// <summary>
        /// Asynchronously creates and initializes a TTSResult instance.
        /// </summary>
        public static async Task<TTSResult> CreateAsync(List<string> audioZipUrls, BackendService backendService)
        {
            var audioChunks = await DownloadAndProcessZipsStatic(audioZipUrls, backendService);
            return new TTSResult(audioZipUrls, audioChunks);
        }

        // Static method that can be called from OCR home level
        public static async Task<List<AudioChunk>> DownloadAndProcessZipsStatic(List<string> audioZipUrls, BackendService backendService)
        {
            var audioChunks = new List<AudioChunk>();
            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };

            foreach (var url in audioZipUrls)
            {
                try
                {
                    var fileName = Path.GetFileNameWithoutExtension(url);

                    // Use a more persistent directory structure
                    string appDataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ReadBuddy", "Audio");
                    string audioDir = Path.Combine(appDataDir, fileName);

                    // Check if already extracted
                    if (Directory.Exists(audioDir))
                    {
                        var existingChunk = await LoadExistingAudioChunk(audioDir, options);
                        if (existingChunk != null)
                        {
                            audioChunks.Add(existingChunk);
                            continue;
                        }
                    }

                    Directory.CreateDirectory(audioDir);

                    // Use temp directory for download only
                    string tempDir = Path.GetTempPath();
                    string tempZipPath = Path.Combine(tempDir, $"{Guid.NewGuid()}.zip");

                    // Download ZIP
                    var bytes = await backendService.DownloadFileAsync(url, true);
                    if (bytes != null)
                    {
                        await File.WriteAllBytesAsync(tempZipPath, bytes);

                        // Extract ZIP to persistent location
                        ZipFile.ExtractToDirectory(tempZipPath, audioDir, true);

                        // Load and process the audio chunk
                        var audioChunk = await LoadExistingAudioChunk(audioDir, options);
                        if (audioChunk != null)
                        {
                            audioChunks.Add(audioChunk);
                        }

                        // Clean up temp zip
                        File.Delete(tempZipPath);
                    }
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"❌ Error processing zip from {url}: {ex.Message}");
                }
            }

            return audioChunks;
        }

        private static async Task<AudioChunk?> LoadExistingAudioChunk(string extractPath, JsonSerializerOptions options)
        {
            try
            {
                // Load summary.json
                var summaryPath = Path.Combine(extractPath, "summary.json");
                if (!File.Exists(summaryPath))
                {
                    Console.WriteLine($"⚠️ Missing summary.json in: {extractPath}");
                    return null;
                }

                var summaryJson = JsonSerializer.Deserialize<Summary>(
                    await File.ReadAllTextAsync(summaryPath), options);

                var result = summaryJson?.Results?.FirstOrDefault();
                if (result == null)
                {
                    Console.WriteLine($"⚠️ No result found in summary.json at: {extractPath}");
                    return null;
                }

                // Build dynamic paths from summary metadata
                var wordPath = Path.Combine(extractPath, result.WordBoundaryFileName);
                var sentencePath = Path.Combine(extractPath, result.SentenceBoundaryFileName);
                var mp3Path = Path.Combine(extractPath, result.AudioFileName);

                if (!File.Exists(wordPath) || !File.Exists(sentencePath) || !File.Exists(mp3Path))
                {
                    Console.WriteLine($"⚠️ Missing one or more audio files in: {extractPath}");
                    return null;
                }

                // Deserialize word and sentence data
                var wordData = JsonSerializer.Deserialize<List<WordData>>(
                    await File.ReadAllTextAsync(wordPath), options);

                var sentenceData = JsonSerializer.Deserialize<List<SentenceData>>(
                    await File.ReadAllTextAsync(sentencePath), options);

                return new AudioChunk
                {
                    FolderPath = extractPath,
                    Words = wordData ?? new List<WordData>(),
                    Sentences = sentenceData ?? new List<SentenceData>(),
                    Summary = summaryJson,
                    Mp3Path = mp3Path
                };
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"❌ Error loading audio chunk from {extractPath}: {ex.Message}");
                return null;
            }
        }

        public bool HasAudio => AudioChunks.Count > 0;

        /// <summary>
        /// Clears all cached audio files from the persistent storage directory
        /// </summary>
        public static void ClearAllCachedAudio()
        {
            try
            {
                string appDataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ReadBuddy", "Audio");
                if (Directory.Exists(appDataDir))
                {
                    Directory.Delete(appDataDir, true);
                    System.Diagnostics.Debug.WriteLine("✅ All cached audio files cleared");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"❌ Error clearing cached audio: {ex.Message}");
            }
        }

        /// <summary>
        /// Clears cached audio files for specific URLs
        /// </summary>
        public static void ClearCachedAudio(List<string> audioZipUrls)
        {
            try
            {
                string appDataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ReadBuddy", "Audio");
                
                foreach (var url in audioZipUrls)
                {
                    var fileName = Path.GetFileNameWithoutExtension(url);
                    string audioDir = Path.Combine(appDataDir, fileName);
                    
                    if (Directory.Exists(audioDir))
                    {
                        Directory.Delete(audioDir, true);
                        System.Diagnostics.Debug.WriteLine($"✅ Cleared cached audio for: {fileName}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"❌ Error clearing specific cached audio: {ex.Message}");
            }
        }

        /// <summary>
        /// Clears cached audio files for this TTSResult instance
        /// </summary>
        public void ClearInstanceCache()
        {
            ClearCachedAudio(AudioZipUrls);
            AudioChunks.Clear();
        }

        /// <summary>
        /// Gets the total size of cached audio files in bytes
        /// </summary>
        public static long GetCachedAudioSize()
        {
            try
            {
                string appDataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ReadBuddy", "Audio");
                if (!Directory.Exists(appDataDir))
                    return 0;

                var dirInfo = new DirectoryInfo(appDataDir);
                return dirInfo.EnumerateFiles("*", SearchOption.AllDirectories).Sum(fi => fi.Length);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"❌ Error calculating cached audio size: {ex.Message}");
                return 0;
            }
        }
    }
}
