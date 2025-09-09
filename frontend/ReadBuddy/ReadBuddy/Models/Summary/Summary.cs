namespace ReadBuddy.Models.Summary;

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

/// <summary>
/// Represents a text summary created from one or more extractions.
/// </summary>
public class Summary
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("source_ids")]
    public List<string> SourceIds { get; set; }

    [JsonPropertyName("content")]
    public List<string> Content { get; set; }

    [JsonPropertyName("audio_zip_urls")]
    public List<string> AudioZipUrls { get; set; }

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }

    public Summary(string id, List<string> sourceIds, List<string> content, List<string> audioZipUrls, DateTime createdAt)
    {
        Id = id;
        SourceIds = sourceIds ?? new();
        Content = content ?? new();
        AudioZipUrls = audioZipUrls ?? new();
        CreatedAt = createdAt;
    }

    public Summary() : this(string.Empty, new List<string>(), new List<string>(), new List<string>(), DateTime.MinValue)
    {
    }
}
