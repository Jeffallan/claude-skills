# Events & Listeners

## Generating Events and Listeners

```bash
php artisan make:event PodcastProcessed
php artisan make:listener SendPodcastNotification --event=PodcastProcessed
php artisan make:event   # Interactive prompt
php artisan make:listener # Interactive prompt
php artisan event:list    # List registered listeners
php artisan event:cache   # Cache listener manifest (production)
php artisan event:clear   # Destroy event cache
```

## Defining Events

```php
<?php

namespace App\Events;

use App\Models\Order;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class OrderShipped
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(
        public Order $order,
    ) {}
}
```

## Defining Listeners

```php
<?php

namespace App\Listeners;

use App\Events\OrderShipped;

class SendShipmentNotification
{
    public function __construct() {}

    public function handle(OrderShipped $event): void
    {
        // Access the order using $event->order...
    }
}
```

Use union types to listen to multiple events:

```php
public function handle(PodcastProcessed|PodcastPublished $event): void
{
    // ...
}
```

Stop propagation by returning `false` from `handle`.

## Registering Events and Listeners

### Auto-Discovery (default)

Laravel auto-scans `app/Listeners/` for methods starting with `handle` or `__invoke`:

```php
class SendPodcastNotification
{
    public function handle(PodcastProcessed $event): void
    {
        // ...
    }
}
```

Custom discovery directories in `bootstrap/app.php`:

```php
->withEvents(discover: [
    __DIR__.'/../app/Domain/Orders/Listeners',
])

// Wildcard for multiple directories
->withEvents(discover: [
    __DIR__.'/../app/Domain/*/Listeners',
])
```

### Dynamic Discovery

Control discovery at runtime with `ShouldBeDiscovered`:

```php
use Illuminate\Contracts\Events\ShouldBeDiscovered;

class SendPodcastNotification implements ShouldBeDiscovered
{
    public function handle(PodcastProcessed $event): void
    {
        // ...
    }

    public static function shouldBeDiscovered(): bool
    {
        return app()->environment('production');
    }
}
```

### Manual Registration via `AppServiceProvider`

```php
use App\Domain\Orders\Events\PodcastProcessed;
use App\Domain\Orders\Listeners\SendPodcastNotification;
use Illuminate\Support\Facades\Event;

public function boot(): void
{
    Event::listen(
        PodcastProcessed::class,
        SendPodcastNotification::class,
    );
}
```

### Closure Listeners

```php
use App\Events\PodcastProcessed;
use Illuminate\Support\Facades\Event;

public function boot(): void
{
    Event::listen(function (PodcastProcessed $event) {
        // ...
    });
}
```

### Queueable Closure Listeners

```php
use function Illuminate\Events\queueable;

Event::listen(queueable(function (PodcastProcessed $event) {
    // ...
}));

// Customize connection, queue, delay
Event::listen(queueable(function (PodcastProcessed $event) {
    // ...
})->onConnection('redis')->onQueue('podcasts')->delay(now()->plus(seconds: 10)));

// Handle failures
Event::listen(queueable(function (PodcastProcessed $event) {
    // ...
})->catch(function (PodcastProcessed $event, Throwable $e) {
    // The queued listener failed...
}));
```

### Wildcard Listeners

```php
Event::listen('event.*', function (string $eventName, array $data) {
    // ...
});
```

## Dispatching Events

```php
// Using Dispatchable trait
OrderShipped::dispatch($order);

// Using Event facade
use Illuminate\Support\Facades\Event;
Event::dispatch(new OrderShipped($order));

// Using helper
event(new OrderShipped($order));
```

### Dispatching After Database Transactions

```php
OrderShipped::dispatchAfterCommit($order);

// Or via Event facade
Event::dispatchAfterCommit(new OrderShipped($order));
```

### Global `after_commit` Config

Set `after_commit` to `true` in `config/queue.php` per connection, or implement `ShouldQueueAfterCommit` on individual listeners.

### Deferring Events

```php
use App\Events\OrderShipped;

OrderShipped::dispatchIf($condition, $order);
OrderShipped::dispatchUnless($condition, $order);
```

## Queued Event Listeners

```php
<?php

namespace App\Listeners;

use App\Events\OrderShipped;
use Illuminate\Contracts\Queue\ShouldQueue;

class SendShipmentNotification implements ShouldQueue
{
    // ...
}
```

### Customizing Connection, Queue & Delay (PHP 8 Attributes)

```php
use Illuminate\Queue\Attributes\Connection;
use Illuminate\Queue\Attributes\Queue;
use Illuminate\Queue\Attributes\Delay;

#[Connection('sqs')]
#[Queue('listeners')]
#[Delay(60)]
class SendShipmentNotification implements ShouldQueue
{
    // ...
}
```

### Customizing at Runtime (Methods)

```php
public function viaConnection(): string
{
    return 'sqs';
}

public function viaQueue(): string
{
    return 'listeners';
}

public function withDelay(OrderShipped $event): int
{
    return $event->highPriority ? 0 : 60;
}
```

### Conditional Queueing

```php
class RewardGiftCard implements ShouldQueue
{
    public function handle(OrderCreated $event): void
    {
        // ...
    }

    public function shouldQueue(OrderCreated $event): bool
    {
        return $event->order->subtotal >= 5000;
    }
}
```

### Manually Interacting With the Queue

```php
use Illuminate\Queue\InteractsWithQueue;

class SendShipmentNotification implements ShouldQueue
{
    use InteractsWithQueue;

    public function handle(OrderShipped $event): void
    {
        if ($condition) {
            $this->release(30);
        }
    }
}
```

### Database Transactions (`ShouldQueueAfterCommit`)

```php
use Illuminate\Contracts\Queue\ShouldQueueAfterCommit;

class SendShipmentNotification implements ShouldQueueAfterCommit
{
    use InteractsWithQueue;
}
```

### Queue Listener Middleware

```php
class SendShipmentNotification implements ShouldQueue
{
    public function handle(OrderShipped $event): void
    {
        // Process the event...
    }

    public function middleware(OrderShipped $event): array
    {
        return [new RateLimited];
    }
}
```

### Encrypted Queued Listeners

```php
use Illuminate\Contracts\Queue\ShouldBeEncrypted;

class SendShipmentNotification implements ShouldQueue, ShouldBeEncrypted
{
    // ...
}
```

### Unique Event Listeners

```php
use Illuminate\Contracts\Queue\ShouldBeUnique;

class AcquireProductKey implements ShouldQueue, ShouldBeUnique
{
    public int $uniqueFor = 3600;

    public function __invoke(LicenseSaved $event): void
    {
        // ...
    }

    public function uniqueId(LicenseSaved $event): string
    {
        return 'listener:'.$event->license->id;
    }
}
```

`ShouldBeUniqueUntilProcessing` releases the lock before processing instead of after:

```php
use Illuminate\Contracts\Queue\ShouldBeUniqueUntilProcessing;

class AcquireProductKey implements ShouldQueue, ShouldBeUniqueUntilProcessing
{
    // ...
}
```

Custom cache driver for unique lock:

```php
public function uniqueVia(LicenseSaved $event): Repository
{
    return Cache::driver('redis');
}
```

### Handling Failed Jobs

```php
use Throwable;

class SendShipmentNotification implements ShouldQueue
{
    use InteractsWithQueue;

    public function handle(OrderShipped $event): void
    {
        // ...
    }

    public function failed(OrderShipped $event, Throwable $exception): void
    {
        // ...
    }
}
```

### Specifying Max Attempts & Backoff (PHP 8 Attributes)

```php
use Illuminate\Queue\Attributes\Tries;
use Illuminate\Queue\Attributes\Backoff;
use Illuminate\Queue\Attributes\MaxExceptions;
use Illuminate\Queue\Attributes\Timeout;
use Illuminate\Queue\Attributes\FailOnTimeout;

#[Tries(5)]
#[Backoff(3)]
#[MaxExceptions(3)]
#[Timeout(120)]
#[FailOnTimeout]
class SendShipmentNotification implements ShouldQueue
{
    // ...
}
```

### Exponential Backoff

```php
public function backoff(OrderShipped $event): array
{
    return [1, 5, 10]; // 1s, 5s, 10s
}
```

### Retry Until

```php
use DateTimeInterface;

public function retryUntil(): DateTimeInterface
{
    return now()->plus(minutes: 5);
}
```

## Event Subscribers

### Writing Subscribers

```php
<?php

namespace App\Listeners;

use Illuminate\Events\Dispatcher;

class UserEventSubscriber
{
    public function handleUserLogin($event): void
    {
        // ...
    }

    public function handleUserLogout($event): void
    {
        // ...
    }

    public function subscribe(Dispatcher $events): void
    {
        $events->listen(
            'Illuminate\Auth\Events\Login',
            [self::class, 'handleUserLogin']
        );

        $events->listen(
            'Illuminate\Auth\Events\Logout',
            [self::class, 'handleUserLogout']
        );
    }
}
```

### Registering Subscribers

```php
use App\Listeners\UserEventSubscriber;
use Illuminate\Support\Facades\Event;

public function boot(): void
{
    Event::subscribe(UserEventSubscriber::class);
}
```

## Testing

### Fake Events

```php
use App\Events\OrderShipped;
use Illuminate\Support\Facades\Event;

// Fake all events
Event::fake();

// Fake specific events
Event::fake([OrderShipped::class]);

// Assert event was dispatched
Event::assertDispatched(OrderShipped::class);
Event::assertDispatched(OrderShipped::class, fn ($event) => $event->order->id === 1);
Event::assertDispatchedTimes(OrderShipped::class, 3);
Event::assertNotDispatched(OrderShipped::class);
Event::assertNothingDispatched();
```

### Faking a Subset of Events

```php
Event::fakeExcept([
    OrderShipped::class,
]);

Event::fakeExcept([
    'App\Events\*',
]);
```

### Scoped Event Fakes

```php
Event::fake()->scoped();
```

Equivalent to faking all events but restoring real event dispatching at the end of the test lifecycle.

## Artisan Commands

| Command | Description |
|---------|-------------|
| `php artisan make:event` | Create a new event class (interactive without name) |
| `php artisan make:listener` | Create a new listener class (interactive without name) |
| `php artisan make:listener --event=EventName` | Create a listener for a specific event |
| `php artisan event:list` | List all registered event listeners |
| `php artisan event:cache` | Cache event listener manifest |
| `php artisan event:clear` | Clear cached event listeners |
| `php artisan optimize` | Cache routes, views, and events |

## Best Practices

1. **Keep event classes as data containers** — No business logic, just properties
2. **Use `ShouldQueue` for slow operations** — Email, HTTP calls, file generation
3. **Prefer auto-discovery** — Let Laravel scan `app/Listeners/` automatically
4. **Use `dispatchAfterCommit` for transactional safety** — Ensures data is persisted before listeners run
5. **Name events in past tense** — `OrderShipped`, `UserRegistered`, `PaymentReceived`
6. **Use PHP 8 attributes for queue config** — Cleaner than methods for static config
7. **Leverage `ShouldBeUnique` for idempotency** — Prevent duplicate processing
8. **Use Event Subscribers for related events** — Group login/logout, CRUD lifecycle
9. **Always fake events in feature tests** — Prevent accidental side effects
10. **Handle failures with `failed()` method** — Log and notify, never silently swallow
