using System.Text.Json;
using Parser.Python;
using Parser.Application.Models;

namespace Parser.Application.UseCases;

public sealed class FindCodesUseCase : IUseCaseHandler
{
    private readonly IPythonRunner _python;

    public FindCodesUseCase(IPythonRunner python) => _python = python;

    public string UseCaseId => "find-codes";

    public async Task<UseCaseResult> ExecuteAsync(IInput input, CancellationToken ct)
    {
        if (input is not FindCodesInput findCodesInput)
        {
            throw new ArgumentException("Expected FindCodesInput", nameof(input));
        }

        var pythonInput = new
        {
            id = findCodesInput.Id,
            name = findCodesInput.Name,
            text = findCodesInput.Text ?? string.Empty
        };

        var payloadJson = JsonSerializer.Serialize(new
        {
           use_case_id = UseCaseId,
           input = pythonInput,
           options = findCodesInput.Options ?? new Dictionary<string, object>() 
        });

        var pythonOut = await _python.RunAsync(UseCaseId, payloadJson, ct);

        using var doc = JsonDocument.Parse(pythonOut);
        var py = doc.RootElement;

        var wrapped = JsonSerializer.SerializeToElement(new
        {
            id = findCodesInput.Id,
            name = findCodesInput.Name,
            result = py
        });

        return new UseCaseResult(
            UseCaseId: UseCaseId,
            Payload: wrapped,
            Metadata: new Dictionary<string, object> { ["handler"] = nameof(FindCodesUseCase) }

        );
    }
}