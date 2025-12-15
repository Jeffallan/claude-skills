# Laravel Specialist

Senior Laravel specialist with deep expertise in Laravel 10+, Eloquent ORM, and modern PHP 8.2+ development patterns.

## Overview

The Laravel Specialist skill provides comprehensive guidance for building elegant, scalable Laravel applications with focus on:

- **Eloquent ORM** - Models, relationships, query optimization
- **API Development** - RESTful APIs, resources, authentication
- **Queue Systems** - Jobs, workers, Horizon, background processing
- **Livewire** - Reactive components, real-time UI
- **Testing** - Feature tests, unit tests, Pest PHP, factories

## When to Use

Invoke this skill when you need:

- Building Laravel 10+ applications
- Implementing Eloquent models with complex relationships
- Creating RESTful APIs with API resources
- Setting up queue systems for background processing
- Building reactive interfaces with Livewire
- Implementing authentication with Sanctum
- Optimizing database queries and performance
- Writing comprehensive tests (>85% coverage)

## Skill Structure

### Core File
- `SKILL.md` - Main skill definition with routing table

### Reference Files

| File | Purpose | Load When |
|------|---------|-----------|
| `eloquent.md` | Eloquent ORM patterns | Working with models, relationships, scopes, query optimization |
| `routing.md` | Routes & API resources | Setting up routes, controllers, middleware, API resources |
| `queues.md` | Queue system | Working with jobs, workers, Horizon, background tasks |
| `livewire.md` | Livewire components | Building reactive interfaces, forms, real-time features |
| `testing.md` | Testing strategies | Writing tests, factories, mocking, achieving coverage |

## Quick Start Examples

### Creating an Eloquent Model

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Post extends Model
{
    protected $fillable = ['title', 'slug', 'content', 'published_at'];

    protected $casts = [
        'published_at' => 'datetime',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }

    public function scopePublished($query)
    {
        return $query->whereNotNull('published_at');
    }
}
```

### Building an API Resource

```php
namespace App\Http\Resources;

use Illuminate\Http\Resources\Json\JsonResource;

class PostResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'content' => $this->content,
            'published_at' => $this->published_at?->toISOString(),
            'author' => new UserResource($this->whenLoaded('user')),
        ];
    }
}
```

### Creating a Queue Job

```php
namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;

class ProcessPost implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public Post $post
    ) {}

    public function handle(): void
    {
        // Process the post
    }
}
```

### Building a Livewire Component

```php
namespace App\Http\Livewire;

use Livewire\Component;
use Livewire\WithPagination;

class PostList extends Component
{
    use WithPagination;

    public string $search = '';

    public function render()
    {
        return view('livewire.post-list', [
            'posts' => Post::where('title', 'like', "%{$this->search}%")
                ->paginate(10)
        ]);
    }
}
```

## Key Principles

### Must Do
- Use PHP 8.2+ features (readonly, enums, typed properties)
- Type hint all method parameters and return types
- Use Eloquent relationships properly (avoid N+1)
- Implement API resources for transforming data
- Queue long-running tasks
- Write comprehensive tests (>85% coverage)
- Use service containers and dependency injection
- Follow PSR-12 coding standards

### Must Not Do
- Use raw queries without protection (SQL injection)
- Skip eager loading (causes N+1 problems)
- Store sensitive data unencrypted
- Mix business logic in controllers
- Hardcode configuration values
- Skip validation on user input
- Use deprecated Laravel features
- Ignore queue failures

## Reference Loading

The skill uses selective disclosure architecture. Load specific references as needed:

```
User asks about Eloquent relationships
→ Load references/eloquent.md

User needs API endpoint help
→ Load references/routing.md

User wants to queue a job
→ Load references/queues.md

User building reactive UI
→ Load references/livewire.md

User writing tests
→ Load references/testing.md
```

## Related Skills

- **Fullstack Guardian** - Full-stack Laravel features
- **Test Master** - Comprehensive testing strategies
- **DevOps Engineer** - Laravel deployment and CI/CD
- **Security Reviewer** - Laravel security audits

## Framework Version

This skill targets:
- Laravel 10.x / 11.x
- PHP 8.2+
- Livewire 3.x
- Pest 2.x / PHPUnit 10.x

## Performance Goals

- Test coverage: >85%
- API response time: <200ms
- Queue throughput: >1000 jobs/min
- Database queries: N+1 eliminated
- Memory usage: Optimized with chunking/lazy loading

## License

Part of the claude-skills project.
