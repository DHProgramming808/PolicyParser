namespace Parser.Application.UseCases;

public sealed record UseCaseEnvelope(
    string UseCaseId,
    object? Input,
    Dictionary<string, object>? Options
);