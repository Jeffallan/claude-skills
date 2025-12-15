# Clean Architecture with CQRS

> Reference for: .NET Core Expert
> Load when: CQRS, MediatR, clean architecture, layers, domain-driven design

## Project Structure

```
Solution.sln
├── src/
│   ├── Domain/                    # Core business logic
│   │   ├── Entities/
│   │   ├── ValueObjects/
│   │   ├── Exceptions/
│   │   └── Interfaces/
│   ├── Application/               # Use cases, CQRS handlers
│   │   ├── Common/
│   │   ├── Products/
│   │   │   ├── Commands/
│   │   │   └── Queries/
│   │   └── DependencyInjection.cs
│   ├── Infrastructure/            # External concerns
│   │   ├── Persistence/
│   │   ├── Identity/
│   │   └── DependencyInjection.cs
│   └── WebApi/                    # API layer
│       ├── Endpoints/
│       ├── Filters/
│       └── Program.cs
└── tests/
```

## Domain Layer

```csharp
// Domain/Entities/Product.cs
namespace Domain.Entities;

public class Product
{
    public int Id { get; private set; }
    public string Name { get; private set; } = string.Empty;
    public string Description { get; private set; } = string.Empty;
    public decimal Price { get; private set; }
    public int CategoryId { get; private set; }
    public Category Category { get; private set; } = null!;
    public DateTime CreatedAt { get; private set; }
    public DateTime? UpdatedAt { get; private set; }

    private Product() { } // EF Core

    public static Product Create(string name, string description, decimal price, int categoryId)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Product name is required");

        if (price <= 0)
            throw new DomainException("Product price must be greater than zero");

        return new Product
        {
            Name = name,
            Description = description,
            Price = price,
            CategoryId = categoryId,
            CreatedAt = DateTime.UtcNow
        };
    }

    public void Update(string name, string description, decimal price)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new DomainException("Product name is required");

        if (price <= 0)
            throw new DomainException("Product price must be greater than zero");

        Name = name;
        Description = description;
        Price = price;
        UpdatedAt = DateTime.UtcNow;
    }
}

// Domain/Exceptions/DomainException.cs
namespace Domain.Exceptions;

public class DomainException : Exception
{
    public DomainException(string message) : base(message) { }
}
```

## Application Layer - Commands

```csharp
// Application/Products/Commands/CreateProduct/CreateProductCommand.cs
using MediatR;

namespace Application.Products.Commands.CreateProduct;

public record CreateProductCommand(
    string Name,
    string Description,
    decimal Price,
    int CategoryId
) : IRequest<ProductDto>;

// Application/Products/Commands/CreateProduct/CreateProductCommandHandler.cs
using Domain.Entities;
using Domain.Interfaces;
using MediatR;

namespace Application.Products.Commands.CreateProduct;

public class CreateProductCommandHandler
    : IRequestHandler<CreateProductCommand, ProductDto>
{
    private readonly IApplicationDbContext _context;

    public CreateProductCommandHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<ProductDto> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        var product = Product.Create(
            request.Name,
            request.Description,
            request.Price,
            request.CategoryId
        );

        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);

        return new ProductDto(
            product.Id,
            product.Name,
            product.Description,
            product.Price,
            product.Category.Name
        );
    }
}

// Application/Products/Commands/CreateProduct/CreateProductCommandValidator.cs
using FluentValidation;

namespace Application.Products.Commands.CreateProduct;

public class CreateProductCommandValidator : AbstractValidator<CreateProductCommand>
{
    public CreateProductCommandValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(100);

        RuleFor(x => x.Description)
            .MaximumLength(500);

        RuleFor(x => x.Price)
            .GreaterThan(0)
            .LessThan(1000000);

        RuleFor(x => x.CategoryId)
            .GreaterThan(0);
    }
}
```

## Application Layer - Queries

```csharp
// Application/Products/Queries/GetProducts/GetProductsQuery.cs
using MediatR;

namespace Application.Products.Queries.GetProducts;

public record GetProductsQuery(
    int Page = 1,
    int PageSize = 10,
    string? SearchTerm = null
) : IRequest<PagedResult<ProductDto>>;

// Application/Products/Queries/GetProducts/GetProductsQueryHandler.cs
using Application.Common.Models;
using Domain.Interfaces;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Application.Products.Queries.GetProducts;

public class GetProductsQueryHandler
    : IRequestHandler<GetProductsQuery, PagedResult<ProductDto>>
{
    private readonly IApplicationDbContext _context;

    public GetProductsQueryHandler(IApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<PagedResult<ProductDto>> Handle(
        GetProductsQuery request,
        CancellationToken cancellationToken)
    {
        var query = _context.Products
            .Include(p => p.Category)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            query = query.Where(p =>
                p.Name.Contains(request.SearchTerm) ||
                p.Description.Contains(request.SearchTerm));
        }

        var totalCount = await query.CountAsync(cancellationToken);

        var products = await query
            .OrderBy(p => p.Name)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(p => new ProductDto(
                p.Id,
                p.Name,
                p.Description,
                p.Price,
                p.Category.Name
            ))
            .ToListAsync(cancellationToken);

        return new PagedResult<ProductDto>(
            products,
            totalCount,
            request.Page,
            request.PageSize
        );
    }
}
```

## DTOs and Common Models

```csharp
// Application/Products/ProductDto.cs
namespace Application.Products;

public record ProductDto(
    int Id,
    string Name,
    string Description,
    decimal Price,
    string CategoryName
);

// Application/Common/Models/PagedResult.cs
namespace Application.Common.Models;

public record PagedResult<T>(
    List<T> Items,
    int TotalCount,
    int Page,
    int PageSize
)
{
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public bool HasPreviousPage => Page > 1;
    public bool HasNextPage => Page < TotalPages;
}
```

## Application Interfaces

```csharp
// Application/Common/Interfaces/IApplicationDbContext.cs
using Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Application.Common.Interfaces;

public interface IApplicationDbContext
{
    DbSet<Product> Products { get; }
    DbSet<Category> Categories { get; }

    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
```

## Dependency Injection Setup

```csharp
// Application/DependencyInjection.cs
using System.Reflection;
using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;

namespace Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
            cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly()));

        services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());

        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
        services.AddTransient(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));

        return services;
    }
}
```

## MediatR Pipeline Behaviors

```csharp
// Application/Common/Behaviors/ValidationBehavior.cs
using FluentValidation;
using MediatR;

namespace Application.Common.Behaviors;

public class ValidationBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public ValidationBehavior(IEnumerable<IValidator<TRequest>> validators)
    {
        _validators = validators;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!_validators.Any())
        {
            return await next();
        }

        var context = new ValidationContext<TRequest>(request);

        var validationResults = await Task.WhenAll(
            _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var failures = validationResults
            .SelectMany(r => r.Errors)
            .Where(f => f != null)
            .ToList();

        if (failures.Count != 0)
        {
            throw new ValidationException(failures);
        }

        return await next();
    }
}

// Application/Common/Behaviors/LoggingBehavior.cs
using MediatR;
using Microsoft.Extensions.Logging;

namespace Application.Common.Behaviors;

public class LoggingBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : IRequest<TResponse>
{
    private readonly ILogger<LoggingBehavior<TRequest, TResponse>> _logger;

    public LoggingBehavior(ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    {
        _logger = logger;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var requestName = typeof(TRequest).Name;

        _logger.LogInformation("Handling {RequestName}", requestName);

        var response = await next();

        _logger.LogInformation("Handled {RequestName}", requestName);

        return response;
    }
}
```

## API Integration

```csharp
// WebApi/Endpoints/ProductEndpoints.cs
using Application.Products.Commands.CreateProduct;
using Application.Products.Queries.GetProducts;
using MediatR;

namespace WebApi.Endpoints;

public static class ProductEndpoints
{
    public static IEndpointRouteBuilder MapProductEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products")
            .WithTags("Products")
            .WithOpenApi();

        group.MapGet("/", async (
            [AsParameters] GetProductsQuery query,
            ISender sender) =>
        {
            var result = await sender.Send(query);
            return Results.Ok(result);
        });

        group.MapPost("/", async (
            CreateProductCommand command,
            ISender sender) =>
        {
            var product = await sender.Send(command);
            return Results.Created($"/api/products/{product.Id}", product);
        });

        return app;
    }
}
```

## Quick Reference

| Pattern | Purpose |
|---------|---------|
| `IRequest<T>` | MediatR command/query interface |
| `IRequestHandler<TReq, TRes>` | Handler implementation |
| `IPipelineBehavior<,>` | Cross-cutting concerns |
| `IValidator<T>` | FluentValidation interface |
| `ISender` | MediatR sender for endpoints |
| Domain entities | Business logic and invariants |
| Application layer | Use cases and orchestration |
| Infrastructure | External dependencies |
