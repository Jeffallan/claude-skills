# Blade Templates & View Components

## Displaying Data

```php
// Basic display - automatically escaped
{{ $name }}

 // Unescaped display (careful with XSS)
{!! $htmlContent !!}

// Display with default value
{{ $name ?? 'Guest' }}

 // Calling PHP functions
{{ time() }}
{{ now()->format('Y-m-d') }}
```

```php
// Blade and JavaScript frameworks
// Use @ to prevent Blade from processing curly braces
<h1>Laravel</h1>
Hello, @{{ name }}.

 // Escape Blade directives
@@if()

// Render JSON for JavaScript
<script>
    var app = {{ Js::from($array) }};
</script>

// Use @verbatim for large blocks
@verbatim
    <div class="container">
        Hello, {{ name }}.
    </div>
@endverbatim
```

## Blade Directives

### Conditionals

```php
@if (count($records) === 1)
    I have one record!
@elseif (count($records) > 1)
    I have multiple records!
@else
    No records found
@endif

@unless (Auth::check())
    You are not signed in.
@endunless

@isset($records)
    $records is defined and not null
@endisset

@empty($records)
    $records is empty
@endempty
```

```php
// Authentication directives
@auth
    User is authenticated
@endauth

@guest
    User is a guest
@endguest

// With guard
@auth('admin')
    Admin authenticated
@endauth

@guest('admin')
    Admin guest
@endguest
```

```php
// Environment directives
@production
    Production content
@endproduction

@env('local')
    Local environment
@endenv

@env(['staging', 'production'])
    Staging or production
@endenv
```

```php
// Session and context directives
@session('status')
    <div class="alert">{{ $value }}</div>
@endsession

@context('canonical')
    <link href="{{ $value }}" rel="canonical">
@endcontext
```

### Loops

```php
@for ($i = 0; $i < 10; $i++)
    Current value: {{ $i }}
@endfor

@foreach ($users as $user)
    <p>User: {{ $user->name }}</p>
@endforeach

@forelse($users as $user)
    <li>{{ $user->name }}</li>
@empty
    <p>No users found</p>
@endforelse

@while (true)
    <p>Looping forever</p>
@endwhile
```

```php
// Loop variable
@foreach ($users as $user)
    @if ($loop->first) First item @endif
    @if ($loop->last) Last item @endif
    Index: {{ $loop->index }}
    Iteration: {{ $loop->iteration }}
    Remaining: {{ $loop->remaining }}
    Count: {{ $loop->count }}
    Even: {{ $loop->even }}
    Odd: {{ $loop->odd }}
    Depth: {{ $loop->depth }}
@endforeach

// Nested loops - access parent
@foreach ($users as $user)
    @foreach ($user->posts as $post)
        @if ($loop->parent->first)
            First post of first user
        @endif
    @endforeach
@endforeach
```

```php
// Continue and break
@foreach ($users as $user)
    @continue($user->type == 1)
    @break($user->number == 5)
    <li>{{ $user->name }}</li>
@endforeach
```

### Switch Statements

```php
@switch($i)
    @case(1)
        First case
        @break
    @case(2)
        Second case
        @break
    @default
        Default case
@endswitch
```

## Component Directives

```php
// Conditional classes
<span @class([
    'p-4',
    'font-bold' => $isActive,
    'text-gray-500' => !$isActive,
    'bg-red-500' => $hasError,
])></span>

// Conditional styles
<span @style([
    'background-color: red',
    'font-weight: bold' => $isImportant,
])></span>

// Form helpers
<input type="checkbox" @checked(old('active', $user->active)) />

<select name="version">
    @foreach($versions as $version)
        <option value="{{ $version }}" @selected(old('version') == $version)>
            {{ $version }}
        </option>
    @endforeach
</select>

<button @disabled($errors->isNotEmpty())>Submit</button>
<input @readonly(!$isEditable) />
<input @required($isRequired) />
```

## Including Subviews

```php
@include('shared.errors')

@include('view.name', ['status' => 'complete'])

@includeIf('view.name')
@includeWhen($boolean, 'view.name')
@includeUnless($boolean, 'view.name')
@includeFirst(['custom.admin', 'admin'])

// Render collection
@each('partials.item', $items, 'item', 'partials.empty')

// Isolated - no parent variables
@includeIsolated('view.name', ['user' => $user])
```

## Raw PHP

```php
@php
    $counter = 1;
@endphp

@use('App\Models\Flight')
@use('App\Models\Flight', 'FlightModel')
@use('App\Models\{Flight, Airport}')

// Import functions and constants
@use(function App\Helpers\format_currency)
@use(const App\Constants\MAX_ATTEMPTS)
@use(function App\Helpers\format_currency, 'formatMoney')

// Comments
{{-- This comment will not be in rendered HTML --}}
```

## Stacks

```php
// Push to stack
@push('scripts')
    <script src="/js/app.js"></script>
@endpush

@prepend('scripts')
    <script src="/vendor.js"></script>
@endprepend

// Render stack
@stack('scripts')

// Render once (useful in loops)
@once
    @push('scripts')
        <script>console.log('loaded');</script>
    @endpush
@endonce

@pushOnce('scripts', 'unique-id')
    <script src="/js/chart.js"></script>
@endPushOnce
```

## Blade Components

### Creating Components

```bash
php artisan make:component Alert
php artisan make:component Forms/Input
php artisan make:component Alert --inline
```

### Component Class

```php
namespace App\View\Components;

use Illuminate\View\Component;
use Illuminate\View\View;

class Alert extends Component
{
    public function __construct(
        public string $type = 'info',
        public string $message = '',
    ) {}

    public function render(): View
    {
        return view('components.alert');
    }

    public function shouldRender(): bool
    {
        return Str::length($this->message) > 0;
    }
}
```

### Component View

```php
{{-- resources/views/components/alert.blade.php --}}
@props(['type' => 'info', 'message' => ''])

<div class="alert alert-{{ $type }}" {{ $attributes }}>
    {{ $message }}
    {{ $slot }}
</div>
```

### Using Components

```php
<x-alert type="error" :message="$errorMsg" class="mb-4" />

<x-alert type="success">
    Operation completed successfully!
</x-alert>

// Nested components
<x-card>
    <x-card.header>Title</x-card.header>
    <x-card.body>Content</x-card.body>
</x-card>
```

## Component Data Binding

```php
// Short attribute syntax
<x-profile :$userId :$name />

// Equivalent to
<x-profile :user-id="$userId" :name="$name" />

// Component methods accessible in view
public function isSelected(string $option): bool
{
    return $option === $this->selected;
}

// In view
<option {{ $isSelected($value) ? 'selected' : '' }}>
    {{ $label }}
</option>

// Accessing parent data
{{ $attributes->get('class') }}
{{ $attributes->has('disabled') }}
```

## Component Attributes

```php
// Merge attributes with defaults
<div {{ $attributes->merge(['class' => 'bg-white p-4']) }}>
    {{ $slot }}
</div>

// Conditional merge
<div {{ $attributes->class(['hidden' => $isHidden]) }}>
    {{ $slot }}
</div>

// Override specific attribute
{{ $attributes->except(['method']) }}
{{ $attributes->only(['class', 'id']) }}
```

## Slots

```php
// resources/views/components/modal.blade.php
<div class="modal">
    <div class="modal-header">
        {{ $title }}
    </div>
    <div class="modal-body">
        {{ $slot }}
    </div>
    @isset($footer)
        <div class="modal-footer">
            {{ $footer }}
        </div>
    @endisset
</div>

// Usage
<x-modal>
    <x-slot name="title">Confirm Action</x-slot>
    Are you sure?
    <x-slot name="footer">
        <button>Cancel</button>
    </x-slot>
</x-modal>
```

## Anonymous Components

```php
// File: resources/views/components/alert.blade.php
@props(['type' => 'info'])

<div class="alert alert-{{ $type }}">
    {{ $slot }}
</div>

// Usage - no class needed
<x-alert type="error">Error message</x-alert>
```

## Dynamic Components

```php
<x-dynamic-component :component="$componentName" />

// Or using component method
@component($componentName, ['title' => 'Hello'])
    Content
@endcomponent
```

## View Composers

```php
// Register in AppServiceProvider
use Illuminate\Support\Facades\View;

public function boot(): void
{
    // Class-based composer
    View::composer('profile', ProfileComposer::class);

    // Closure-based composer
    View::composer('dashboard', function (View $view) {
        $view->with('stats', getStats());
    });

    // Multiple views
    View::composer(['profile', 'dashboard'], MultiComposer::class);

    // Wildcard - all views
    View::composer('*', function (View $view) {
        $view->with('appName', config('app.name'));
    });
}
```

```php
// Composer class
namespace App\View\Composers;

use App\Repositories\UserRepository;
use Illuminate\View\View;

class ProfileComposer
{
    public function __construct(
        protected UserRepository $users,
    ) {}

    public function compose(View $view): void
    {
        $view->with('count', $this->users->count());
    }
}
```

## View Creators

```php
// Similar to composers but runs immediately on instantiation
View::creator('profile', ProfileCreator::class);

class ProfileCreator
{
    public function create(View $view): void
    {
        $view->with('quickStats', cache()->remember('stats', 60, function () {
            return ['users' => User::count()];
        }));
    }
}
```

## Sharing Data With All Views

```php
// In AppServiceProvider
public function boot(): void
{
    View::share('siteName', config('app.name'));
    View::share('categories', Category::all());
}
```

## Service Injection

```php
@inject('stats', 'App\Services\StatsService')

{{ $stats->getTotal() }}
```

## Extending Blade

```php
// Custom if statements
use Illuminate\Support\Facades\Blade;

public function boot(): void
{
    Blade::if('env', function ($environment) {
        return app()->environment($environment);
    });
}

@env('local')
    Local
@endenv
```

```php
// Custom echo handlers
Blade::stringable(function ($value) {
    return str($value)->upper();
});

{{ $name }} // Outputs uppercase
```

## Building Layouts

### Using Components

```php
{{-- layouts/app.blade.php --}}
<!DOCTYPE html>
<html>
<head>
    <title>{{ $title ?? 'Default' }}</title>
    {{ $scripts }}
</head>
<body>
    {{ $slot }}
</body>
</html>

{{-- Usage --}}
<x-layout>
    <x-slot name="title">Page Title</x-slot>
    <p>Content here</p>
</x-layout>
```

### Using Template Inheritance

```php
{{-- layouts/app.blade.php --}}
<html>
<body>
    @yield('content')
</body>
</html>

{{-- child.blade.php --}}
@extends('layouts.app')

@section('content')
    <p>My content</p>
@endsection
```

## View Optimization

```bash
# Precompile all views
php artisan view:cache

# Clear view cache
php artisan view:clear
```

## Best Practices

1. **Use components over includes** - Better data binding and reusability
2. **Leverage short attribute syntax** - Cleaner component usage
3. **Use anonymous components** - For simple UI elements without logic
4. **Prefer slots over passing data** - More flexible content
5. **Use View Composers** - Centralize shared view data
6. **Cache compiled views in production** - Use `view:cache`
7. **Avoid complex logic in views** - Move to controllers or services
8. **Use @class and @style** - Clean conditional styling
9. **Use eager loading** - Prevent N+1 in views with relationships
10. **Leverage service injection** - Keep views clean of business logic