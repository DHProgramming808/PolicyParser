namespace Parser.Application.Models;


public class FindCodesInput : IInput{
    public string? useCaseId {get; set; } = null;
    public string? Text { get; set; } = null;
    public string? Id { get; set; } = null;
    public string? Name { get; set; } = null;
    public List<TextBatchItem>? Items { get; set; } = null;
    public Dictionary<string, object>? Options { get; set; } = null;
}