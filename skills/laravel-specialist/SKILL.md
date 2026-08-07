---
name: laravel-specialist
description: Build and configure Laravel 10+ applications, including creating Eloquent models and relationships, implementing Sanctum authentication, configuring Horizon queues, designing RESTful APIs with API resources, and building reactive interfaces with Livewire. Use when creating Laravel models, setting up queue workers, implementing Sanctum auth flows, building Livewire components, optimising Eloquent queries, or writing Pest/PHPUnit tests for Laravel features.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.2.0"
  domain: backend
  triggers: Laravel, Eloquent, PHP framework, Laravel API, Artisan, Blade templates, Laravel queues, Livewire, Laravel testing, Sanctum, Horizon
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, test-master, devops-engineer, security-reviewer
---

# Laravel Specialist

Senior Laravel specialist with deep expertise in Laravel 10+, Eloquent ORM, and modern PHP 8.2+.

## Core Workflow

1. **Analyse** — Identify models, relationships, APIs, queue needs
2. **Design** — Plan schema, service layers, job queues
3. **Implement** — Create models, migrations; verify with `php artisan migrate:status`
4. **Build** — Controllers, services, API resources, jobs; verify with `php artisan route:list`
5. **Test** — Write tests; run `php artisan test` (>85% coverage target)

## Reference Guide

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Eloquent ORM | `references/eloquent.md` | Models, relationships, scopes, queries |
| Routing & APIs | `references/routing.md` | Routes, controllers, middleware, resources |
| Queue System | `references/queues.md` | Jobs, workers, Horizon, batching |
| Livewire | `references/livewire.md` | Components, wire:model, real-time |
| Testing | `references/testing.md` | Feature tests, factories, Pest PHP |
| Blade & Views | `references/view-components.md` | Blade templates, components, slots |
| Events | `references/events.md` | Events, listeners, subscribers |
| Sanctum / Auth | `references/sanctum.md` | API tokens, SPA auth, abilities |
| Validation | `references/validation.md` | Form requests, rules, custom validation |
| Authorization | `references/authorization.md` | Gates, policies, `@can` |
| Notifications | `references/notifications.md` | Mail, database, broadcast, Slack |
| Broadcasting | `references/broadcasting.md` | WebSockets, Echo, Reverb, Pusher |
| Service Container | `references/container.md` | Bindings, resolution, `#[Singleton]` |
| Artisan Console | `references/artisan.md` | Custom commands, scheduling |
| Collections | `references/collections.md` | `collect()`, filtering, lazy collections |
| Helpers | `references/helpers.md` | `Arr`, `Str`, `Number`, URLs |

## Constraints

### MUST DO
- PHP 8.2+ features (readonly, enums, typed properties)
- Type hint all parameters and return types
- Eager-load relationships (avoid N+1)
- API resources for data transformation
- Queue long-running tasks
- Tests >85% coverage, PSR-12 standards
- Use service containers and DI

### MUST NOT DO
- Raw queries without protection (SQL injection)
- Skip eager loading (N+1 problems)
- Store sensitive data unencrypted
- Mix business logic in controllers
- Hardcode configuration values
- Skip validation on user input
- Use deprecated Laravel features

## Code Templates

### Eloquent Model

```php
final class Post extends Model
{
    use HasFactory, SoftDeletes;
    protected $fillable = ['title', 'body', 'status', 'user_id'];
    protected $casts = ['status' => PostStatus::class, 'published_at' => 'immutable_datetime'];
    public function author(): BelongsTo { return $this->belongsTo(User::class); }
    public function comments(): HasMany { return $this->hasMany(Comment::class); }
    public function scopePublished(Builder $query): Builder { return $query->where('status', PostStatus::Published); }
}
```

### API Resource

```php
final class PostResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return ['id' => $this->id, 'title' => $this->title, 'body' => $this->body,
            'status' => $this->status->value, 'published_at' => $this->published_at?->toIso8601String(),
            'author' => new UserResource($this->whenLoaded('author'))];
    }
}
```

### Queued Job

```php
final class PublishPost implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;
    public int $tries = 3;
    public function __construct(private readonly Post $post) {}
    public function handle(): void { $this->post->update(['status' => PostStatus::Published, 'published_at' => now()]); }
    public function failed(\Throwable $e): void { logger()->error('PublishPost failed', ['error' => $e->getMessage()]); }
}
```

### Feature Test (Pest)

```php
it('returns a published post', function (): void {
    $user = User::factory()->create();
    $post = Post::factory()->published()->for($user, 'author')->create();
    $this->actingAs($user)->getJson("/api/posts/{$post->id}")
        ->assertOk()->assertJsonPath('data.status', 'published');
});
```

## Validation Checkpoints

| Stage | Command | Expected |
|-------|---------|----------|
| Migration | `php artisan migrate:status` | All `Ran` |
| Routing | `php artisan route:list --path=api` | Routes with correct verbs |
| Queue | `php artisan queue:work --once` | No exception |
| Test | `php artisan test --coverage` | >85%, 0 failures |
| Lint | `./vendor/bin/pint --test` | PSR-12 passes |

## Knowledge Reference

Laravel 10+, Eloquent ORM, PHP 8.2+, API resources, Sanctum, queues, Horizon, Livewire, Inertia, Octane, Pest/PHPUnit, Redis, broadcasting, events, notifications, scheduling

[Documentation](https://jeffallan.github.io/claude-skills/skills/backend/laravel-specialist/)
