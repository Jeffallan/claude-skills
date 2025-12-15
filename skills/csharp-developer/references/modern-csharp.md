# Modern C# Patterns

> Reference for: C# Developer
> Load when: Using C# 12 features, records, pattern matching, nullable types

## File-Scoped Namespaces and Primary Constructors

```csharp
namespace MyApp.Domain;

// Primary constructor (C# 12)
public class ProductService(IProductRepository repository, ILogger<ProductService> logger)
{
    public async Task<Product?> GetByIdAsync(int id, CancellationToken ct = default)
    {
        logger.LogInformation("Fetching product {ProductId}", id);
        return await repository.GetByIdAsync(id, ct);
    }
}

// Record with primary constructor
public record Product(int Id, string Name, decimal Price)
{
    public bool IsExpensive => Price > 100m;
}
```

## Record Types and Pattern Matching

```csharp
// Immutable record
public record Customer(int Id, string Name, string Email);

// Record with validation
public record OrderRequest(int ProductId, int Quantity)
{
    public OrderRequest : this(ProductId, Quantity)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(Quantity);
    }
}

// Pattern matching with records
public decimal CalculateDiscount(Customer customer, Order order) => customer switch
{
    { Id: > 1000 } => order.Total * 0.2m,          // Premium customer
    { Name: "VIP" } => order.Total * 0.3m,          // VIP
    _ when order.Total > 500 => order.Total * 0.1m, // Large order
    _ => 0m
};

// List patterns (C# 11+)
public string DescribeItems(int[] items) => items switch
{
    [] => "Empty",
    [var single] => $"One item: {single}",
    [var first, .., var last] => $"Multiple items from {first} to {last}",
    _ => "Unknown"
};
```

## Nullable Reference Types

```csharp
#nullable enable

public class UserService
{
    // Non-nullable parameter and return type
    public User CreateUser(string email, string name)
    {
        ArgumentNullException.ThrowIfNull(email);
        ArgumentNullException.ThrowIfNull(name);

        return new User { Email = email, Name = name };
    }

    // Nullable return type
    public User? FindUserByEmail(string? email)
    {
        if (string.IsNullOrWhiteSpace(email))
            return null;

        return _repository.Find(email);
    }

    // Required modifier (C# 11)
    public class User
    {
        public required string Email { get; init; }
        public required string Name { get; init; }
        public string? PhoneNumber { get; init; } // Optional
    }
}

// Null-forgiving operator (use sparingly)
var user = FindUserById(id)!; // Only if you're certain

// Null-coalescing assignment
_cache ??= new Dictionary<string, object>();
```

## Modern Collection Patterns

```csharp
// Collection expressions (C# 12)
int[] numbers = [1, 2, 3, 4, 5];
List<string> names = ["Alice", "Bob", "Charlie"];

// Spread operator
int[] moreNumbers = [..numbers, 6, 7, 8];
string[] allNames = [..names, "David"];

// ReadOnly collections
public IReadOnlyList<Product> Products { get; } = [product1, product2];

// Frozen collections for performance
using System.Collections.Frozen;

private static readonly FrozenDictionary<string, int> StatusCodes =
    new Dictionary<string, int>
    {
        ["Active"] = 1,
        ["Inactive"] = 2,
        ["Pending"] = 3
    }.ToFrozenDictionary();
```

## Expression-Bodied Members

```csharp
public class Product
{
    private decimal _price;

    // Expression-bodied property
    public decimal Price
    {
        get => _price;
        init => _price = value > 0 ? value : throw new ArgumentException();
    }

    // Expression-bodied method
    public decimal GetPriceWithTax(decimal taxRate) => _price * (1 + taxRate);

    // Expression-bodied constructor (with validation)
    public Product(string name) => Name = !string.IsNullOrWhiteSpace(name)
        ? name
        : throw new ArgumentException(nameof(name));

    public required string Name { get; init; }
}
```

## String Interpolation and Raw Strings

```csharp
// Raw string literals (C# 11)
var json = """
    {
        "name": "Product",
        "price": 99.99,
        "available": true
    }
    """;

// Interpolated raw strings
var productJson = $$"""
    {
        "id": {{product.Id}},
        "name": "{{product.Name}}",
        "price": {{product.Price}}
    }
    """;

// UTF-8 string literals
ReadOnlySpan<byte> utf8 = "Hello"u8;
```

## Global Using Directives

```csharp
// GlobalUsings.cs
global using System;
global using System.Collections.Generic;
global using System.Linq;
global using System.Threading;
global using System.Threading.Tasks;
global using Microsoft.Extensions.Logging;
global using Microsoft.Extensions.DependencyInjection;
```

## Source Generators (Preparation)

```csharp
// Use partial classes for source generators
public partial class UserRepository
{
    // Generator will add methods here
}

// Example: JsonSerializer source generation
using System.Text.Json.Serialization;

[JsonSerializable(typeof(Product))]
[JsonSerializable(typeof(List<Product>))]
internal partial class AppJsonContext : JsonSerializerContext
{
}

// Usage
var json = JsonSerializer.Serialize(product, AppJsonContext.Default.Product);
```

## Discriminated Unions with Records

```csharp
// Base record for result pattern
public abstract record Result<T>
{
    public record Success(T Value) : Result<T>;
    public record Failure(string Error) : Result<T>;
}

// Usage
public Result<User> GetUser(int id) =>
    _repository.Find(id) is User user
        ? new Result<User>.Success(user)
        : new Result<User>.Failure("User not found");

// Pattern matching on result
var message = GetUser(id) switch
{
    Result<User>.Success(var user) => $"Found: {user.Name}",
    Result<User>.Failure(var error) => $"Error: {error}",
    _ => "Unknown"
};
```

## Quick Reference

| Feature | C# Version | Example |
|---------|------------|---------|
| File-scoped namespace | C# 10 | `namespace MyApp;` |
| Primary constructors | C# 12 | `class Service(ILogger logger)` |
| Required members | C# 11 | `public required string Name { get; init; }` |
| Raw string literals | C# 11 | `var s = """ multi-line """;` |
| List patterns | C# 11 | `[1, 2, .., var last]` |
| Collection expressions | C# 12 | `int[] x = [1, 2, 3];` |
| Init-only properties | C# 9 | `public string Name { get; init; }` |
| Record types | C# 9 | `record Person(string Name);` |
