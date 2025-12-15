# ASP.NET Core Patterns

> Reference for: C# Developer
> Load when: Building APIs, middleware, routing, dependency injection

## Minimal API Setup

```csharp
// Program.cs
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Services
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("Default")));

builder.Services.AddScoped<IProductRepository, ProductRepository>();
builder.Services.AddScoped<ProductService>();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// Middleware pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();

// Map endpoints
app.MapProductEndpoints();

app.Run();
```

## Minimal API Endpoints with Route Groups

```csharp
public static class ProductEndpoints
{
    public static void MapProductEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products")
            .WithTags("Products")
            .RequireAuthorization();

        group.MapGet("/", GetAllProducts)
            .WithName("GetProducts")
            .Produces<List<ProductDto>>();

        group.MapGet("/{id:int}", GetProductById)
            .WithName("GetProduct")
            .Produces<ProductDto>()
            .Produces(404);

        group.MapPost("/", CreateProduct)
            .Produces<ProductDto>(201)
            .ProducesValidationProblem();

        group.MapPut("/{id:int}", UpdateProduct)
            .Produces(204)
            .Produces(404);

        group.MapDelete("/{id:int}", DeleteProduct)
            .Produces(204)
            .Produces(404);
    }

    private static async Task<IResult> GetAllProducts(
        ProductService service,
        CancellationToken ct)
    {
        var products = await service.GetAllAsync(ct);
        return Results.Ok(products);
    }

    private static async Task<IResult> GetProductById(
        int id,
        ProductService service,
        CancellationToken ct)
    {
        var product = await service.GetByIdAsync(id, ct);
        return product is not null
            ? Results.Ok(product)
            : Results.NotFound();
    }

    private static async Task<IResult> CreateProduct(
        CreateProductRequest request,
        ProductService service,
        CancellationToken ct)
    {
        var product = await service.CreateAsync(request, ct);
        return Results.CreatedAtRoute("GetProduct", new { id = product.Id }, product);
    }
}
```

## Endpoint Filters

```csharp
// Validation filter
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var request = context.Arguments.OfType<T>().FirstOrDefault();
        if (request is null)
            return Results.BadRequest("Invalid request");

        // Validate using FluentValidation or custom logic
        var validator = context.HttpContext.RequestServices
            .GetService<IValidator<T>>();

        if (validator is not null)
        {
            var result = await validator.ValidateAsync(request);
            if (!result.IsValid)
                return Results.ValidationProblem(result.ToDictionary());
        }

        return await next(context);
    }
}

// Usage
group.MapPost("/", CreateProduct)
    .AddEndpointFilter<ValidationFilter<CreateProductRequest>>();
```

## Dependency Injection Patterns

```csharp
// Service registration
public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddApplicationServices(
        this IServiceCollection services)
    {
        // Transient: new instance per request
        services.AddTransient<IEmailService, EmailService>();

        // Scoped: one instance per HTTP request
        services.AddScoped<IProductRepository, ProductRepository>();
        services.AddScoped<ProductService>();

        // Singleton: one instance for app lifetime
        services.AddSingleton<ICacheService, MemoryCacheService>();

        // Keyed services (C# 12, .NET 8)
        services.AddKeyedScoped<INotificationService, EmailNotificationService>("email");
        services.AddKeyedScoped<INotificationService, SmsNotificationService>("sms");

        return services;
    }
}

// Consuming keyed services
public class NotificationController(
    [FromKeyedServices("email")] INotificationService emailService,
    [FromKeyedServices("sms")] INotificationService smsService)
{
    public async Task SendNotifications()
    {
        await emailService.SendAsync("Hello via email");
        await smsService.SendAsync("Hello via SMS");
    }
}
```

## Options Pattern

```csharp
// appsettings.json
{
  "JwtSettings": {
    "Secret": "your-secret-key",
    "Issuer": "your-app",
    "Audience": "your-audience",
    "ExpiryMinutes": 60
  }
}

// Options class
public class JwtSettings
{
    public required string Secret { get; init; }
    public required string Issuer { get; init; }
    public required string Audience { get; init; }
    public int ExpiryMinutes { get; init; }
}

// Registration
builder.Services.Configure<JwtSettings>(
    builder.Configuration.GetSection("JwtSettings"));

// Validation
builder.Services.AddOptions<JwtSettings>()
    .BindConfiguration("JwtSettings")
    .ValidateDataAnnotations()
    .ValidateOnStart();

// Usage
public class TokenService(IOptions<JwtSettings> options)
{
    private readonly JwtSettings _settings = options.Value;

    public string GenerateToken(User user)
    {
        // Use _settings.Secret, _settings.Issuer, etc.
    }
}
```

## Custom Middleware

```csharp
// Middleware class
public class RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        var start = DateTime.UtcNow;

        try
        {
            await next(context);
        }
        finally
        {
            var elapsed = DateTime.UtcNow - start;
            logger.LogInformation(
                "Request {Method} {Path} completed in {Elapsed}ms with status {StatusCode}",
                context.Request.Method,
                context.Request.Path,
                elapsed.TotalMilliseconds,
                context.Response.StatusCode);
        }
    }
}

// Extension method
public static class MiddlewareExtensions
{
    public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder app)
    {
        return app.UseMiddleware<RequestLoggingMiddleware>();
    }
}

// Usage in Program.cs
app.UseRequestLogging();
```

## Authentication and Authorization

```csharp
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;
using System.Text;

// JWT Authentication setup
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        var jwtSettings = builder.Configuration.GetSection("JwtSettings").Get<JwtSettings>()!;

        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = jwtSettings.Issuer,
            ValidAudience = jwtSettings.Audience,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(jwtSettings.Secret))
        };
    });

// Policy-based authorization
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("RequireEmailVerified", policy =>
        policy.RequireClaim("email_verified", "true"));
});

// Usage in endpoints
app.MapGet("/admin", () => "Admin only")
    .RequireAuthorization("AdminOnly");
```

## Exception Handling

```csharp
// Global exception handler (.NET 8)
app.UseExceptionHandler(exceptionHandlerApp =>
{
    exceptionHandlerApp.Run(async context =>
    {
        var exceptionHandler = context.Features.Get<IExceptionHandlerFeature>();
        var exception = exceptionHandler?.Error;

        var logger = context.RequestServices.GetRequiredService<ILogger<Program>>();
        logger.LogError(exception, "Unhandled exception occurred");

        var problemDetails = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "An error occurred",
            Detail = context.RequestServices.GetRequiredService<IHostEnvironment>()
                .IsDevelopment() ? exception?.Message : "Please contact support"
        };

        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await context.Response.WriteAsJsonAsync(problemDetails);
    });
});
```

## Output Caching (.NET 8)

```csharp
// Enable output caching
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(builder => builder.Expire(TimeSpan.FromSeconds(10)));

    options.AddPolicy("Products", builder => builder
        .Expire(TimeSpan.FromMinutes(5))
        .SetVaryByQuery("category", "page"));
});

app.UseOutputCache();

// Apply to endpoints
app.MapGet("/api/products", GetProducts)
    .CacheOutput("Products");
```

## Rate Limiting (.NET 7+)

```csharp
using System.Threading.RateLimiting;

builder.Services.AddRateLimiter(options =>
{
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
        RateLimitPartition.GetFixedWindowLimiter(
            partitionKey: context.User.Identity?.Name ?? context.Request.Headers.Host.ToString(),
            factory: partition => new FixedWindowRateLimiterOptions
            {
                AutoReplenishment = true,
                PermitLimit = 100,
                QueueLimit = 0,
                Window = TimeSpan.FromMinutes(1)
            }));
});

app.UseRateLimiter();
```

## Health Checks

```csharp
builder.Services.AddHealthChecks()
    .AddDbContextCheck<AppDbContext>()
    .AddUrlGroup(new Uri("https://api.example.com/health"), "External API");

app.MapHealthChecks("/health");
```

## Quick Reference

| Pattern | Use Case | Lifetime |
|---------|----------|----------|
| Minimal API | Simple endpoints | - |
| Route Groups | Organize endpoints | - |
| Endpoint Filters | Validation, logging | - |
| Scoped Service | Per-request state | HTTP request |
| Singleton Service | Shared state | Application |
| Transient Service | Stateless operations | Each injection |
| Options Pattern | Configuration | - |
| Output Caching | Performance | Configurable |
| Rate Limiting | API protection | Per partition |
