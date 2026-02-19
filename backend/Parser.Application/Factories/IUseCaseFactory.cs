using Parser.Application.UseCases;

namespace Parser.Application.Factories;

public interface IUseCaseFactory
{
    IUseCaseHandler Create(string useCaseId);
}
