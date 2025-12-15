# Entity Framework Core

> Reference for: .NET Core Expert
> Load when: DbContext, migrations, relationships, query optimization

## DbContext Configuration

```csharp
using Microsoft.EntityFrameworkCore;
using Domain.Entities;

namespace Infrastructure.Persistence;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(ApplicationDbContext).Assembly);
    }
}
```

## Entity Configuration

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Domain.Entities;

namespace Infrastructure.Persistence.Configurations;

public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.ToTable("Products");

        builder.HasKey(p => p.Id);

        builder.Property(p => p.Name)
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(p => p.Description)
            .HasMaxLength(500);

        builder.Property(p => p.Price)
            .HasPrecision(18, 2);

        builder.Property(p => p.CreatedAt)
            .IsRequired();

        builder.HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(p => p.Name);
        builder.HasIndex(p => p.CategoryId);
    }
}

public class CategoryConfiguration : IEntityTypeConfiguration<Category>
{
    public void Configure(EntityTypeBuilder<Category> builder)
    {
        builder.ToTable("Categories");

        builder.HasKey(c => c.Id);

        builder.Property(c => c.Name)
            .IsRequired()
            .HasMaxLength(50);

        builder.HasMany(c => c.Products)
            .WithOne(p => p.Category)
            .HasForeignKey(p => p.CategoryId);

        builder.HasData(
            new Category { Id = 1, Name = "Electronics" },
            new Category { Id = 2, Name = "Books" },
            new Category { Id = 3, Name = "Clothing" }
        );
    }
}
```

## Complex Relationships

```csharp
// Many-to-Many with payload
public class OrderItemConfiguration : IEntityTypeConfiguration<OrderItem>
{
    public void Configure(EntityTypeBuilder<OrderItem> builder)
    {
        builder.ToTable("OrderItems");

        builder.HasKey(oi => new { oi.OrderId, oi.ProductId });

        builder.Property(oi => oi.Quantity)
            .IsRequired();

        builder.Property(oi => oi.UnitPrice)
            .HasPrecision(18, 2);

        builder.HasOne(oi => oi.Order)
            .WithMany(o => o.OrderItems)
            .HasForeignKey(oi => oi.OrderId);

        builder.HasOne(oi => oi.Product)
            .WithMany()
            .HasForeignKey(oi => oi.ProductId);
    }
}

// One-to-One
public class UserProfileConfiguration : IEntityTypeConfiguration<UserProfile>
{
    public void Configure(EntityTypeBuilder<UserProfile> builder)
    {
        builder.ToTable("UserProfiles");

        builder.HasKey(up => up.Id);

        builder.HasOne(up => up.User)
            .WithOne(u => u.Profile)
            .HasForeignKey<UserProfile>(up => up.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.OwnsOne(up => up.Address, address =>
        {
            address.Property(a => a.Street).HasMaxLength(200);
            address.Property(a => a.City).HasMaxLength(100);
            address.Property(a => a.Country).HasMaxLength(100);
        });
    }
}
```

## Query Patterns

```csharp
// Async queries with filtering
public async Task<List<Product>> GetProductsByCategoryAsync(
    int categoryId,
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Include(p => p.Category)
        .Where(p => p.CategoryId == categoryId)
        .OrderBy(p => p.Name)
        .ToListAsync(cancellationToken);
}

// Pagination
public async Task<PagedResult<Product>> GetPagedProductsAsync(
    int page,
    int pageSize,
    CancellationToken cancellationToken = default)
{
    var query = _context.Products
        .AsNoTracking()
        .Include(p => p.Category);

    var totalCount = await query.CountAsync(cancellationToken);

    var items = await query
        .Skip((page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync(cancellationToken);

    return new PagedResult<Product>(items, totalCount, page, pageSize);
}

// Projection with Select
public async Task<List<ProductDto>> GetProductDtosAsync(
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Select(p => new ProductDto(
            p.Id,
            p.Name,
            p.Description,
            p.Price,
            p.Category.Name
        ))
        .ToListAsync(cancellationToken);
}

// Complex filtering with specification pattern
public async Task<List<Product>> GetProductsBySpecificationAsync(
    Expression<Func<Product, bool>> predicate,
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Where(predicate)
        .ToListAsync(cancellationToken);
}

// Aggregate queries
public async Task<decimal> GetTotalRevenueAsync(
    int year,
    CancellationToken cancellationToken = default)
{
    return await _context.Orders
        .AsNoTracking()
        .Where(o => o.CreatedAt.Year == year && o.Status == OrderStatus.Completed)
        .SelectMany(o => o.OrderItems)
        .SumAsync(oi => oi.Quantity * oi.UnitPrice, cancellationToken);
}
```

## CRUD Operations

```csharp
public class ProductRepository : IProductRepository
{
    private readonly ApplicationDbContext _context;

    public ProductRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<Product?> GetByIdAsync(
        int id,
        CancellationToken cancellationToken = default)
    {
        return await _context.Products
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == id, cancellationToken);
    }

    public async Task<List<Product>> GetAllAsync(
        CancellationToken cancellationToken = default)
    {
        return await _context.Products
            .AsNoTracking()
            .Include(p => p.Category)
            .ToListAsync(cancellationToken);
    }

    public async Task<Product> AddAsync(
        Product product,
        CancellationToken cancellationToken = default)
    {
        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);
        return product;
    }

    public async Task UpdateAsync(
        Product product,
        CancellationToken cancellationToken = default)
    {
        _context.Products.Update(product);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task DeleteAsync(
        int id,
        CancellationToken cancellationToken = default)
    {
        var product = await _context.Products.FindAsync(new object[] { id }, cancellationToken);
        if (product is not null)
        {
            _context.Products.Remove(product);
            await _context.SaveChangesAsync(cancellationToken);
        }
    }
}
```

## Migrations

```csharp
// Add migration (via CLI)
// dotnet ef migrations add InitialCreate --project Infrastructure --startup-project WebApi

// Migration file example
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "Categories",
            columns: table => new
            {
                Id = table.Column<int>(nullable: false)
                    .Annotation("SqlServer:Identity", "1, 1"),
                Name = table.Column<string>(maxLength: 50, nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Categories", x => x.Id);
            });

        migrationBuilder.InsertData(
            table: "Categories",
            columns: new[] { "Id", "Name" },
            values: new object[,]
            {
                { 1, "Electronics" },
                { 2, "Books" },
                { 3, "Clothing" }
            });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "Categories");
    }
}

// Apply migrations at startup
public static async Task Main(string[] args)
{
    var host = CreateHostBuilder(args).Build();

    using (var scope = host.Services.CreateScope())
    {
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        await context.Database.MigrateAsync();
    }

    await host.RunAsync();
}
```

## Performance Optimization

```csharp
// Compiled queries for frequently used queries
private static readonly Func<ApplicationDbContext, int, Task<Product?>> _getProductById =
    EF.CompileAsyncQuery((ApplicationDbContext context, int id) =>
        context.Products
            .Include(p => p.Category)
            .FirstOrDefault(p => p.Id == id));

public async Task<Product?> GetByIdOptimizedAsync(int id)
{
    return await _getProductById(_context, id);
}

// Split queries for complex includes
public async Task<List<Order>> GetOrdersWithItemsAsync(
    CancellationToken cancellationToken = default)
{
    return await _context.Orders
        .Include(o => o.OrderItems)
            .ThenInclude(oi => oi.Product)
        .AsSplitQuery()
        .ToListAsync(cancellationToken);
}

// Batch operations
public async Task AddRangeAsync(
    List<Product> products,
    CancellationToken cancellationToken = default)
{
    await _context.Products.AddRangeAsync(products, cancellationToken);
    await _context.SaveChangesAsync(cancellationToken);
}

// Raw SQL for complex queries
public async Task<List<ProductSalesReport>> GetProductSalesReportAsync(
    int year,
    CancellationToken cancellationToken = default)
{
    return await _context.Database
        .SqlQuery<ProductSalesReport>(
            $@"SELECT p.Id, p.Name, SUM(oi.Quantity) as TotalSold, SUM(oi.Quantity * oi.UnitPrice) as Revenue
               FROM Products p
               INNER JOIN OrderItems oi ON p.Id = oi.ProductId
               INNER JOIN Orders o ON oi.OrderId = o.Id
               WHERE YEAR(o.CreatedAt) = {year}
               GROUP BY p.Id, p.Name
               ORDER BY Revenue DESC")
        .ToListAsync(cancellationToken);
}
```

## Dependency Injection

```csharp
// Infrastructure/DependencyInjection.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("DefaultConnection"),
                b => b.MigrationsAssembly(typeof(ApplicationDbContext).Assembly.FullName)));

        services.AddScoped<IApplicationDbContext>(provider =>
            provider.GetRequiredService<ApplicationDbContext>());

        services.AddScoped<IProductRepository, ProductRepository>();

        return services;
    }
}
```

## Quick Reference

| Pattern | Usage |
|---------|-------|
| `AsNoTracking()` | Read-only queries for better performance |
| `Include()` | Eager loading related entities |
| `ThenInclude()` | Loading nested relationships |
| `AsSplitQuery()` | Prevent cartesian explosion |
| `FirstOrDefaultAsync()` | Get single or null |
| `ToListAsync()` | Execute query and get list |
| `AddAsync()` | Add entity to context |
| `Update()` | Mark entity as modified |
| `Remove()` | Mark entity for deletion |
| `SaveChangesAsync()` | Persist changes to database |
