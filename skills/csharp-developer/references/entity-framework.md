# Entity Framework Core Patterns

> Reference for: C# Developer
> Load when: Database operations, EF Core, migrations, query optimization

## DbContext Setup

```csharp
using Microsoft.EntityFrameworkCore;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Apply all configurations from assembly
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);

        // Global query filters
        modelBuilder.Entity<Product>()
            .HasQueryFilter(p => !p.IsDeleted);
    }
}

// Configuration class (recommended)
public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.ToTable("Products");

        builder.HasKey(p => p.Id);

        builder.Property(p => p.Name)
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(p => p.Price)
            .HasPrecision(18, 2);

        builder.HasIndex(p => p.Sku)
            .IsUnique();

        // Relationships
        builder.HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);
    }
}
```

## Entity Models

```csharp
// Base entity
public abstract class BaseEntity
{
    public int Id { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public bool IsDeleted { get; set; }
}

// Product entity
public class Product : BaseEntity
{
    public required string Name { get; set; }
    public required string Sku { get; set; }
    public decimal Price { get; set; }
    public string? Description { get; set; }

    // Navigation properties
    public int CategoryId { get; set; }
    public Category Category { get; set; } = null!;

    public ICollection<OrderItem> OrderItems { get; set; } = [];
}

// Value objects (owned types)
public class Address
{
    public required string Street { get; init; }
    public required string City { get; init; }
    public required string Country { get; init; }
    public required string PostalCode { get; init; }
}

public class Order : BaseEntity
{
    public required string OrderNumber { get; set; }
    public Address ShippingAddress { get; set; } = null!;
}

// Configuration for owned type
builder.OwnsOne(o => o.ShippingAddress, address =>
{
    address.Property(a => a.Street).HasMaxLength(200);
    address.Property(a => a.City).HasMaxLength(100);
});
```

## Repository Pattern

```csharp
public interface IRepository<T> where T : BaseEntity
{
    Task<T?> GetByIdAsync(int id, CancellationToken ct = default);
    Task<List<T>> GetAllAsync(CancellationToken ct = default);
    Task<T> AddAsync(T entity, CancellationToken ct = default);
    Task UpdateAsync(T entity, CancellationToken ct = default);
    Task DeleteAsync(int id, CancellationToken ct = default);
}

public class Repository<T>(AppDbContext context) : IRepository<T> where T : BaseEntity
{
    private readonly DbSet<T> _dbSet = context.Set<T>();

    public async Task<T?> GetByIdAsync(int id, CancellationToken ct = default)
    {
        return await _dbSet.FindAsync([id], cancellationToken: ct);
    }

    public async Task<List<T>> GetAllAsync(CancellationToken ct = default)
    {
        return await _dbSet.AsNoTracking().ToListAsync(ct);
    }

    public async Task<T> AddAsync(T entity, CancellationToken ct = default)
    {
        entity.CreatedAt = DateTime.UtcNow;
        await _dbSet.AddAsync(entity, ct);
        await context.SaveChangesAsync(ct);
        return entity;
    }

    public async Task UpdateAsync(T entity, CancellationToken ct = default)
    {
        entity.UpdatedAt = DateTime.UtcNow;
        _dbSet.Update(entity);
        await context.SaveChangesAsync(ct);
    }

    public async Task DeleteAsync(int id, CancellationToken ct = default)
    {
        var entity = await GetByIdAsync(id, ct);
        if (entity is not null)
        {
            entity.IsDeleted = true;
            await UpdateAsync(entity, ct);
        }
    }
}
```

## Query Optimization

```csharp
public class ProductRepository(AppDbContext context)
{
    // AsNoTracking for read-only queries
    public async Task<List<ProductDto>> GetProductsAsync(CancellationToken ct = default)
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

    // Include related data (eager loading)
    public async Task<Product?> GetProductWithCategoryAsync(int id, CancellationToken ct = default)
    {
        return await context.Products
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == id, ct);
    }

    // Split queries for collections
    public async Task<Order?> GetOrderWithItemsAsync(int id, CancellationToken ct = default)
    {
        return await context.Orders
            .Include(o => o.OrderItems)
                .ThenInclude(oi => oi.Product)
            .AsSplitQuery() // Prevents cartesian explosion
            .FirstOrDefaultAsync(o => o.Id == id, ct);
    }

    // Filtered includes (.NET 5+)
    public async Task<Category?> GetCategoryWithActiveProducts(
        int id,
        CancellationToken ct = default)
    {
        return await context.Categories
            .Include(c => c.Products.Where(p => p.Price > 0))
            .FirstOrDefaultAsync(c => c.Id == id, ct);
    }

    // Projection for performance
    public async Task<List<ProductSummaryDto>> GetProductSummariesAsync(
        CancellationToken ct = default)
    {
        return await context.Products
            .Where(p => !p.IsDeleted)
            .Select(p => new ProductSummaryDto
            {
                Id = p.Id,
                Name = p.Name,
                Price = p.Price,
                CategoryName = p.Category.Name,
                OrderCount = p.OrderItems.Count
            })
            .ToListAsync(ct);
    }
}
```

## Compiled Queries

```csharp
// Define compiled query as static field
private static readonly Func<AppDbContext, int, CancellationToken, Task<Product?>>
    GetProductByIdCompiled = EF.CompileAsyncQuery(
        (AppDbContext context, int id, CancellationToken ct) =>
            context.Products
                .Include(p => p.Category)
                .FirstOrDefault(p => p.Id == id));

public async Task<Product?> GetProductByIdOptimized(int id, CancellationToken ct = default)
{
    return await GetProductByIdCompiled(context, id, ct);
}
```

## Bulk Operations

```csharp
public class BulkProductRepository(AppDbContext context)
{
    // Bulk insert
    public async Task AddRangeAsync(List<Product> products, CancellationToken ct = default)
    {
        await context.Products.AddRangeAsync(products, ct);
        await context.SaveChangesAsync(ct);
    }

    // Bulk update with ExecuteUpdate (.NET 7+)
    public async Task IncreasePricesAsync(decimal percentage, CancellationToken ct = default)
    {
        await context.Products
            .Where(p => !p.IsDeleted)
            .ExecuteUpdateAsync(
                setters => setters.SetProperty(p => p.Price, p => p.Price * (1 + percentage)),
                ct);
    }

    // Bulk delete with ExecuteDelete (.NET 7+)
    public async Task DeleteDiscontinuedAsync(CancellationToken ct = default)
    {
        await context.Products
            .Where(p => p.IsDeleted)
            .ExecuteDeleteAsync(ct);
    }
}
```

## Transactions

```csharp
public class OrderService(AppDbContext context)
{
    public async Task<Order> CreateOrderAsync(CreateOrderDto dto, CancellationToken ct = default)
    {
        using var transaction = await context.Database.BeginTransactionAsync(ct);

        try
        {
            var order = new Order
            {
                OrderNumber = GenerateOrderNumber(),
                CreatedAt = DateTime.UtcNow
            };

            await context.Orders.AddAsync(order, ct);
            await context.SaveChangesAsync(ct);

            // Update inventory
            foreach (var item in dto.Items)
            {
                var product = await context.Products.FindAsync([item.ProductId], ct);
                if (product is null)
                    throw new InvalidOperationException($"Product {item.ProductId} not found");

                product.Stock -= item.Quantity;
            }

            await context.SaveChangesAsync(ct);
            await transaction.CommitAsync(ct);

            return order;
        }
        catch
        {
            await transaction.RollbackAsync(ct);
            throw;
        }
    }
}
```

## Migrations

```bash
# Add migration
dotnet ef migrations add InitialCreate

# Update database
dotnet ef database update

# Generate SQL script
dotnet ef migrations script

# Remove last migration (if not applied)
dotnet ef migrations remove

# Revert to specific migration
dotnet ef database update PreviousMigrationName
```

```csharp
// Apply migrations programmatically
public static async Task ApplyMigrationsAsync(IServiceProvider services)
{
    using var scope = services.CreateScope();
    var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await context.Database.MigrateAsync();
}
```

## Change Tracking Optimization

```csharp
// Disable change tracking for read-only operations
context.ChangeTracker.QueryTrackingBehavior = QueryTrackingBehavior.NoTracking;

// Attach entity for updates without loading
public async Task UpdateProductPriceAsync(int id, decimal newPrice, CancellationToken ct = default)
{
    var product = new Product { Id = id };
    context.Products.Attach(product);
    product.Price = newPrice;
    context.Entry(product).Property(p => p.Price).IsModified = true;
    await context.SaveChangesAsync(ct);
}
```

## Interceptors (.NET 6+)

```csharp
public class AuditInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken ct = default)
    {
        if (eventData.Context is null)
            return base.SavingChangesAsync(eventData, result, ct);

        var entries = eventData.Context.ChangeTracker.Entries<BaseEntity>();

        foreach (var entry in entries)
        {
            if (entry.State == EntityState.Added)
                entry.Entity.CreatedAt = DateTime.UtcNow;
            else if (entry.State == EntityState.Modified)
                entry.Entity.UpdatedAt = DateTime.UtcNow;
        }

        return base.SavingChangesAsync(eventData, result, ct);
    }
}

// Register interceptor
builder.Services.AddDbContext<AppDbContext>((sp, options) =>
{
    options.UseSqlServer(connectionString)
        .AddInterceptors(new AuditInterceptor());
});
```

## Quick Reference

| Operation | Method | Notes |
|-----------|--------|-------|
| Read-only query | `.AsNoTracking()` | Better performance |
| Eager loading | `.Include()` | Load related data |
| Filtered include | `.Include(x => x.Items.Where(...))` | .NET 5+ |
| Split query | `.AsSplitQuery()` | Avoid cartesian explosion |
| Bulk update | `.ExecuteUpdateAsync()` | .NET 7+ |
| Bulk delete | `.ExecuteDeleteAsync()` | .NET 7+ |
| Compiled query | `EF.CompileAsyncQuery()` | Reusable queries |
| Soft delete | Query filter | `HasQueryFilter()` |
