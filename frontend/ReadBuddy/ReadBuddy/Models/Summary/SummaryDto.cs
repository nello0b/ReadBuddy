namespace ReadBuddy.Models.Summary;

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

/// <summary>
/// DTO used when deserializing summary objects returned by the backend.
/// </summary>
public class SummaryDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("source_ids")]
    public List<string> Source_Ids { get; set; }

    [JsonPropertyName("content")]
    public List<string> Content { get; set; }

    [JsonPropertyName("audio_zip_urls")]
    public List<string> Audio_Zip_Urls { get; set; }

    [JsonPropertyName("created_at")]
    public DateTime Created_At { get; set; }
}
