using Parser.Application.UseCases;

namespace Parser.Application.Registry;

public sealed class UseCaseRegistry : IUseCaseRegistry
{
    private readonly Dictionary<string, IUseCaseHandler> _map;

    public UseCaseRegistry(IEnumerable<IUseCaseHandler> handlers)
    {
        _map = handlers.ToDictionary(h => h.UseCaseId, StringComparer.OrdinalIgnoreCase);
    }

    public IUseCaseHandler Resolve(string useCaseId)
    {
        if (!string.IsNullOrWhiteSpace(useCaseId) && _map.TryGetValue(useCaseId, out var handler))
            return handler;

        if (_map.TryGetValue("default_text", out var fallback))
            return fallback;

        throw new KeyNotFoundException($"Unknown use_case_id '{useCaseId}' and no default_text handler registered.");
    }
}