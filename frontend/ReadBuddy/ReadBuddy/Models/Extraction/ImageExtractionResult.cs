using ReadBuddy.Models.OCR;
using ReadBuddy.Models.TTS;
using ReadBuddy.Services;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace ReadBuddy.Models.Extraction
{
    public class ImageExtractionResult : ExtractionResult
    {
        public string ImagePath { get; set; }
        public DateTime CreatedAt { get; set; }

        protected ImageExtractionResult(AnalyzeResult textData, TTSResult audioData, string category, string id, DateTime createdAt, string imagePath)
            : base(textData, audioData, category, id, createdAt)
        {
            ImagePath = imagePath;
        }

        public static async Task<ImageExtractionResult> CreateAsync(
            AnalyzeResult textData,
            List<string> audioZipUrls,
            string category,
            string id,
            string imagePath,
            DateTime createdAt,
            BackendService backendService)
        {
            string finalImagePath = await PrepareImageAsync(imagePath, backendService);
            TTSResult ttsResult = await TTSResult.CreateAsync(audioZipUrls, backendService);

            return new ImageExtractionResult(textData, ttsResult, category, id, createdAt, finalImagePath);
        }

        private static async Task<string> PrepareImageAsync(string originalPath, BackendService backendService)
        {
            string fileName = Path.GetFileName(originalPath);

            bool toDelete = false;

            // Download the image if it doesn't exist locally
            if (!File.Exists(originalPath))
            {
                byte[] imageBytes = await backendService.DownloadFileAsync(originalPath, true);
                if (imageBytes == null || imageBytes.Length == 0)
                    throw new IOException($"Could not download image from: {originalPath}");

                originalPath = Path.Combine(Path.GetTempPath(), fileName);
                await File.WriteAllBytesAsync(originalPath, imageBytes);

                toDelete = true;
            }

            // Save image to static/image directory
            string destinationDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "static", "image");
            Directory.CreateDirectory(destinationDir);

            string destinationPath = Path.Combine(destinationDir, fileName);

            if (!Path.GetFullPath(originalPath).Equals(Path.GetFullPath(destinationPath), StringComparison.OrdinalIgnoreCase))
            {
                File.Copy(originalPath, destinationPath, overwrite: true);
            }

            // delete the original file if it was downloaded
            if (toDelete && File.Exists(originalPath))
            {
                try
                {
                    File.Delete(originalPath);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"⚠️ Could not delete temporary image file: {ex.Message}");
                }
            }

            return destinationPath;
        }
    }
}
