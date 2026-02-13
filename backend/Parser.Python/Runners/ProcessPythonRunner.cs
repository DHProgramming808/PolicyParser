using System.Text.Json;
using System.Text;
using System.Diagnostics;
using System.Runtime.CompilerServices;

namespace Parser.Python.Runners;

public sealed class ProcessPythonRunner : IPythonRunner
{
    // TODO move these to appsettings
    private const string PythonExe = "python";
    private const string PythonModule = "aiparser.entrypoints.find_codes_entrypoint";
    private static readonly TimeSpan DefaultTimeout = TimeSpan.FromMinutes(10);


    public async Task<string> RunAsync(string useCaseId, string payloadJson, CancellationToken ct)
    {
        var (text, options) = ExtractTextAndOptions(payloadJson);

        var minimalPayload = options.HasValue
            ? JsonSerializer.Serialize(new {text, options = options.Value})
            : JsonSerializer.Serialize(new {text});

        var workingDir = FindRepoRootOrThrow();

        var processStartInfo = new ProcessStartInfo
        {
            FileName = PythonExe,
            Arguments = $"-m {PythonModule}",
            WorkingDirectory = workingDir,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };

        using var proc = new Process
        {
            StartInfo = processStartInfo,
            EnableRaisingEvents = true
        };

        try
        {
            if (!proc.Start())
            {
                throw new InvalidOperationException("Failed to start Parser python module");
            }
        }
        catch (Exception e)
        {
            throw new InvalidOperationException($"Failed to start python executable '{PythonExe}'. Ensure Python is installed and on PATH.", e);
        }

        await proc.StandardInput.WriteAsync(minimalPayload.AsMemory(), ct);
        await proc.StandardInput.FlushAsync(ct);
        proc.StandardInput.Close();

        var stdoutTask = proc.StandardOutput.ReadToEndAsync();
        var stderrTask = proc.StandardError.ReadToEndAsync();

        using var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeoutCts.CancelAfter(DefaultTimeout);

        try
        {
            await proc.WaitForExitAsync(timeoutCts.Token);
        }
        catch (OperationCanceledException)
        {
            TryKill(proc);
            if (ct.IsCancellationRequested)
            {
                throw;
            }
            throw new TimeoutException($"Python runner timed out after {DefaultTimeout.TotalSeconds} seconds.");

        }

        var stdout = (await stdoutTask).Trim();
        var stderr = (await stderrTask).Trim();

        if (proc.ExitCode != 0)
        {
            throw new InvalidOperationException(
                $"Python runner failed (exit {proc.ExitCode}). " +
                $"UseCaseId='{useCaseId}'. STDERR: {stderr}"
            );
        }

        if (string.IsNullOrWhiteSpace(stdout))
        {
            throw new InvalidOperationException(
                $"Python runner returned empty stdout. UseCaseId='{useCaseId}'. STDERR: {stderr}"
            );
        }

        try
        {
            JsonDocument.Parse(stdout);
        }
        catch (Exception e)
        {
            throw new InvalidOperationException(
                $"Python runner returned non-JSON stdout. " +
                $"UseCaseId='{useCaseId}'. First 500 chars: {stdout[..Math.Min(500, stdout.Length)]}",
                e
            );
        }

        return stdout;
    }


    private static (string text, JsonElement? options) ExtractTextAndOptions(string payloadJson)
    {
        using var doc = JsonDocument.Parse(payloadJson);
        var root = doc.RootElement;

        string text = "";

        if (root.TryGetProperty("input", out var input))
        {
            // input can be a string: "..."
            if (input.ValueKind == JsonValueKind.String)
            {
                text = input.GetString() ?? "";
            }
            // input can be object with text: { text: "..." }
            else if (input.ValueKind == JsonValueKind.Object && input.TryGetProperty("text", out var textProp))
            {
                if (textProp.ValueKind == JsonValueKind.String)
                    text = textProp.GetString() ?? "";
                else
                    text = textProp.GetRawText();
            }
            else
            {
                // last resort: stringify
                text = input.GetRawText();
            }
        }

        JsonElement? options = null;
        if (root.TryGetProperty("options", out var opt) && opt.ValueKind == JsonValueKind.Object)
        {
            options = opt.Clone(); // clone out of JsonDocument lifetime
        }

        return (text, options);
    }


    private static void TryKill(Process proc)
    {
        try
        {
            if (!proc.HasExited)
                proc.Kill(entireProcessTree: true);
        }
        catch
        {
            // ignore
        }
    }


    private static string FindRepoRootOrThrow()
    {
        var baseDir = AppContext.BaseDirectory;
        var dir = new DirectoryInfo(baseDir);

        for (int i = 0; i < 10 && dir is not null; i++)
        {
            var aiparserDir = Path.Combine(dir.FullName, "aiparser");
            var backendDir = Path.Combine(dir.FullName, "backend");

            if (Directory.Exists(aiparserDir) && Directory.Exists(backendDir))
                return dir.FullName;

            dir = dir.Parent;
        }

        // Fallback: current directory if you're running from repo root manually
        var cwd = Directory.GetCurrentDirectory();
        if (Directory.Exists(Path.Combine(cwd, "aiparser")) && Directory.Exists(Path.Combine(cwd, "backend")))
            return cwd;

        throw new DirectoryNotFoundException(
            "Could not locate repo root. Expected to find 'aiparser' and 'backend' folders. " +
            $"BaseDirectory was: {baseDir}, CurrentDirectory was: {cwd}"
        );
    }
}
