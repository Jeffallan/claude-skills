# Inertia.js

## Overview

Inertia bridges Laravel with React, Vue, or Svelte — you write routes/controllers in Laravel, return page components, and Inertia handles the SPA experience without building a separate API.

Single codebase, server-side routing, client-side rendering.

## Installation

```bash
composer require inertiajs/inertia-laravel
php artisan inertia:middleware
```

Register the middleware in `bootstrap/app.php`:

```php
<?php

use App\Http\Middleware\HandleInertiaRequests;

->withMiddleware(function (Middleware $middleware) {
    $middleware->web(append: [
        HandleInertiaRequests::class,
    ]);
})
```

Install the client-side adapter:

```bash
npm install @inertiajs/react   # or @inertiajs/vue3, @inertiajs/svelte
```

Set up your app entry point to use Inertia:

```js
import { createInertiaApp } from '@inertiajs/react'
import { createRoot } from 'react-dom/client'

createInertiaApp({
    resolve: name => import(`./pages/${name}.jsx`),
    setup({ el, App, props }) {
        createRoot(el).render(<App {...props} />)
    },
})
```

## Root Template

The root Blade template renders the initial HTML and mounts the JS app. Located at `resources/views/app.blade.php` by default:

```blade
<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    @vite('resources/js/app.jsx')
    @inertiaHead
</head>
<body>
    @inertia
</body>
</html>
```

Configure the root template in the middleware:

```php
<?php

// app/Http/Middleware/HandleInertiaRequests.php
protected $rootView = 'app';
```

## Rendering Pages

```php
<?php

use Inertia\Inertia;

class EventsController extends Controller
{
    public function show(Event $event): \Inertia\Response
    {
        return Inertia::render('Event/Show', [
            'event'   => $event->only('id', 'title', 'start_date'),
            'canEdit' => auth()->user()->can('edit', $event),
        ]);
    }
}
```

The prop value can be any of:
- Primitives, arrays, collections, Eloquent models, API resources
- Closures (lazy — resolved only when rendered)
- `Inertia::optional(fn () => ...)` — never sent unless requested via partial reload
- `Inertia::always(...)` — always included, even in partial reloads

### Blade-Only View Data

Pass data available only in the root Blade template, not exposed to JS:

```php
<?php

return Inertia::render('Event/Edit', ['event' => $event])
    ->withViewData(['meta' => $event->meta]);
```

```blade
<meta name="description" content="{{ $meta }}">
```

## Shared Data

Configure in `HandleInertiaRequests` middleware:

```php
<?php

namespace App\Http\Middleware;

use Inertia\Middleware;
use Illuminate\Http\Request;

class HandleInertiaRequests extends Middleware
{
    public function share(Request $request): array
    {
        return array_merge(parent::share($request), [
            'app.name' => config('app.name'),
            'auth.user' => fn () => $request->user()
                ? $request->user()->only('id', 'name', 'email')
                : null,
            'flash' => [
                'message' => fn () => $request->session()->get('message'),
            ],
        ]);
    }

    // Resolved once and cached client-side across navigations
    public function shareOnce(Request $request): array
    {
        return array_merge(parent::shareOnce($request), [
            'countries' => fn () => Country::all(),
        ]);
    }
}
```

## Asset Versioning

Prevents stale JS/CSS after deployment. Configure in the middleware:

```php
<?php

public function version(Request $request): ?string
{
    return parent::version($request);
}
```

By default, uses `md5_file` on the Vite manifest. You can override with a custom version string.

When assets change, the server returns `409 Conflict` with `X-Inertia-Location` header, forcing a full page reload.

## Forms & Validation

### Server-side

```php
<?php

class UsersController extends Controller
{
    public function store(Request $request)
    {
        $validated = $request->validate([
            'first_name' => ['required', 'max:50'],
            'last_name'  => ['required', 'max:50'],
            'email'      => ['required', 'email'],
        ]);

        User::create($validated);

        return to_route('users.index');
    }
}
```

Inertia automatically sends validation errors back as props. Access them client-side:

```jsx
import { useForm } from '@inertiajs/react'

const { data, setData, post, errors } = useForm({
    first_name: '',
    last_name: '',
    email: '',
})

const submit = (e) => {
    e.preventDefault()
    post('/users')
}

return (
    <form onSubmit={submit}>
        <input value={data.first_name} onChange={e => setData('first_name', e.target.value)} />
        {errors.first_name && <div>{errors.first_name}</div>}
        <button type="submit">Save</button>
    </form>
)
```

## Redirects

```php
<?php

// Standard redirect (Inertia handles it as a client-side visit)
return redirect('/dashboard');
return to_route('dashboard');

// External redirect (full page load, breaks out of Inertia)
return Inertia::location('https://example.com');

// Back with flash
return back()->with('message', 'User created!');
```

## Responses

Inertia responses use specific HTTP codes:
- `200` — successful GET
- `201` — successful POST/PUT
- `204` — successful DELETE
- `303` — redirect after POST/PUT/PATCH (session preservation)
- `409` — asset version mismatch (forces full reload)
- `422` — validation errors

## Testing

```php
<?php

// Page assertions
$response = $this->get('/events/1');

$response->assertInertia(fn ($page) => $page
    ->component('Event/Show')
    ->has('event')
    ->where('event.id', 1)
    ->has('canEdit')
);

// Flash data assertions on redirects
$response = $this->post('/users', [
    'first_name' => 'John',
    'last_name'  => 'Doe',
    'email'      => 'john@example.com',
]);

$response->assertRedirect('/dashboard')
    ->assertInertiaFlash('message')
    ->assertInertiaFlash('message', 'User created!')
    ->assertInertiaFlash('notification.type', 'success')
    ->assertInertiaFlashMissing('error');

// Version assertion
$response->assertInertiaHasVersion('abc123');
```

Available helpers on `assertInertia`:
- `->component(string)` — matches page component name
- `->has(string\|int, ?\Closure)` — prop exists or nested assertion
- `->where(string, mixed)` — exact prop value
- `->whereAll(array)` — multiple exact values
- `->missing(string)` — prop absent
- `->count(string, int)` — array length
- `->dd()` / `->dump()` — debug

## Partial Reloads

Request only specific props to reduce payload. Use the `only` option:

```jsx
import { Link } from '@inertiajs/react'

<Link href="/users?active=true" only={['users']}>
    Show active
</Link>
```

Server-side props marked as `Inertia::optional()` are only sent when explicitly requested via partial reload.

## Best Practices

- Set up shared data for auth user, flash messages, and app config in `HandleInertiaRequests`
- Use lazy closures (`fn () => ...`) for expensive or optional data
- Use `Inertia::always()` for props that must survive partial reloads (e.g. flash messages)
- Use `Inertia::optional()` for heavy data only needed on full-page visits
- Return `303` redirects after form submissions to prevent double-submit
- Keep page components lean — move complex logic into dedicated components
- Use `@inertiaHead` in your root template for per-page `<head>` management
- Version assets via the middleware `version()` method or rely on Vite's built-in hashing
