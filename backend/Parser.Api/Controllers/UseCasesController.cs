using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Parser.Api.DTOs;
using Parser.Application.Registry;
using Parser.Application.Factories;
using Parser.Application.UseCases;
using Parser.Application.Models;
using Microsoft.Extensions.Options;

namespace Parser.Api.Controllers;

[ApiController]
[Route("api/v1/use-cases")]
public sealed class UseCasesControler : ControllerBase
{
    private readonly IUseCaseFactory _useCaseFactory;

    public UseCasesControler(IUseCaseFactory useCaseFactory)
    {
        _useCaseFactory = useCaseFactory;
    }

    [HttpPost("json/{useCaseId}")]
    public async Task<IActionResult> ExecuteJson(string useCaseId, [FromBody] InputDTO input, CancellationToken ct)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(useCaseId))
            {
                return BadRequest("useCaseId is required.");
            }

            IUseCaseHandler useCase = _useCaseFactory.Create(useCaseId);


            List<TextBatchItem> batchItems = new List<TextBatchItem>();
            if (input.Items != null && input.Items.Any())
            {
                foreach (BatchItemDTO item in input.Items)
                {
                    TextBatchItem batchItem = new TextBatchItem{
                        Id = item.Id,
                        Name = item.Name,
                        Text = item.Text
                    };
                    batchItems.Add(batchItem);
                }
            }
            FindCodesInput findCodesInput = new FindCodesInput(){
                Text = input.Text,
                Id = input.Id,
                Name = input.Name,
                Items = batchItems.Any() ? batchItems : null,
                Options = input.Options != null ? input.Options : null
            };

            UseCaseResult result = await useCase.ExecuteAsync(findCodesInput, ct);

            // TODO add result validation and error handling
            return new JsonResult(result.Payload);
        }
        catch (NotSupportedException e)
        {
            // unknown use case id
            return NotFound(new { error = e.Message });
        }
        catch (ArgumentException e)
        {
            // bad inputs / wrong shapes
            return BadRequest(new { error = e.Message });
        }
        catch (Exception e)
        {
            // unexpected
            return StatusCode(500, new { error = "Unhandled server error.", detail = e.Message });
        }
    }


    // TODO flesh out
    [HttpPost("csv/{useCaseId}")]
    public async Task<IActionResult> ExecuteCsv(string useCaseId, [FromBody] InputDTO input, CancellationToken ct)
    {
        return Ok("stub");
    }
    
}