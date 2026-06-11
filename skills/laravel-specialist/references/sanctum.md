# Sanctum Authentication

## Installation

```bash
php artisan install:api
```

This publishes the `config/sanctum.php` config file and creates the `api` routes file. The migration for `personal_access_tokens` is also published.

## User Model Setup

```php
<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens;

    // ...
}
```

## Issuing API Tokens

```php
$token = $user->createToken('token-name');

return $token->plainTextToken;

// Abilities (permissions)
$token = $user->createToken('token-name', ['post:create', 'post:read']);

// Token with expiration
use DateTimeImmutable;

$expiresAt = new DateTimeImmutable('+30 days');
$token = $user->createToken('token-name', ['*'], $expiresAt);

return $token->plainTextToken;
```

## Checking Token Abilities

```php
if ($user->tokenCan('post:create')) {
    // The user's token has the post:create ability
}

if ($user->tokenCant('post:delete')) {
    // The user's token does not have the post:delete ability
}
```

## Protecting Routes

```php
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/user', function (Request $request) {
        return $request->user();
    });

    Route::apiResource('posts', PostController::class);
});
```

## Ability Middleware

```php
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/orders', function () {
        // Token has the orders:read ability
    })->middleware(['abilities:orders:read']);

    Route::post('/orders', function () {
        // Token has the orders:create ability
    })->middleware(['abilities:orders:create']);
});

// You can also use the can middleware with policies
Route::put('/posts/{post}', function (Post $post) {
    // Token must have the ability AND pass the policy
})->middleware(['auth:sanctum', 'can:update,post']);
```

## Revoking Tokens

```php
// Revoke all tokens for the user
$user->tokens()->delete();

// Revoke the current token
$user->currentAccessToken()->delete();

// Revoke a specific token by ID
$user->tokens()->where('id', $tokenId)->delete();
```

## Token Expiration

```php
// config/sanctum.php
'expiration' => 60 * 24, // Tokens expire after 24 hours (in minutes)
// Set to null for tokens that never expire
```

```bash
# Prune expired tokens from the database
php artisan sanctum:prune-expired

# Prune expired tokens older than 24 hours
php artisan sanctum:prune-expired --hours=24
```

Expiration via `createToken`:

```php
use Carbon\CarbonImmutable;

$token = $user->createToken(
    'token-name',
    ['*'],
    CarbonImmutable::now()->addDays(7)
);
```

## SPA Authentication

```php
// config/sanctum.php
'stateful' => [
    'localhost:3000',
    'localhost:5173',
    'your-app.test',
],
```

```php
// bootstrap/app.php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        api: __DIR__.'/../routes/api.php',
        // ...
    )
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->statefulApi();
    })
    // ...
    ->create();
```

CSRF protection for SPA login:

```php
// From your SPA, make a GET request to /sanctum/csrf-cookie
await axios.get('/sanctum/csrf-cookie');

// Then make the login request
await axios.post('/login', {
    email: 'user@example.com',
    password: 'password',
});
```

Session-based SPA login:

```php
<?php

namespace App\Http\Controllers\Auth;

use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class LoginController
{
    public function store(Request $request): Response
    {
        $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required'],
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            return response()->json([
                'message' => 'The provided credentials are incorrect.',
            ], 401);
        }

        auth()->login($user);

        return response()->noContent();
    }

    public function destroy(Request $request): Response
    {
        auth('web')->logout();

        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return response()->noContent();
    }
}
```

## Mobile API Authentication

```php
<?php

namespace App\Http\Controllers\Auth;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class LoginController
{
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required'],
            'device_name' => ['required', 'string'],
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            return response()->json([
                'message' => 'The provided credentials are incorrect.',
            ], 401);
        }

        $token = $user->createToken($request->device_name, ['*'])->plainTextToken;

        return response()->json([
            'token' => $token,
            'user' => $user,
        ]);
    }

    public function destroy(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Logged out successfully.']);
    }
}
```

## Testing

```php
<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Laravel\Sanctum\Sanctum;
use Illuminate\Foundation\Testing\RefreshDatabase;

class PostTest extends TestCase
{
    use RefreshDatabase;

    public function test_authenticated_user_can_create_posts(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user, ['post:create']);

        $response = $this->postJson('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content here.',
        ]);

        $response->assertStatus(201);
    }

    public function test_user_without_ability_cannot_create(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user, ['post:read']);

        $response = $this->postJson('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content here.',
        ]);

        $response->assertStatus(403);
    }

    public function test_unauthenticated_user_cannot_access(): void
    {
        $response = $this->postJson('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content here.',
        ]);

        $response->assertStatus(401);
    }
}
```

## Middleware Registration

```php
// bootstrap/app.php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withMiddleware(function (Middleware $middleware) {
        // Enable SPA stateful authentication
        $middleware->statefulApi();

        // Register ability middleware alias
        $middleware->alias([
            'abilities' => \Laravel\Sanctum\Http\Middleware\CheckAbilities::class,
            'ability' => \Laravel\Sanctum\Http\Middleware\CheckForAnyAbility::class,
        ]);
    })
    ->create();
```

## CORS Configuration

```php
// config/cors.php
return [
    'paths' => ['api/*', 'sanctum/csrf-cookie'],
    'allowed_methods' => ['*'],
    'allowed_origins' => [env('FRONTEND_URL', 'http://localhost:3000')],
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => true,
];
```

For SPA authentication, `supports_credentials` must be `true` and the `allowed_origins` must match your frontend domain exactly.

## Best Practices

1. **Use token abilities** - Scope tokens with fine-grained permissions like `post:create`, `post:read`
2. **Regenerate tokens on password change** - Invalidate old sessions when security changes
3. **Use short-lived tokens for mobile** - Combine with refresh token pattern for long sessions
4. **Store `plainTextToken` only once** - Return it on creation; it cannot be retrieved later
5. **Always validate abilities in middleware** - Not just in the controller
6. **Use SPA auth for first-party clients** - Avoid token management on the frontend
7. **Prune expired tokens regularly** - Schedule `sanctum:prune-expired` in the console kernel
8. **Unique device names** - Use device_name or UUID to identify tokens for users managing multiple sessions
9. **Never expose `plainTextToken` in logs** - Sanitize token values in log context
10. **Use HTTPS in production** - Always encrypt token transmission
