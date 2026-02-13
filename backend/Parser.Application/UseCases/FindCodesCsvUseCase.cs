using System.Text.Json;
using Parser.Python;
using Parser.Application.Models;

namespace Parser.Application.UseCases;

public sealed class FindCodesCsvUseCase : IUseCaseHandler
{
    private readonly IPythonRunner _python;

    public FindCodesCsvUseCase(IPythonRunner python) => _python = python;

    public string UseCaseId => "find-codes-csv";

    public async Task<UseCaseResult> ExecuteAsync(IInput input, CancellationToken ct)
    {
        // TODO stub, will probably deprecate and adjust csv endpoint to use FindCodesBatchJsonUseCase instead
        if (input is not FindCodesInput findCodesInput)
        {
            throw new ArgumentException("Expected FindCodesInput", nameof(input));
        }

        var payloadJson = JsonSerializer.Serialize(new
        {
            
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
