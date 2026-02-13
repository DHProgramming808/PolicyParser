namespace Parser.Python;

public interface IPythonRunner
{
    /// <summary>
    /// Runs python logic for the given use case. Input and output are JSON strings.
    /// </summary>
    Task<string> RunAsync(string useCaseId, string payloadJson, CancellationToken ct);
}
