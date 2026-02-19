using System.Text.Json;

namespace Parser.Application.UseCases;

public sealed record UseCaseResult(
    string UseCaseId,
    JsonElement Payload,
    Dictionary<string, object>? Metadata = null
);