using Parser.Application.Registry;
using Parser.Application.Factories;
using Parser.Application.UseCases;
using Parser.Python;
using Parser.Python.Runners;


var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();


// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

builder.Services.AddSingleton<IPythonRunner, ProcessPythonRunner>(); // TODO stub

builder.Services.AddScoped<FindCodesUseCase>();
builder.Services.AddScoped<FindCodesBatchJsonUseCase>();
builder.Services.AddScoped<FindCodesCsvUseCase>();

builder.Services.AddScoped<IUseCaseFactory, UseCaseFactory>();

// TODO choose between Registry Factory and switchcase Factory
// builder.Services.AddSingleton<IUseCaseRegistry, UseCaseRegistry>();


var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}


app.UseSwagger();
app.UseSwaggerUI();

app.MapControllers();
app.MapGet("/health", () => Results.Ok(new { ok = true }));

app.Run();
