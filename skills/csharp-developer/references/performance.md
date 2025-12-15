# Performance Optimization

> Reference for: C# Developer
> Load when: Performance tuning, memory optimization, async patterns, Span<T>

## Span<T> and Memory<T>

```csharp
// Traditional string manipulation (allocates)
public string ProcessStringOld(string input)
{
    return input.Substring(0, 10).ToUpper();
}

// Using Span<T> (zero allocation)
public string ProcessStringNew(ReadOnlySpan<char> input)
{
    Span<char> buffer = stackalloc char[10];
    input[..10].ToUpperInvariant(buffer);
    return new string(buffer);
}

// Parsing with Span<T>
public int ParseNumber(ReadOnlySpan<char> text)
{
    return int.Parse(text);
}

// Stack allocation for small arrays
public void ProcessSmallArray()
{
    Span<int> numbers = stackalloc int[10];
    for (int i = 0; i < numbers.Length; i++)
    {
        numbers[i] = i * 2;
    }
}

// Working with byte data
public void ProcessBytes(ReadOnlySpan<byte> data)
{
    // Direct memory access, no allocations
    for (int i = 0; i < data.Length; i++)
    {
        var byte = data[i];
        // Process byte
    }
}
```

## ArrayPool for Buffer Reuse

```csharp
using System.Buffers;

public class BufferProcessor
{
    public async Task ProcessLargeDataAsync(Stream stream, CancellationToken ct)
    {
        // Rent array from pool
        var buffer = ArrayPool<byte>.Shared.Rent(4096);

        try
        {
            int bytesRead;
            while ((bytesRead = await stream.ReadAsync(buffer, ct)) > 0)
            {
                // Process buffer[0..bytesRead]
                ProcessChunk(buffer.AsSpan(0, bytesRead));
            }
        }
        finally
        {
            // Always return to pool
            ArrayPool<byte>.Shared.Return(buffer);
        }
    }

    private void ProcessChunk(ReadOnlySpan<byte> chunk)
    {
        // Processing logic
    }
}
```

## Async Best Practices

```csharp
// Use ValueTask for frequently synchronous paths
public class CacheService
{
    private readonly Dictionary<string, string> _cache = new();

    public ValueTask<string?> GetAsync(string key)
    {
        // If cached, return synchronously without allocation
        if (_cache.TryGetValue(key, out var value))
            return ValueTask.FromResult<string?>(value);

        // Otherwise, async path
        return LoadFromDatabaseAsync(key);
    }

    private async ValueTask<string?> LoadFromDatabaseAsync(string key)
    {
        var value = await _database.GetAsync(key);
        _cache[key] = value;
        return value;
    }
}

// ConfigureAwait(false) in libraries
public async Task<Data> GetDataAsync()
{
    var response = await _httpClient.GetAsync("api/data")
        .ConfigureAwait(false);
    return await response.Content.ReadFromJsonAsync<Data>()
        .ConfigureAwait(false);
}

// Avoid async void except for event handlers
public async void ButtonClick(object sender, EventArgs e) // OK for events
{
    try
    {
        await ProcessClickAsync();
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Error processing click");
    }
}

// Cancellation token support
public async Task<List<Product>> GetProductsAsync(CancellationToken ct = default)
{
    return await _dbContext.Products
        .AsNoTracking()
        .ToListAsync(ct);
}

// Parallel async operations
public async Task<(User user, Orders orders, Profile profile)> GetUserDataAsync(int userId)
{
    var userTask = _userService.GetAsync(userId);
    var ordersTask = _orderService.GetByUserAsync(userId);
    var profileTask = _profileService.GetAsync(userId);

    await Task.WhenAll(userTask, ordersTask, profileTask);

    return (await userTask, await ordersTask, await profileTask);
}
```

## Object Pooling

```csharp
using Microsoft.Extensions.ObjectPool;

// Define pooled object policy
public class StringBuilderPooledObjectPolicy : PooledObjectPolicy<StringBuilder>
{
    public override StringBuilder Create() => new StringBuilder();

    public override bool Return(StringBuilder obj)
    {
        obj.Clear();
        return obj.Capacity <= 4096; // Don't pool if too large
    }
}

// Register in DI
builder.Services.AddSingleton<ObjectPoolProvider, DefaultObjectPoolProvider>();
builder.Services.AddSingleton(serviceProvider =>
{
    var provider = serviceProvider.GetRequiredService<ObjectPoolProvider>();
    return provider.Create(new StringBuilderPooledObjectPolicy());
});

// Usage
public class MessageFormatter(ObjectPool<StringBuilder> pool)
{
    public string FormatMessage(string template, params object[] args)
    {
        var builder = pool.Get();
        try
        {
            builder.AppendFormat(template, args);
            return builder.ToString();
        }
        finally
        {
            pool.Return(builder);
        }
    }
}
```

## Benchmarking with BenchmarkDotNet

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

[MemoryDiagnoser]
[SimpleJob(warmupCount: 3, iterationCount: 5)]
public class StringBenchmarks
{
    private const string Input = "Hello, World!";

    [Benchmark(Baseline = true)]
    public string UsingSubstring()
    {
        return Input.Substring(0, 5).ToUpper();
    }

    [Benchmark]
    public string UsingSpan()
    {
        ReadOnlySpan<char> span = Input.AsSpan(0, 5);
        return span.ToString().ToUpper();
    }

    [Benchmark]
    public string UsingSpanWithStackAlloc()
    {
        ReadOnlySpan<char> input = Input;
        Span<char> buffer = stackalloc char[5];
        input[..5].ToUpperInvariant(buffer);
        return new string(buffer);
    }
}

// Program.cs
class Program
{
    static void Main(string[] args)
    {
        var summary = BenchmarkRunner.Run<StringBenchmarks>();
    }
}
```

## Collection Performance

```csharp
// Use appropriate collection types
public class CollectionExamples
{
    // Fast lookups: Dictionary over List
    private readonly Dictionary<int, Product> _productsById = new();

    // HashSet for unique items
    private readonly HashSet<string> _processedIds = new();

    // Frozen collections for readonly data (.NET 8)
    private static readonly FrozenDictionary<string, int> StatusCodes =
        new Dictionary<string, int>
        {
            ["Active"] = 1,
            ["Inactive"] = 0
        }.ToFrozenDictionary();

    // Pre-size collections when count is known
    public List<Product> CreateProducts(int count)
    {
        var products = new List<Product>(count); // Pre-allocate
        for (int i = 0; i < count; i++)
        {
            products.Add(new Product { Id = i });
        }
        return products;
    }

    // Use spans for array operations
    public int SumArray(int[] numbers)
    {
        return Sum(numbers.AsSpan());
    }

    private static int Sum(ReadOnlySpan<int> numbers)
    {
        int total = 0;
        foreach (var n in numbers)
            total += n;
        return total;
    }
}
```

## LINQ Optimization

```csharp
public class LinqOptimizations
{
    // Avoid multiple enumerations
    public void BadExample(IEnumerable<int> numbers)
    {
        if (numbers.Any())
        {
            var first = numbers.First(); // Enumerates again
            var count = numbers.Count(); // Enumerates again
        }
    }

    public void GoodExample(IEnumerable<int> numbers)
    {
        var list = numbers.ToList(); // Enumerate once
        if (list.Count > 0)
        {
            var first = list[0];
            var count = list.Count;
        }
    }

    // Use appropriate LINQ methods
    public bool HasActiveUsers(List<User> users)
    {
        return users.Any(u => u.IsActive); // Better than Count() > 0
    }

    // Avoid unnecessary ToList()
    public IEnumerable<Product> GetExpensiveProducts(IEnumerable<Product> products)
    {
        return products.Where(p => p.Price > 100); // Deferred execution
    }

    // Use Select for projections early
    public List<string> GetProductNames(IEnumerable<Product> products)
    {
        return products
            .Where(p => p.IsActive)
            .Select(p => p.Name) // Project early
            .ToList();
    }
}
```

## Response Caching and Compression

```csharp
// Program.cs
builder.Services.AddResponseCaching();
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;
    options.Providers.Add<BrotliCompressionProvider>();
    options.Providers.Add<GzipCompressionProvider>();
});

app.UseResponseCompression();
app.UseResponseCaching();

// Endpoint with caching
app.MapGet("/api/products", async (ProductService service) =>
{
    var products = await service.GetAllAsync();
    return Results.Ok(products);
})
.CacheOutput(policy => policy.Expire(TimeSpan.FromMinutes(5)));
```

## Database Query Optimization

```csharp
public class OptimizedQueries(AppDbContext context)
{
    // Use AsNoTracking for read-only queries
    public async Task<List<ProductDto>> GetProductsAsync(CancellationToken ct)
    {
        return await context.Products
            .AsNoTracking()
            .Select(p => new ProductDto
            {
                Id = p.Id,
                Name = p.Name,
                Price = p.Price
            })
            .ToListAsync(ct);
    }

    // Avoid N+1 queries with Include
    public async Task<List<Order>> GetOrdersWithItemsAsync(CancellationToken ct)
    {
        return await context.Orders
            .Include(o => o.OrderItems)
                .ThenInclude(oi => oi.Product)
            .AsNoTracking()
            .ToListAsync(ct);
    }

    // Use compiled queries for repeated queries
    private static readonly Func<AppDbContext, int, Task<Product?>> GetProductById =
        EF.CompileAsyncQuery((AppDbContext ctx, int id) =>
            ctx.Products.FirstOrDefault(p => p.Id == id));

    public Task<Product?> GetProductOptimizedAsync(int id)
    {
        return GetProductById(context, id);
    }

    // Pagination
    public async Task<PagedResult<ProductDto>> GetPagedAsync(
        int page,
        int pageSize,
        CancellationToken ct)
    {
        var query = context.Products.AsNoTracking();

        var total = await query.CountAsync(ct);

        var items = await query
            .OrderBy(p => p.Name)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(p => new ProductDto
            {
                Id = p.Id,
                Name = p.Name,
                Price = p.Price
            })
            .ToListAsync(ct);

        return new PagedResult<ProductDto>(items, total, page, pageSize);
    }
}
```

## Source Generators and AOT

```csharp
// Prepare for Native AOT
using System.Text.Json.Serialization;

[JsonSerializable(typeof(ProductDto))]
[JsonSerializable(typeof(List<ProductDto>))]
internal partial class AppJsonSerializerContext : JsonSerializerContext
{
}

// Usage in API
app.MapGet("/api/products", async (ProductService service) =>
{
    var products = await service.GetAllAsync();
    return Results.Json(products, AppJsonSerializerContext.Default.ListProductDto);
});

// .csproj for AOT
<PropertyGroup>
    <PublishAot>true</PublishAot>
    <InvariantGlobalization>true</InvariantGlobalization>
    <JsonSerializerIsReflectionEnabledByDefault>false</JsonSerializerIsReflectionEnabledByDefault>
</PropertyGroup>
```

## Memory Profiling Tips

```csharp
// Avoid boxing value types
public void AvoidBoxing()
{
    // Bad: boxing
    object obj = 42;

    // Good: use generics
    void Print<T>(T value) => Console.WriteLine(value);
    Print(42); // No boxing
}

// Use structs for small, immutable data
public readonly struct Point(int x, int y)
{
    public int X { get; } = x;
    public int Y { get; } = y;
}

// Avoid string concatenation in loops
public string BuildString(List<string> items)
{
    var builder = new StringBuilder();
    foreach (var item in items)
    {
        builder.Append(item);
    }
    return builder.ToString();
}
```

## Quick Reference

| Optimization | Use Case | Benefit |
|-------------|----------|---------|
| `Span<T>` | Array/string operations | Zero allocation |
| `ArrayPool<T>` | Temporary buffers | Reduce GC pressure |
| `ValueTask<T>` | Frequently sync paths | Lower allocation |
| `ConfigureAwait(false)` | Libraries | Avoid context capture |
| Frozen collections | Static readonly data | Faster lookups |
| `AsNoTracking()` | Read-only queries | Better EF performance |
| Object pooling | Heavy objects | Reuse instances |
| Response caching | Static responses | Reduce server load |
| Native AOT | Startup time critical | Faster cold start |
