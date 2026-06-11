# Service Container

## Zero Configuration Resolution

Dependencies are auto-resolved by type-hinting in constructors. No explicit binding needed when the class has no interface dependencies.

```php
<?php

namespace App\Http\Controllers;

use App\Repositories\UserRepository;

class UserController extends Controller
{
    public function __construct(
        private UserRepository $users,
    ) {}

    public function index(): array
    {
        return $this->users->all()->toArray();
    }
}
```

This works for controllers, jobs, listeners, middleware, event handlers, and any class resolved by the container.

## When to Use the Container Manually

- Binding interfaces to implementations
- Configuring singletons or scoped instances
- Passing primitive values to constructors
- Resolving classes with tagged dependencies
- Registering contextual bindings for specific classes

## Binding Basics

### Simple Bindings

```php
use App\Services\Transistor;
use App\Services\PodcastParser;
use Illuminate\Contracts\Foundation\Application;

$this->app->bind(Transistor::class, function (Application $app) {
    return new Transistor($app->make(PodcastParser::class));
});

// Only register if not already bound
$this->app->bindIf(Transistor::class, function (Application $app) {
    return new Transistor($app->make(PodcastParser::class));
});
```

### Singletons

```php
// Resolved once per application lifecycle
$this->app->singleton(Transistor::class, function (Application $app) {
    return new Transistor($app->make(PodcastParser::class));
});

$this->app->singletonIf(Transistor::class, function (Application $app) {
    // Only registers if not already bound
});
```

### Scoped Singletons

```php
// Resolved once per request/job lifecycle (flushed by Octane/queue workers)
$this->app->scoped(Transistor::class, function (Application $app) {
    return new Transistor($app->make(PodcastParser::class));
});

$this->app->scopedIf(Transistor::class, function (Application $app) {
    // Only registers if not already bound
});
```

### Instance Binding

```php
// Bind an existing object instance
$service = new Transistor(new PodcastParser);
$this->app->instance(Transistor::class, $service);
```

## PHP 8 Attributes

### Singleton

```php
<?php

namespace App\Services;

use Illuminate\Container\Attributes\Singleton;

#[Singleton]
class Transistor
{
    // Resolved once per application lifecycle
}
```

### Scoped

```php
<?php

namespace App\Services;

use Illuminate\Container\Attributes\Scoped;

#[Scoped]
class Transistor
{
    // Resolved once per request/job lifecycle
}
```

## Binding Interfaces to Implementations

```php
$this->app->bind(
    \App\Contracts\EventPusher::class,
    \App\Services\RedisEventPusher::class
);
```

### Using the `#[Bind]` Attribute

Combine with `#[Singleton]` for singleton resolution:

```php
<?php

namespace App\Contracts;

use App\Services\RedisEventPusher;
use Illuminate\Container\Attributes\Bind;
use Illuminate\Container\Attributes\Singleton;

#[Bind(RedisEventPusher::class)]
#[Singleton]
interface EventPusher
{
    public function push(string $event, array $data): void;
}
```

Now type-hint `EventPusher` anywhere and the container resolves `RedisEventPusher` as a singleton.

## Contextual Binding

Bind different implementations based on the consuming class.

### Basic Contextual Binding

```php
use App\Contracts\EventPusher;
use App\Services\RedisEventPusher;
use App\Services\SqsEventPusher;

$this->app->when(OrderController::class)
    ->needs(EventPusher::class)
    ->give(RedisEventPusher::class);

$this->app->when(ReportController::class)
    ->needs(EventPusher::class)
    ->give(SqsEventPusher::class);
```

### Primitives and Configuration

```php
$this->app->when(ReportAggregator::class)
    ->needs('$timezone')
    ->giveConfig('app.timezone');

$this->app->when(ReportAggregator::class)
    ->needs('$maxRetries')
    ->give(3);
```

### Tagged Dependencies

```php
$this->app->when(ReportAggregator::class)
    ->needs('$reports')
    ->giveTagged('reports');

// Typed variadic dependencies
$this->app->when(Firewall::class)
    ->needs(Filter::class)
    ->give([
        NullFilter::class,
        ProfanityFilter::class,
        TooLongFilter::class,
    ]);
```

## Contextual Attributes

Inject specific resources directly into constructors without configuration.

### Auth

```php
use Illuminate\Container\Attributes\Auth;
use Illuminate\Contracts\Auth\Guard;

public function __construct(
    #[Auth('web')] protected Guard $auth,
) {}
```

### Cache

```php
use Illuminate\Container\Attributes\Cache;
use Illuminate\Contracts\Cache\Repository;

public function __construct(
    #[Cache('redis')] protected Repository $cache,
) {}
```

### Config

```php
use Illuminate\Container\Attributes\Config;

public function __construct(
    #[Config('app.timezone')] protected string $timezone,
) {}
```

### Context (Request/Job Scoped Values)

```php
use Illuminate\Container\Attributes\Context;

public function __construct(
    #[Context('uuid')] protected string $uuid,
    #[Context('ulid', hidden: true)] protected string $ulid,
) {}
```

### DB

```php
use Illuminate\Container\Attributes\DB;
use Illuminate\Database\Connection;

public function __construct(
    #[DB('mysql')] protected Connection $connection,
) {}
```

### Log

```php
use Illuminate\Container\Attributes\Log;
use Psr\Log\LoggerInterface;

public function __construct(
    #[Log('daily')] protected LoggerInterface $log,
) {}
```

### Storage

```php
use Illuminate\Container\Attributes\Storage;
use Illuminate\Contracts\Filesystem\Filesystem;

public function __construct(
    #[Storage('s3')] protected Filesystem $storage,
) {}
```

### CurrentUser

```php
use App\Models\User;
use Illuminate\Container\Attributes\CurrentUser;

Route::get('/user', function (#[CurrentUser] User $user) {
    return $user;
})->middleware('auth');
```

### Tag

```php
use Illuminate\Container\Attributes\Tag;

public function __construct(
    #[Tag('reports')] protected iterable $reports,
) {}
```

### RouteParameter

```php
use App\Models\Photo;
use Illuminate\Container\Attributes\RouteParameter;

public function __construct(
    #[RouteParameter('photo')] protected Photo $photo,
) {}
```

### Give

```php
use App\Contracts\UserRepository;
use App\Repositories\DatabaseRepository;
use Illuminate\Container\Attributes\Give;

public function __construct(
    #[Give(DatabaseRepository::class)] protected UserRepository $users,
) {}
```

### Combined Example

```php
<?php

namespace App\Http\Controllers;

use App\Contracts\UserRepository;
use App\Models\Photo;
use App\Repositories\DatabaseRepository;
use Illuminate\Container\Attributes\Auth;
use Illuminate\Container\Attributes\Cache;
use Illuminate\Container\Attributes\Config;
use Illuminate\Container\Attributes\Context;
use Illuminate\Container\Attributes\DB;
use Illuminate\Container\Attributes\Give;
use Illuminate\Container\Attributes\Log;
use Illuminate\Container\Attributes\RouteParameter;
use Illuminate\Container\Attributes\Tag;
use Illuminate\Contracts\Auth\Guard;
use Illuminate\Contracts\Cache\Repository;
use Illuminate\Database\Connection;
use Psr\Log\LoggerInterface;

class PhotoController extends Controller
{
    public function __construct(
        #[Auth('web')] protected Guard $auth,
        #[Cache('redis')] protected Repository $cache,
        #[Config('app.timezone')] protected string $timezone,
        #[Context('uuid')] protected string $uuid,
        #[Context('ulid', hidden: true)] protected string $ulid,
        #[DB('mysql')] protected Connection $connection,
        #[Give(DatabaseRepository::class)] protected UserRepository $users,
        #[Log('daily')] protected LoggerInterface $log,
        #[RouteParameter('photo')] protected Photo $photo,
        #[Tag('reports')] protected iterable $reports,
    ) {}
}
```

### Custom Contextual Attributes

Create an attribute class that implements `Illuminate\Contracts\Container\ContextualAttribute`:

```php
<?php

namespace App\Container\Attributes;

use Illuminate\Contracts\Container\ContextualAttribute;

#[\Attribute(\Attribute::TARGET_PARAMETER)]
class StripeKey implements ContextualAttribute
{
    public function __construct(
        public string $key = 'default',
    ) {}
}
```

Then resolve the value by implementing a resolver:

```php
<?php

namespace App\Providers;

use Illuminate\Container\Attributes\Config;
use Illuminate\Contracts\Container\Container;
use Illuminate\Support\ServiceProvider;

class StripeKeyResolver extends ServiceProvider
{
    public function register(): void
    {
        StripeKey::resolveUsing(function (StripeKey $attribute, Container $container) {
            return $container->make(Config::class)->get("services.stripe.{$attribute->key}_key");
        });
    }
}
```

Usage:

```php
public function __construct(
    #[StripeKey('secret')] protected string $stripeKey,
) {}
```

## Tagging

```php
$this->app->tag([
    CpuReport::class,
    MemoryReport::class,
], 'reports');

// Retrieve tagged bindings
$this->app->tagged('reports'); // returns iterable of resolved instances
```

## Extending Bindings

Decorate or replace a resolved service:

```php
$this->app->extend(Service::class, function (Service $service, Application $app) {
    return new DecoratedService($service);
});
```

## Resolving

```php
// From anywhere
$api = resolve('HelpSpot\API');

// From a service provider
$api = $this->app->make('HelpSpot\API');

// With additional parameters
$api = $this->app->makeWith('HelpSpot\API', ['key' => 'abc123']);

// Check if bound
$bound = $this->app->bound('HelpSpot\API');

// Helper and facade
$api = app('HelpSpot\API');
$api = \App::make('HelpSpot\API');
```

## Automatic Injection

Type-hint dependencies in constructors and they resolve automatically. Supported locations:

- Controllers
- Jobs
- Event listeners
- Queue listeners
- Middleware
- Route closures
- `handle()` methods of commands and jobs

```php
// Route closure
Route::get('/users', function (UserRepository $users) {
    return $users->all();
});
```

## Method Invocation

```php
use App\Services\PaymentProcessor;
use Illuminate\Support\Facades\App;

$result = App::call(function (PaymentProcessor $processor) {
    return $processor->charge(100);
});

// On an object method
$result = App::call([$this, 'methodName']);
```

## Container Events

### Resolving Events

```php
$this->app->resolving(Transistor::class, function (Transistor $transistor, Application $app) {
    // Called when Transistor is resolved
});

$this->app->resolving(function (mixed $object, Application $app) {
    // Called when any object is resolved
});
```

### Rebinding Events

```php
$this->app->bind(EventPusher::class, RedisEventPusher::class);

$this->app->rebinding(EventPusher::class, function (Application $app, EventPusher $newInstance) {
    // Called whenever the binding is re-bound
});

$this->app->bind(EventPusher::class, SqsEventPusher::class);
// Triggers the rebinding closure
```

## PSR-11

The container implements `Psr\Container\ContainerInterface`:

```php
use Psr\Container\ContainerInterface;

class SomeClass
{
    public function __construct(
        private ContainerInterface $container,
    ) {}

    public function handle(): void
    {
        $service = $this->container->get(Service::class);
    }
}
```

## Best Practices

1. **Use auto-injection whenever possible** — let the container resolve without explicit binding
2. **Bind interfaces, not implementations** — enables swapping and testing
3. **Use `#[Singleton]` for stateless services** — HTTP clients, parsers, configuration providers
4. **Use `#[Scoped]` for request-scoped state** — current user, request context
5. **Prefer contextual attributes over `when()->needs()->give()` chains** — cleaner DX
6. **Use `#[Bind]` on interfaces** — eliminates manual provider registration
7. **Resolve from the container only at composition roots** — avoid `resolve()` or `app()->make()` deep in business logic
8. **Use `tag()` for collections of similar services** — report generators, payment gateways, notification channels
9. **Use `extend()` to decorate services** — add logging, caching, or metrics without modifying the original class
10. **Register bindings in the `register()` method of a ServiceProvider** — never in `boot()`
