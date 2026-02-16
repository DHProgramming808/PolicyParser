using Parser.Application.UseCases;

namespace Parser.Application.Registry;

public interface IUseCaseRegistry
{
    IUseCaseHandler Resolve(string useCaseId);
}