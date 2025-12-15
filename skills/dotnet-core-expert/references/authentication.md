# Authentication & Authorization

> Reference for: .NET Core Expert
> Load when: JWT, Identity, authentication, authorization, security

## JWT Authentication Setup

```csharp
// Domain/Entities/User.cs
namespace Domain.Entities;

public class User
{
    public int Id { get; private set; }
    public string Email { get; private set; } = string.Empty;
    public string PasswordHash { get; private set; } = string.Empty;
    public string FirstName { get; private set; } = string.Empty;
    public string LastName { get; private set; } = string.Empty;
    public List<string> Roles { get; private set; } = new();
    public DateTime CreatedAt { get; private set; }
    public bool IsActive { get; private set; } = true;

    private User() { } // EF Core

    public static User Create(string email, string passwordHash, string firstName, string lastName)
    {
        return new User
        {
            Email = email,
            PasswordHash = passwordHash,
            FirstName = firstName,
            LastName = lastName,
            Roles = new List<string> { "User" },
            CreatedAt = DateTime.UtcNow
        };
    }

    public void AddRole(string role)
    {
        if (!Roles.Contains(role))
        {
            Roles.Add(role);
        }
    }
}
```

## JWT Service

```csharp
// Application/Common/Interfaces/IJwtService.cs
namespace Application.Common.Interfaces;

public interface IJwtService
{
    string GenerateToken(int userId, string email, List<string> roles);
    int? ValidateToken(string token);
}

// Infrastructure/Services/JwtService.cs
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

namespace Infrastructure.Services;

public class JwtSettings
{
    public string Secret { get; init; } = string.Empty;
    public string Issuer { get; init; } = string.Empty;
    public string Audience { get; init; } = string.Empty;
    public int ExpirationMinutes { get; init; } = 60;
}

public class JwtService : IJwtService
{
    private readonly JwtSettings _settings;

    public JwtService(IOptions<JwtSettings> settings)
    {
        _settings = settings.Value;
    }

    public string GenerateToken(int userId, string email, List<string> roles)
    {
        var claims = new List<Claim>
        {
            new(JwtRegisteredClaimNames.Sub, userId.ToString()),
            new(JwtRegisteredClaimNames.Email, email),
            new(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
        };

        claims.AddRange(roles.Select(role => new Claim(ClaimTypes.Role, role)));

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_settings.Secret));
        var credentials = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _settings.Issuer,
            audience: _settings.Audience,
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(_settings.ExpirationMinutes),
            signingCredentials: credentials
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    public int? ValidateToken(string token)
    {
        var tokenHandler = new JwtSecurityTokenHandler();
        var key = Encoding.UTF8.GetBytes(_settings.Secret);

        try
        {
            tokenHandler.ValidateToken(token, new TokenValidationParameters
            {
                ValidateIssuerSigningKey = true,
                IssuerSigningKey = new SymmetricSecurityKey(key),
                ValidateIssuer = true,
                ValidIssuer = _settings.Issuer,
                ValidateAudience = true,
                ValidAudience = _settings.Audience,
                ClockSkew = TimeSpan.Zero
            }, out SecurityToken validatedToken);

            var jwtToken = (JwtSecurityToken)validatedToken;
            var userId = int.Parse(jwtToken.Claims.First(x => x.Type == JwtRegisteredClaimNames.Sub).Value);

            return userId;
        }
        catch
        {
            return null;
        }
    }
}
```

## Password Hashing

```csharp
// Application/Common/Interfaces/IPasswordHasher.cs
namespace Application.Common.Interfaces;

public interface IPasswordHasher
{
    string HashPassword(string password);
    bool VerifyPassword(string password, string hash);
}

// Infrastructure/Services/PasswordHasher.cs
using System.Security.Cryptography;

namespace Infrastructure.Services;

public class PasswordHasher : IPasswordHasher
{
    private const int SaltSize = 16;
    private const int HashSize = 32;
    private const int Iterations = 100000;

    public string HashPassword(string password)
    {
        using var rng = RandomNumberGenerator.Create();
        var salt = new byte[SaltSize];
        rng.GetBytes(salt);

        using var pbkdf2 = new Rfc2898DeriveBytes(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256);

        var hash = pbkdf2.GetBytes(HashSize);

        var hashBytes = new byte[SaltSize + HashSize];
        Array.Copy(salt, 0, hashBytes, 0, SaltSize);
        Array.Copy(hash, 0, hashBytes, SaltSize, HashSize);

        return Convert.ToBase64String(hashBytes);
    }

    public bool VerifyPassword(string password, string hash)
    {
        var hashBytes = Convert.FromBase64String(hash);

        var salt = new byte[SaltSize];
        Array.Copy(hashBytes, 0, salt, 0, SaltSize);

        using var pbkdf2 = new Rfc2898DeriveBytes(
            password,
            salt,
            Iterations,
            HashAlgorithmName.SHA256);

        var testHash = pbkdf2.GetBytes(HashSize);

        for (int i = 0; i < HashSize; i++)
        {
            if (hashBytes[i + SaltSize] != testHash[i])
            {
                return false;
            }
        }

        return true;
    }
}
```

## Authentication Commands

```csharp
// Application/Auth/Commands/Register/RegisterCommand.cs
using MediatR;

namespace Application.Auth.Commands.Register;

public record RegisterCommand(
    string Email,
    string Password,
    string FirstName,
    string LastName
) : IRequest<AuthResponse>;

// Application/Auth/Commands/Register/RegisterCommandHandler.cs
using Application.Common.Interfaces;
using Domain.Entities;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace Application.Auth.Commands.Register;

public class RegisterCommandHandler : IRequestHandler<RegisterCommand, AuthResponse>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtService _jwtService;

    public RegisterCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher,
        IJwtService jwtService)
    {
        _context = context;
        _passwordHasher = passwordHasher;
        _jwtService = jwtService;
    }

    public async Task<AuthResponse> Handle(
        RegisterCommand request,
        CancellationToken cancellationToken)
    {
        var existingUser = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == request.Email, cancellationToken);

        if (existingUser is not null)
        {
            throw new ValidationException("Email already registered");
        }

        var passwordHash = _passwordHasher.HashPassword(request.Password);

        var user = User.Create(
            request.Email,
            passwordHash,
            request.FirstName,
            request.LastName);

        _context.Users.Add(user);
        await _context.SaveChangesAsync(cancellationToken);

        var token = _jwtService.GenerateToken(user.Id, user.Email, user.Roles);

        return new AuthResponse(token, user.Email, user.FirstName, user.LastName);
    }
}

// Application/Auth/Commands/Login/LoginCommand.cs
public record LoginCommand(
    string Email,
    string Password
) : IRequest<AuthResponse>;

// Application/Auth/Commands/Login/LoginCommandHandler.cs
public class LoginCommandHandler : IRequestHandler<LoginCommand, AuthResponse>
{
    private readonly IApplicationDbContext _context;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtService _jwtService;

    public LoginCommandHandler(
        IApplicationDbContext context,
        IPasswordHasher passwordHasher,
        IJwtService jwtService)
    {
        _context = context;
        _passwordHasher = passwordHasher;
        _jwtService = jwtService;
    }

    public async Task<AuthResponse> Handle(
        LoginCommand request,
        CancellationToken cancellationToken)
    {
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Email == request.Email, cancellationToken);

        if (user is null || !_passwordHasher.VerifyPassword(request.Password, user.PasswordHash))
        {
            throw new UnauthorizedException("Invalid credentials");
        }

        if (!user.IsActive)
        {
            throw new UnauthorizedException("Account is inactive");
        }

        var token = _jwtService.GenerateToken(user.Id, user.Email, user.Roles);

        return new AuthResponse(token, user.Email, user.FirstName, user.LastName);
    }
}

public record AuthResponse(string Token, string Email, string FirstName, string LastName);
```

## Configure Authentication in Program.cs

```csharp
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

// Configure JWT settings
builder.Services.Configure<JwtSettings>(
    builder.Configuration.GetSection("JwtSettings"));

var jwtSettings = builder.Configuration
    .GetSection("JwtSettings")
    .Get<JwtSettings>()!;

// Add authentication
builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuerSigningKey = true,
        IssuerSigningKey = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(jwtSettings.Secret)),
        ValidateIssuer = true,
        ValidIssuer = jwtSettings.Issuer,
        ValidateAudience = true,
        ValidAudience = jwtSettings.Audience,
        ValidateLifetime = true,
        ClockSkew = TimeSpan.Zero
    };
});

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();
```

## Authorization Policies

```csharp
// Configure policies
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AdminOnly", policy =>
        policy.RequireRole("Admin"));

    options.AddPolicy("UserOrAdmin", policy =>
        policy.RequireRole("User", "Admin"));

    options.AddPolicy("RequireEmailVerified", policy =>
        policy.RequireClaim("email_verified", "true"));
});

// Apply to endpoints
app.MapGet("/api/admin/users", GetAllUsers)
    .RequireAuthorization("AdminOnly");

app.MapGet("/api/profile", GetProfile)
    .RequireAuthorization();

app.MapPost("/api/products", CreateProduct)
    .RequireAuthorization("AdminOnly");
```

## Current User Service

```csharp
// Application/Common/Interfaces/ICurrentUserService.cs
namespace Application.Common.Interfaces;

public interface ICurrentUserService
{
    int? UserId { get; }
    string? Email { get; }
    bool IsAuthenticated { get; }
    bool IsInRole(string role);
}

// Infrastructure/Services/CurrentUserService.cs
using System.Security.Claims;
using Microsoft.AspNetCore.Http;

namespace Infrastructure.Services;

public class CurrentUserService : ICurrentUserService
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public CurrentUserService(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    public int? UserId
    {
        get
        {
            var userIdClaim = _httpContextAccessor.HttpContext?.User?
                .FindFirstValue(ClaimTypes.NameIdentifier);

            return int.TryParse(userIdClaim, out var userId) ? userId : null;
        }
    }

    public string? Email =>
        _httpContextAccessor.HttpContext?.User?.FindFirstValue(ClaimTypes.Email);

    public bool IsAuthenticated =>
        _httpContextAccessor.HttpContext?.User?.Identity?.IsAuthenticated ?? false;

    public bool IsInRole(string role) =>
        _httpContextAccessor.HttpContext?.User?.IsInRole(role) ?? false;
}

// Register service
builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<ICurrentUserService, CurrentUserService>();
```

## Auth Endpoints

```csharp
// WebApi/Endpoints/AuthEndpoints.cs
using Application.Auth.Commands.Login;
using Application.Auth.Commands.Register;
using MediatR;

namespace WebApi.Endpoints;

public static class AuthEndpoints
{
    public static IEndpointRouteBuilder MapAuthEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/auth")
            .WithTags("Authentication")
            .WithOpenApi();

        group.MapPost("/register", async (
            RegisterCommand command,
            ISender sender) =>
        {
            var response = await sender.Send(command);
            return Results.Ok(response);
        })
        .AllowAnonymous();

        group.MapPost("/login", async (
            LoginCommand command,
            ISender sender) =>
        {
            var response = await sender.Send(command);
            return Results.Ok(response);
        })
        .AllowAnonymous();

        group.MapGet("/me", async (
            ICurrentUserService currentUser,
            IApplicationDbContext context) =>
        {
            if (currentUser.UserId is null)
            {
                return Results.Unauthorized();
            }

            var user = await context.Users
                .FindAsync(currentUser.UserId.Value);

            return user is not null
                ? Results.Ok(new
                {
                    user.Email,
                    user.FirstName,
                    user.LastName,
                    user.Roles
                })
                : Results.NotFound();
        })
        .RequireAuthorization();

        return app;
    }
}
```

## appsettings.json

```json
{
  "JwtSettings": {
    "Secret": "your-super-secret-key-minimum-32-characters",
    "Issuer": "YourApp",
    "Audience": "YourAppUsers",
    "ExpirationMinutes": 60
  }
}
```

## Quick Reference

| Pattern | Usage |
|---------|-------|
| `RequireAuthorization()` | Endpoint requires authentication |
| `RequireAuthorization("Policy")` | Endpoint requires specific policy |
| `AllowAnonymous()` | Allow unauthenticated access |
| `RequireRole("Admin")` | Require specific role |
| JWT Bearer | Token-based authentication |
| `ICurrentUserService` | Access current user info |
| `IPasswordHasher` | Hash and verify passwords |
| `IJwtService` | Generate and validate tokens |
