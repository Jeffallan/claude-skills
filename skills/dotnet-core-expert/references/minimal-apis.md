# Minimal APIs

> Reference for: .NET Core Expert
> Load when: Creating endpoints, routing, middleware, HTTP handlers

## Basic Endpoint Patterns

```csharp
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Configure middleware
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// Simple GET endpoint
app.MapGet("/api/products", async (IProductService service) =>
{
    var products = await service.GetAllAsync();
    return Results.Ok(products);
});

// GET with route parameter
app.MapGet("/api/products/{id:int}", async (int id, IProductService service) =>
{
    var product = await service.GetByIdAsync(id);
    return product is not null
        ? Results.Ok(product)
        : Results.NotFound();
});

// POST with validation
app.MapPost("/api/products", async (
    [FromBody] CreateProductRequest request,
    IProductService service) =>
{
    var product = await service.CreateAsync(request);
    return Results.Created($"/api/products/{product.Id}", product);
})
.WithName("CreateProduct")
.Produces<ProductResponse>(StatusCodes.Status201Created)
.ProducesValidationProblem();

// PUT endpoint
app.MapPut("/api/products/{id:int}", async (
    int id,
    [FromBody] UpdateProductRequest request,
    IProductService service) =>
{
    var success = await service.UpdateAsync(id, request);
    return success ? Results.NoContent() : Results.NotFound();
});

// DELETE endpoint
app.MapDelete("/api/products/{id:int}", async (int id, IProductService service) =>
{
    await service.DeleteAsync(id);
    return Results.NoContent();
});

app.Run();
```

## Route Groups

```csharp
var app = builder.Build();

var api = app.MapGroup("/api")
    .WithOpenApi()
    .RequireAuthorization();

var products = api.MapGroup("/products")
    .WithTags("Products");

products.MapGet("/", GetAllProducts);
products.MapGet("/{id:int}", GetProductById);
products.MapPost("/", CreateProduct);
products.MapPut("/{id:int}", UpdateProduct);
products.MapDelete("/{id:int}", DeleteProduct);

static async Task<IResult> GetAllProducts(IProductService service)
{
    var products = await service.GetAllAsync();
    return Results.Ok(products);
}

static async Task<IResult> GetProductById(int id, IProductService service)
{
    var product = await service.GetByIdAsync(id);
    return product is not null ? Results.Ok(product) : Results.NotFound();
}
```

## Filters and Validation

```csharp
using FluentValidation;

// Request DTO with validation
public record CreateProductRequest(
    string Name,
    string Description,
    decimal Price,
    int CategoryId
);

public class CreateProductValidator : AbstractValidator<CreateProductRequest>
{
    public CreateProductValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(100);

        RuleFor(x => x.Price)
            .GreaterThan(0)
            .LessThan(1000000);

        RuleFor(x => x.CategoryId)
            .GreaterThan(0);
    }
}

// Endpoint filter for validation
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    private readonly IValidator<T> _validator;

    public ValidationFilter(IValidator<T> validator)
    {
        _validator = validator;
    }

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var request = context.Arguments.OfType<T>().FirstOrDefault();
        if (request is null)
        {
            return Results.BadRequest("Invalid request");
        }

        var validationResult = await _validator.ValidateAsync(request);
        if (!validationResult.IsValid)
        {
            return Results.ValidationProblem(
                validationResult.ToDictionary());
        }

        return await next(context);
    }
}

// Register and use
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

app.MapPost("/api/products", CreateProduct)
    .AddEndpointFilter<ValidationFilter<CreateProductRequest>>();
```

## Dependency Injection

```csharp
// Service registration
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IProductRepository, ProductRepository>();

// Multiple parameter binding
app.MapPost("/api/orders", async (
    CreateOrderRequest request,
    IOrderService orderService,
    IEmailService emailService,
    ILogger<Program> logger,
    CancellationToken ct) =>
{
    logger.LogInformation("Creating order for {CustomerId}", request.CustomerId);

    var order = await orderService.CreateAsync(request, ct);
    await emailService.SendOrderConfirmationAsync(order.Id, ct);

    return Results.Created($"/api/orders/{order.Id}", order);
});
```

## Response Patterns

```csharp
// Typed responses
public record ProductResponse(
    int Id,
    string Name,
    string Description,
    decimal Price,
    string CategoryName
);

// Results.Ok with typed response
app.MapGet("/api/products/{id:int}", async (int id, IProductService service) =>
{
    var product = await service.GetByIdAsync(id);
    return product is not null
        ? Results.Ok(product)
        : Results.NotFound(new { Message = "Product not found" });
})
.Produces<ProductResponse>(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound);

// Custom result type
public class PagedResult<T>
{
    public required List<T> Items { get; init; }
    public required int TotalCount { get; init; }
    public required int Page { get; init; }
    public required int PageSize { get; init; }
}

app.MapGet("/api/products", async (
    [AsParameters] PaginationParams pagination,
    IProductService service) =>
{
    var result = await service.GetPagedAsync(
        pagination.Page,
        pagination.PageSize);
    return Results.Ok(result);
})
.Produces<PagedResult<ProductResponse>>();

public record PaginationParams(int Page = 1, int PageSize = 10);
```

## Error Handling

```csharp
// Global exception handler
app.UseExceptionHandler(exceptionHandlerApp =>
{
    exceptionHandlerApp.Run(async context =>
    {
        var exceptionHandlerFeature =
            context.Features.Get<IExceptionHandlerFeature>();
        var exception = exceptionHandlerFeature?.Error;

        var problemDetails = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "An error occurred",
            Detail = exception?.Message
        };

        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await context.Response.WriteAsJsonAsync(problemDetails);
    });
});

// Custom endpoint filter for error handling
public class ErrorHandlingFilter : IEndpointFilter
{
    private readonly ILogger<ErrorHandlingFilter> _logger;

    public ErrorHandlingFilter(ILogger<ErrorHandlingFilter> logger)
    {
        _logger = logger;
    }

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        try
        {
            return await next(context);
        }
        catch (ValidationException ex)
        {
            _logger.LogWarning(ex, "Validation failed");
            return Results.ValidationProblem(ex.Errors.ToDictionary(
                e => e.PropertyName,
                e => new[] { e.ErrorMessage }
            ));
        }
        catch (NotFoundException ex)
        {
            _logger.LogWarning(ex, "Resource not found");
            return Results.NotFound(new { Message = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            return Results.Problem("An unexpected error occurred");
        }
    }
}
```

## Quick Reference

| Pattern | Usage |
|---------|-------|
| `Results.Ok(data)` | 200 with response body |
| `Results.Created(uri, data)` | 201 with location header |
| `Results.NoContent()` | 204 no response body |
| `Results.BadRequest()` | 400 validation error |
| `Results.NotFound()` | 404 resource not found |
| `Results.Unauthorized()` | 401 authentication required |
| `Results.Forbid()` | 403 authorization failed |
| `app.MapGroup()` | Group related endpoints |
| `.WithTags()` | OpenAPI tag grouping |
| `.Produces<T>()` | Document response type |
