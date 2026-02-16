namespace Parser.Api.DTOs;


public sealed record InputDTO(
    string? Text = null,
    string? Id = null,
    string? Name = null,
    List<BatchItemDTO>? Items = null,
    Dictionary<string, object>? Options = null,
    InferenceConfig? InferenceConfig = null
);

public sealed record BatchItemDTO(
    string Id,
    string Name,
    string Text 
);

public sealed record InferenceConfig(
    string Mode = "mock", // "mock" or "openai"
    string? ApiKey = null,
    string? Model = null,
    string? BaseUrl = null
);