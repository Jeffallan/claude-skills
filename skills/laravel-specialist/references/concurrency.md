# Concurrency

## Overview

Execute multiple slow independent tasks in parallel for performance gains. Laravel serializes closures, dispatches them to hidden Artisan CLI commands in child PHP processes, then unserializes results back to the parent.

## Drivers

| Driver | Requires | Context | Notes |
|--------|----------|---------|-------|
| `process` (default) | Nothing | Any | Serializes closures to CLI subprocesses |
| `fork` | `spatie/fork` | CLI only (no forking during web requests) | Better performance |
| `sync` | Nothing | Testing | Executes sequentially in parent process, disables concurrency |

Install fork driver:

```bash
composer require spatie/fork
```

Publish config to change default driver:

```bash
php artisan config:publish concurrency
```

```php
<?php

// config/concurrency.php
'default' => 'fork',
```

## Running Concurrent Tasks

### Basic Usage

```php
<?php

use Illuminate\Support\Facades\Concurrency;
use Illuminate\Support\Facades\DB;

[$userCount, $orderCount] = Concurrency::run([
    fn () => DB::table('users')->count(),
    fn () => DB::table('orders')->count(),
]);
```

### Named Results

Access results by associative key instead of position:

```php
<?php

$results = Concurrency::run([
    'users' => fn () => DB::table('users')->count(),
    'orders' => fn () => DB::table('orders')->count(),
]);

$userCount = $results['users'];
$orderCount = $results['orders'];
```

### Specific Driver

```php
<?php

$results = Concurrency::driver('fork')->run([...]);
```

### Task Timeouts

Only supported for the `process` driver. Specify max seconds per task:

```php
<?php

[$userCount, $orderCount] = Concurrency::run([
    fn () => DB::table('users')->count(),
    fn () => DB::table('orders')->count(),
], timeout: 30);
```

Using `CarbonInterval`:

```php
<?php

use function Illuminate\Support\seconds;

Concurrency::run([...], timeout: seconds(30));
```

## Deferring Concurrent Tasks

Run closures after the HTTP response is sent — no return values:

```php
<?php

use App\Services\Metrics;
use Illuminate\Support\Facades\Concurrency;

Concurrency::defer([
    fn () => Metrics::report('users'),
    fn () => Metrics::report('orders'),
]);
```

## Best Practices

- Use `fork` driver in CLI commands/queue jobs for best performance
- Use `sync` driver in tests to avoid complexity
- Use named results for readability when you have 3+ tasks
- Set timeouts for the `process` driver to prevent hung subprocesses
- Use `defer` for non-critical background work that doesn't need results returned
- Keep closures self-contained — they execute in isolation, so no shared in-memory state
