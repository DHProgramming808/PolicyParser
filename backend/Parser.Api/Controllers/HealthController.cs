using Microsoft.AspNetCore.Mvc;

namespace Parser.Api.Controllers;

[ApiController]
[Route("api/v1/health")]
public sealed class HealthController : ControllerBase
{
    [HttpGet]
    public IActionResult Get()
    {
        return Ok(new
        {
            ok = true,
            service = "Parser.Api",
            utc = DateTime.UtcNow.ToString("O")
        });
    }

    // Optional readiness endpoint (useful for deployments)
    [HttpGet("ready")]
    public IActionResult Ready()
    {
        // Later: check python availability, model files, db, etc.
        return Ok(new
        {
            ready = true,
            utc = DateTime.UtcNow.ToString("O")
        });
    }
}