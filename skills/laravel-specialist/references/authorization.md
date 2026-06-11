# Authorization

## Gates

### Defining Gates

```php
<?php

namespace App\Providers;

use App\Models\Post;
use App\Models\User;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Gate::define('update-post', function (User $user, Post $post) {
            return $user->id === $post->user_id;
        });

        Gate::define('delete-post', function (User $user, Post $post) {
            return $user->id === $post->user_id;
        });

        Gate::define('publish-post', function (User $user, Post $post) {
            return $user->isAdmin() || $user->id === $post->user_id;
        });
    }
}
```

### Authorizing via Gates

```php
<?php

use Illuminate\Support\Facades\Gate;

// Basic checks
if (Gate::allows('update-post', $post)) {
    // User can update
}

if (Gate::denies('update-post', $post)) {
    // User cannot update
}

// Authorize or abort
Gate::authorize('update-post', $post);

// Inspect returns a response object
$response = Gate::inspect('update-post', $post);

if ($response->allowed()) {
    // Action allowed
} else {
    echo $response->message();
}
```

### Gate Responses

```php
<?php

namespace App\Providers;

use App\Models\Post;
use App\Models\User;
use Illuminate\Auth\Access\Response;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Gate::define('update-post', function (User $user, Post $post) {
            return $user->id === $post->user_id
                ? Response::allow()
                : Response::deny('You do not own this post.');
        });

        Gate::define('view-report', function (User $user) {
            return $user->isAdmin()
                ? Response::allow()
                : Response::denyWithStatus(403);
        });

        Gate::define('view-financials', function (User $user) {
            return $user->isAdmin()
                ? Response::allow()
                : Response::denyAsNotFound();
        });
    }
}
```

### Before / After Interception

```php
<?php

namespace App\Providers;

use App\Models\User;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        // Before checks run before all other gate checks
        Gate::before(function (User $user, string $ability) {
            if ($user->isSuperAdmin()) {
                return true;
            }
        });

        // After checks run after all other gate checks
        Gate::after(function (User $user, string $ability, ?bool $result, mixed $arguments) {
            if ($user->isAdmin() && $ability === 'delete-post') {
                return true;
            }
        });
    }
}
```

### Inline Authorization

```php
<?php

use Illuminate\Support\Facades\Gate;

Gate::allowIf(fn (User $user) => $user->isAdmin());

Gate::denyIf(fn (User $user) => $user->isBanned());
```

## Policies

### Generating Policies

```bash
php artisan make:policy PostPolicy
php artisan make:policy PostPolicy --model=Post
```

```php
<?php

namespace App\Policies;

use App\Models\Post;
use App\Models\User;

class PostPolicy
{
    public function viewAny(User $user): bool
    {
        return true;
    }

    public function view(User $user, Post $post): bool
    {
        return true;
    }

    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail();
    }

    public function update(User $user, Post $post): bool
    {
        return $user->id === $post->user_id;
    }

    public function delete(User $user, Post $post): bool
    {
        return $this->update($user, $post);
    }

    public function restore(User $user, Post $post): bool
    {
        return $user->isAdmin();
    }

    public function forceDelete(User $user, Post $post): bool
    {
        return $user->isAdmin();
    }
}
```

### Policy Auto-Discovery

Laravel automatically discovers policies when the model and policy follow naming conventions (`Post` => `PostPolicy`). Manual registration is only needed for custom model/policy names:

```php
<?php

namespace App\Providers;

use App\Models\Post;
use App\Policies\PostPolicy;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Gate::policy(Post::class, PostPolicy::class);
    }
}
```

### `#[UsePolicy]` Attribute

```php
<?php

namespace App\Http\Controllers;

use App\Models\Post;
use App\Policies\PostPolicy;
use Illuminate\Routing\Controller;
use Illuminate\Foundation\Auth\Access\Attributes\UsePolicy;

#[UsePolicy(PostPolicy::class)]
class PostController extends Controller
{
    // Controller actions automatically authorize against PostPolicy
}
```

### Policy Methods Without Models

```php
<?php

namespace App\Policies;

use App\Models\User;

class PostPolicy
{
    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail();
    }

    // Guest users (not logged in)
    public function view(?User $user, Post $post): bool
    {
        if ($post->isPublished()) {
            return true;
        }

        return $user?->id === $post->user_id;
    }
}
```

### Policy Responses

```php
<?php

namespace App\Policies;

use App\Models\Post;
use App\Models\User;
use Illuminate\Auth\Access\Response;

class PostPolicy
{
    public function update(User $user, Post $post): Response
    {
        return $user->id === $post->user_id
            ? Response::allow()
            : Response::deny('You do not own this post.');
    }

    public function archive(User $user, Post $post): Response
    {
        return $user->isAdmin()
            ? Response::allow()
            : Response::denyWithStatus(403);
    }

    public function viewDeleted(User $user): Response
    {
        return $user->isAdmin()
            ? Response::allow()
            : Response::denyAsNotFound();
    }
}
```

### Policy Filters

```php
<?php

namespace App\Policies;

use App\Models\User;

class PostPolicy
{
    public function before(User $user, string $ability): ?bool
    {
        if ($user->isSuperAdmin()) {
            return true;
        }

        return null; // Let the method decide
    }
}
```

## Authorizing via User Model

```php
<?php

if ($user->can('update', $post)) {
    // User can update
}

if ($user->cannot('update', $post)) {
    // User cannot update
}

// Authorize or abort
$user->can('create', Post::class);
```

## Authorizing via Gate Facade

```php
<?php

use Illuminate\Support\Facades\Gate;

// Using the gate facade to authorize
Gate::authorize('update-post', $post);

// Using for a specific user
if (Gate::forUser($otherUser)->allows('update-post', $post)) {
    // $otherUser can update
}
```

## Authorizing via Middleware

```php
<?php

use Illuminate\Support\Facades\Route;

// Using the can middleware
Route::put('/posts/{post}', function (Post $post) {
    // User must be authorized to update the post
})->middleware('can:update,post');

// With model binding
Route::delete('/posts/{post}', function (Post $post) {
    // User must be authorized to delete
})->middleware('can:delete,post');

// For create actions (no model instance)
Route::post('/posts', function () {
    // User must be authorized to create
})->middleware('can:create,App\Models\Post');

// Multiple abilities
Route::get('/reports', function () {
    // User must have at least one ability
})->middleware('can:view-reports|export-reports');
```

## Authorizing via Blade

```blade
@can('update', $post)
    <a href="{{ route('posts.edit', $post) }}">Edit</a>
@endcan

@cannot('update', $post)
    <span>You cannot edit this post.</span>
@endcannot

@canany(['update', 'delete'], $post)
    <div class="actions">
        @can('update', $post)
            <button>Edit</button>
        @endcan
        @can('delete', $post)
            <button>Delete</button>
        @endcan
    </div>
@endcanany

@can('create', App\Models\Post::class)
    <a href="{{ route('posts.create') }}">New Post</a>
@endcan
```

## Authorization & Inertia

```php
<?php

namespace App\Http\Middleware;

use App\Models\Post;
use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    public function share(Request $request): array
    {
        return [
            ...parent::share($request),
            'auth' => [
                'user' => $request->user(),
                'permissions' => [
                    'canCreatePosts' => $request->user()?->can('create', Post::class),
                    'canManageUsers' => $request->user()?->can('manage-users'),
                ],
            ],
        ];
    }
}
```

```vue
<template>
    <button v-if="$page.props.auth.permissions.canCreatePosts">
        New Post
    </button>
</template>
```

## Supplying Additional Context

```php
<?php

namespace App\Policies;

use App\Models\Post;
use App\Models\User;

class PostPolicy
{
    public function forceDelete(User $user, Post $post, bool $hardDelete = false): bool
    {
        if ($hardDelete && $user->isSuperAdmin()) {
            return true;
        }

        return false;
    }
}
```

Passing extra parameters:

```php
<?php

use App\Models\Post;

$user->can('forceDelete', [$post, true]);

Gate::authorize('forceDelete', [$post, true]);

// In blade
@can('forceDelete', [$post, true])
    // Show permanent delete button
@endcan

// In middleware (use array syntax)
Route::delete('/posts/{post}/force', function (Post $post) {
    //
})->middleware('can:forceDelete,post,true');
```

## Best Practices

1. **Prefer policies over gates** - Policies keep authorization organized per model
2. **Use `#[UsePolicy]` on controllers** - Cleaner than authorizing manually in each method
3. **Return `Response::denyWithStatus()`** - Return proper HTTP status codes for API endpoints
4. **Use `before()` sparingly** - Only for super-admin shortcuts; let individual methods decide
5. **Handle guest users explicitly** - Type-hint `?User` for abilities guests can access
6. **Authorize at the route level** - Use `can` middleware for cleaner controller logic
7. **Share permissions for SPAs** - Precompute permissions for Inertia or Vue frontends
8. **Use `denyAsNotFound()`** - Hide sensitive resources from unauthorized users
9. **Keep policies single-responsibility** - One policy per model; use gates for non-model actions
10. **Always use the user parameter** - Never rely on `auth()->user()` inside a policy
