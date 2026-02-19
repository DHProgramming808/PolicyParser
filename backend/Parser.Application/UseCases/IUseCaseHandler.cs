using Parser.Application.Models;

namespace Parser.Application.UseCases;

public interface IUseCaseHandler
{
    string UseCaseId { get; }

    Task<UseCaseResult> ExecuteAsync(IInput input, CancellationToken ct);
}