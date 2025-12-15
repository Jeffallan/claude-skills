# Cloud-Native Patterns

> Reference for: .NET Core Expert
> Load when: Docker, Kubernetes, health checks, configuration, observability

## Dockerfile Optimization

```dockerfile
# Multi-stage build for minimal image size
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy and restore dependencies (cached layer)
COPY ["WebApi/WebApi.csproj", "WebApi/"]
COPY ["Application/Application.csproj", "Application/"]
COPY ["Infrastructure/Infrastructure.csproj", "Infrastructure/"]
COPY ["Domain/Domain.csproj", "Domain/"]
RUN dotnet restore "WebApi/WebApi.csproj"

# Copy source and build
COPY . .
WORKDIR "/src/WebApi"
RUN dotnet build "WebApi.csproj" -c Release -o /app/build

# Publish
FROM build AS publish
RUN dotnet publish "WebApi.csproj" -c Release -o /app/publish /p:UseAppHost=false

# Runtime image
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
EXPOSE 8080
EXPOSE 8081

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

COPY --from=publish /app/publish .
ENTRYPOINT ["dotnet", "WebApi.dll"]
```

## Docker Compose for Development

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - ConnectionStrings__DefaultConnection=Server=db;Database=MyApp;User=sa;Password=YourStrong@Passw0rd;TrustServerCertificate=true
      - JwtSettings__Secret=your-super-secret-key-minimum-32-characters
    depends_on:
      - db
      - redis
    networks:
      - app-network

  db:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=YourStrong@Passw0rd
    ports:
      - "1433:1433"
    volumes:
      - sqldata:/var/opt/mssql
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  sqldata:
```

## Health Checks

```csharp
using Microsoft.Extensions.Diagnostics.HealthChecks;

// Configure health checks
builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>("database")
    .AddRedis(builder.Configuration.GetConnectionString("Redis")!, "redis")
    .AddUrlGroup(new Uri("https://api.external-service.com/health"), "external-api")
    .AddCheck<CustomHealthCheck>("custom-check");

// Custom health check
public class CustomHealthCheck : IHealthCheck
{
    private readonly ILogger<CustomHealthCheck> _logger;

    public CustomHealthCheck(ILogger<CustomHealthCheck> logger)
    {
        _logger = logger;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            // Perform custom health check logic
            var isHealthy = await PerformCheckAsync(cancellationToken);

            return isHealthy
                ? HealthCheckResult.Healthy("Custom check passed")
                : HealthCheckResult.Degraded("Custom check degraded");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Health check failed");
            return HealthCheckResult.Unhealthy("Custom check failed", ex);
        }
    }

    private async Task<bool> PerformCheckAsync(CancellationToken cancellationToken)
    {
        await Task.Delay(100, cancellationToken);
        return true;
    }
}

// Map health check endpoints
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";
        var result = JsonSerializer.Serialize(new
        {
            status = report.Status.ToString(),
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                description = e.Value.Description,
                duration = e.Value.Duration
            }),
            totalDuration = report.TotalDuration
        });
        await context.Response.WriteAsync(result);
    }
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false
});
```

## Configuration Management

```csharp
// appsettings.json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=MyApp;Integrated Security=true;"
  },
  "JwtSettings": {
    "Secret": "",
    "Issuer": "MyApp",
    "Audience": "MyAppUsers",
    "ExpirationMinutes": 60
  },
  "Features": {
    "EnableSwagger": true,
    "EnableMetrics": true
  }
}

// Strongly-typed configuration
public class ApplicationSettings
{
    public const string SectionName = "ApplicationSettings";

    public required string ApplicationName { get; init; }
    public required int MaxRequestSize { get; init; }
    public required bool EnableCaching { get; init; }
}

// Register configuration
builder.Services.Configure<ApplicationSettings>(
    builder.Configuration.GetSection(ApplicationSettings.SectionName));

// Use in services
public class MyService
{
    private readonly ApplicationSettings _settings;

    public MyService(IOptions<ApplicationSettings> options)
    {
        _settings = options.Value;
    }
}

// Environment-specific configuration
builder.Configuration
    .AddJsonFile("appsettings.json", optional: false)
    .AddJsonFile($"appsettings.{builder.Environment.EnvironmentName}.json", optional: true)
    .AddEnvironmentVariables()
    .AddUserSecrets<Program>(optional: true);
```

## Structured Logging

```csharp
using Serilog;
using Serilog.Events;

// Configure Serilog
builder.Host.UseSerilog((context, configuration) =>
{
    configuration
        .MinimumLevel.Information()
        .MinimumLevel.Override("Microsoft", LogEventLevel.Warning)
        .MinimumLevel.Override("Microsoft.Hosting.Lifetime", LogEventLevel.Information)
        .Enrich.FromLogContext()
        .Enrich.WithMachineName()
        .Enrich.WithEnvironmentName()
        .WriteTo.Console(outputTemplate: "[{Timestamp:HH:mm:ss} {Level:u3}] {Message:lj}{NewLine}{Exception}")
        .WriteTo.File(
            "logs/app-.log",
            rollingInterval: RollingInterval.Day,
            outputTemplate: "{Timestamp:yyyy-MM-dd HH:mm:ss.fff zzz} [{Level:u3}] {Message:lj}{NewLine}{Exception}");

    if (context.HostingEnvironment.IsProduction())
    {
        configuration.WriteTo.Seq("http://seq:5341");
    }
});

// Use structured logging
public class ProductService
{
    private readonly ILogger<ProductService> _logger;

    public ProductService(ILogger<ProductService> logger)
    {
        _logger = logger;
    }

    public async Task<Product> CreateAsync(CreateProductRequest request)
    {
        _logger.LogInformation(
            "Creating product {ProductName} with price {Price}",
            request.Name,
            request.Price);

        try
        {
            // Create product
            var product = Product.Create(request.Name, request.Description, request.Price, request.CategoryId);

            _logger.LogInformation(
                "Product {ProductId} created successfully",
                product.Id);

            return product;
        }
        catch (Exception ex)
        {
            _logger.LogError(
                ex,
                "Failed to create product {ProductName}",
                request.Name);
            throw;
        }
    }
}
```

## Graceful Shutdown

```csharp
// Configure graceful shutdown
builder.Services.Configure<HostOptions>(options =>
{
    options.ShutdownTimeout = TimeSpan.FromSeconds(30);
});

// Background service with cancellation
public class DataProcessingService : BackgroundService
{
    private readonly ILogger<DataProcessingService> _logger;

    public DataProcessingService(ILogger<DataProcessingService> logger)
    {
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("Data processing service starting");

        try
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                await ProcessDataAsync(stoppingToken);
                await Task.Delay(TimeSpan.FromMinutes(5), stoppingToken);
            }
        }
        catch (OperationCanceledException)
        {
            _logger.LogInformation("Data processing service is stopping");
        }
    }

    private async Task ProcessDataAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Processing data batch");
        // Process data
        await Task.Delay(1000, cancellationToken);
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        _logger.LogInformation("Data processing service stopping");
        await base.StopAsync(cancellationToken);
        _logger.LogInformation("Data processing service stopped");
    }
}
```

## Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp-api
  labels:
    app: myapp-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp-api
  template:
    metadata:
      labels:
        app: myapp-api
    spec:
      containers:
      - name: api
        image: myapp/api:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ASPNETCORE_ENVIRONMENT
          value: "Production"
        - name: ConnectionStrings__DefaultConnection
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-connection
        - name: JwtSettings__Secret
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: myapp-api-service
spec:
  selector:
    app: myapp-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Distributed Caching with Redis

```csharp
// Configure Redis
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "MyApp_";
});

// Use distributed cache
public class CachedProductService
{
    private readonly IProductService _productService;
    private readonly IDistributedCache _cache;
    private readonly ILogger<CachedProductService> _logger;

    public CachedProductService(
        IProductService productService,
        IDistributedCache cache,
        ILogger<CachedProductService> logger)
    {
        _productService = productService;
        _cache = cache;
        _logger = logger;
    }

    public async Task<Product?> GetByIdAsync(int id, CancellationToken cancellationToken = default)
    {
        var cacheKey = $"product_{id}";

        var cachedData = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (cachedData is not null)
        {
            _logger.LogInformation("Cache hit for product {ProductId}", id);
            return JsonSerializer.Deserialize<Product>(cachedData);
        }

        _logger.LogInformation("Cache miss for product {ProductId}", id);
        var product = await _productService.GetByIdAsync(id, cancellationToken);

        if (product is not null)
        {
            var options = new DistributedCacheEntryOptions
            {
                AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10)
            };

            await _cache.SetStringAsync(
                cacheKey,
                JsonSerializer.Serialize(product),
                options,
                cancellationToken);
        }

        return product;
    }
}
```

## OpenTelemetry Observability

```csharp
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using OpenTelemetry.Metrics;

builder.Services.AddOpenTelemetry()
    .ConfigureResource(resource => resource.AddService("MyApp"))
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddOtlpExporter(options =>
        {
            options.Endpoint = new Uri("http://jaeger:4317");
        }))
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddRuntimeInstrumentation()
        .AddPrometheusExporter());

app.MapPrometheusScrapingEndpoint();
```

## Quick Reference

| Pattern | Usage |
|---------|-------|
| Multi-stage Dockerfile | Minimize image size |
| Health checks | Kubernetes liveness/readiness |
| Structured logging | JSON logs for aggregation |
| Distributed cache | Redis for scalability |
| Graceful shutdown | Clean resource cleanup |
| Configuration | Environment-specific settings |
| OpenTelemetry | Distributed tracing/metrics |
| HPA | Auto-scaling based on metrics |
