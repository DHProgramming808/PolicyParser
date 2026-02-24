using System;

using Parser.Application.UseCases;
using Parser.Application.Factories;

namespace Parser.Application.Factories;


public sealed class UseCaseFactory : IUseCaseFactory
{
    private readonly  FindCodesBatchJsonUseCase _findCodesBatchJson;
    private readonly FindCodesCsvUseCase _findCodesCsv;
    private readonly FindCodesUseCase _findCodes;

    public UseCaseFactory(
        FindCodesBatchJsonUseCase findCodesBatchJson,
        FindCodesCsvUseCase findCodesCsv,
        FindCodesUseCase findCodes
    )
    {
        _findCodesBatchJson = findCodesBatchJson;
        _findCodesCsv = findCodesCsv;
        _findCodes = findCodes;
    }

    public IUseCaseHandler Create(string useCaseId)
    {
        return useCaseId switch
        {
            "find-codes-batch-json" => _findCodesBatchJson,
            "find-codes-csv" => _findCodesCsv,
            "find-codes" => _findCodes,
            _ => throw new NotSupportedException($"Unknown useCaseId '{useCaseId}'.")
        };
    }
}

