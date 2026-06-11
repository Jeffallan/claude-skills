# Package Development

## Overview

Packages are the primary way to add functionality to Laravel. This guide covers Laravel-specific packages with routes, controllers, views, and configuration.

## Package Discovery

Auto-register service providers and facades via `composer.json`:

```json
{
    "extra": {
        "laravel": {
            "providers": [
                "Barryvdh\\Debugbar\\ServiceProvider"
            ],
            "aliases": {
                "Debugbar": "Barryvdh\\Debugbar\\Facade"
            }
        }
    }
}
```

### Opting Out of Discovery

In the application's `composer.json`:

```json
{
    "extra": {
        "laravel": {
            "dont-discover": [
                "barryvdh/laravel-debugbar"
            ]
        }
    }
}
```

Disable for all packages:

```json
"dont-discover": ["*"]
```

## Service Providers

Extend `Illuminate\Support\ServiceProvider`. Two methods: `register` and `boot`.

```php
<?php

namespace Vendor\Package;

use Illuminate\Support\ServiceProvider;

class PackageServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Bind into container, merge config
    }

    public function boot(): void
    {
        // Load routes, views, migrations, etc.
    }
}
```

## Resources

### Configuration

Publish config files:

```php
<?php

public function boot(): void
{
    $this->publishes([
        __DIR__.'/../config/courier.php' => config_path('courier.php'),
    ]);
}
```

Merge default config (in `register` method):

```php
<?php

public function register(): void
{
    $this->mergeConfigFrom(
        __DIR__.'/../config/courier.php', 'courier'
    );
}
```

Only merges the first level of the array. Users access config via `config('courier.option')`.

Do **not** use closures in config files — they cannot be serialized by `config:cache`.

### Routes

```php
<?php

public function boot(): void
{
    $this->loadRoutesFrom(__DIR__.'/../routes/web.php');
}
```

Respects route caching automatically.

### Migrations

```php
<?php

public function boot(): void
{
    $this->publishesMigrations([
        __DIR__.'/../database/migrations' => database_path('migrations'),
    ]);
}
```

Laravel auto-updates migration timestamps when publishing.

### Language Files

Load translations:

```php
<?php

public function boot(): void
{
    $this->loadTranslationsFrom(__DIR__.'/../lang', 'courier');
}
```

Usage: `trans('courier::messages.welcome')`.

JSON translations:

```php
<?php

$this->loadJsonTranslationsFrom(__DIR__.'/../lang');
```

Publishing language files:

```php
<?php

$this->publishes([
    __DIR__.'/../lang' => $this->app->langPath('vendor/courier'),
]);
```

### Views

```php
<?php

public function boot(): void
{
    $this->loadViewsFrom(__DIR__.'/../resources/views', 'courier');
}
```

Usage: `view('courier::dashboard')`.

Override in app by placing views in `resources/views/vendor/courier/`.

Publishing views:

```php
<?php

$this->publishes([
    __DIR__.'/../resources/views' => resource_path('views/vendor/courier'),
]);
```

### View Components

Register a named component:

```php
<?php

use Illuminate\Support\Facades\Blade;
use VendorPackage\View\Components\AlertComponent;

public function boot(): void
{
    Blade::component('package-alert', AlertComponent::class);
}
```

Usage: `<x-package-alert />`.

Autoload with component namespace:

```php
<?php

Blade::componentNamespace('Nightshade\\Views\\Components', 'nightshade');
```

Usage: `<x-nightshade::calendar />`, `<x-nightshade::color-picker />`.

Anonymous components: place in a `components` subdirectory of your package's views directory. Render with `<x-courier::alert />`.

### "About" Artisan Command

Add info to `php artisan about`:

```php
<?php

use Illuminate\Foundation\Console\AboutCommand;

public function boot(): void
{
    AboutCommand::add('My Package', fn () => ['Version' => '1.0.0']);
}
```

## Commands

```php
<?php

use Courier\Console\Commands\InstallCommand;
use Courier\Console\Commands\NetworkCommand;

public function boot(): void
{
    if ($this->app->runningInConsole()) {
        $this->commands([
            InstallCommand::class,
            NetworkCommand::class,
        ]);
    }
}
```

### Optimize Commands

Register commands that run during `optimize` / `optimize:clear`:

```php
<?php

public function boot(): void
{
    if ($this->app->runningInConsole()) {
        $this->optimizes(
            optimize: 'package:optimize',
            clear: 'package:clear-optimizations',
        );
    }
}
```

### Reload Commands

Register commands that run during `reload`:

```php
<?php

public function boot(): void
{
    if ($this->app->runningInConsole()) {
        $this->reloads('package:reload');
    }
}
```

## Public Assets

Publish JS, CSS, images to `public/vendor/{package}`:

```php
<?php

public function boot(): void
{
    $this->publishes([
        __DIR__.'/../public' => public_path('vendor/courier'),
    ], 'public');
}
```

Users publish with `--force` flag to overwrite on updates:

```bash
php artisan vendor:publish --tag=public --force
```

## Publishing File Groups

Tag publish groups for selective publishing:

```php
<?php

public function boot(): void
{
    $this->publishes([
        __DIR__.'/../config/package.php' => config_path('package.php'),
    ], 'courier-config');

    $this->publishesMigrations([
        __DIR__.'/../database/migrations/' => database_path('migrations'),
    ], 'courier-migrations');
}
```

Users publish by tag:

```bash
php artisan vendor:publish --tag=courier-config
php artisan vendor:publish --tag=courier-migrations
```

Or by provider:

```bash
php artisan vendor:publish --provider="Vendor\Package\PackageServiceProvider"
```

## Best Practices

- Use `mergeConfigFrom` in `register()` for defaults, `publishes` in `boot()` for overrides
- Guard command registration with `$this->app->runningInConsole()`
- Use `publishesMigrations()` instead of `publishes()` for migrations
- Prefix translation and view namespaces with your package name
- Use `optimizes()` to hook into Laravel's deploy optimization commands
- Use `AboutCommand::add()` to expose package version and config summary
- Test your package with [Orchestral Testbench](https://github.com/orchestral/testbench)
