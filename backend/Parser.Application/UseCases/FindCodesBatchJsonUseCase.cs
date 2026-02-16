using System.Text.Json;
using Parser.Python;
using Parser.Application.Models;

namespace Parser.Application.UseCases;

public sealed class FindCodesBatchJsonUseCase : IUseCaseHandler
{
    private readonly IPythonRunner _python;

    public FindCodesBatchJsonUseCase(IPythonRunner python) => _python = python;

    public string UseCaseId => "find-codes-batch-json";

    public async Task<UseCaseResult> ExecuteAsync(IInput input, CancellationToken ct)
    {
        if (input is not FindCodesInput findCodesInput)
        {
            throw new ArgumentException("Expected FindCodesInput", nameof(input));
        }
        if (findCodesInput?.Items is null || findCodesInput.Items.Count == 0)
        {
            throw new ArgumentException("Batch mode requires Items with at least one element.", nameof(input));
        }

        var results = new List<JsonElement>();

        foreach (TextBatchItem item in findCodesInput.Items)
        {
            var pythonInput = new
            {
                id = item.Id,
                name = item.Name,
                text = item.Text ?? string.Empty
            };

            var payloadJson = JsonSerializer.Serialize(new
            {
                use_case_id = UseCaseId,
                input = pythonInput,
                options = findCodesInput.Options ?? new Dictionary<string, object>()
            });

            var pythonOut = await _python.RunAsync("find-codes", payloadJson, ct);

            using var doc = JsonDocument.Parse(pythonOut);
            var py = doc.RootElement;

            var wrapped = JsonSerializer.SerializeToElement(new
            {
                id = item.Id,
                name = item.Name,
                result = py
            });

            results.Add(wrapped);
        }

        var arrayPayLoad = JsonSerializer.SerializeToElement(results);

        return new UseCaseResult(
            UseCaseId,
            Payload: arrayPayLoad,
            Metadata: new Dictionary<string, object> { ["handler"] = nameof(FindCodesBatchJsonUseCase) }
        );
    }
}
