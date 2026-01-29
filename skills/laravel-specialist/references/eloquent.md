# Eloquent ORM

## Model Patterns

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Database\Eloquent\Casts\Attribute;

class Post extends Model
{
    use HasFactory, SoftDeletes;

    protected $fillable = [
        'title',
        'slug',
        'content',
        'published_at',
        'user_id',
    ];

    protected $casts = [
        'published_at' => 'datetime',
        'metadata' => 'array',
        'is_featured' => 'boolean',
    ];

    // Accessor using new Attribute syntax (Laravel 9+)
    protected function title(): Attribute
    {
        return Attribute::make(
            get: fn (string $value) => ucfirst($value),
            set: fn (string $value) => strtolower($value),
        );
    }

    // Mutator for computed property
    protected function excerpt(): Attribute
    {
        return Attribute::make(
            get: fn () => str($this->content)->limit(100),
        );
    }
}
```

## Relationships

```php
// One-to-Many
class User extends Model
{
    public function posts(): HasMany
    {
        return $this->hasMany(Post::class);
    }

    public function latestPost(): HasOne
    {
        return $this->hasOne(Post::class)->latestOfMany();
    }

    public function oldestPost(): HasOne
    {
        return $this->hasOne(Post::class)->oldestOfMany();
    }
}

class Post extends Model
{
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    // Inverse relationship
    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }
}

// Many-to-Many with Pivot
class User extends Model
{
    public function roles(): BelongsToMany
    {
        return $this->belongsToMany(Role::class)
            ->withPivot('expires_at', 'assigned_by')
            ->withTimestamps()
            ->using(RoleUser::class); // Custom pivot model
    }
}

// Has Many Through
class Country extends Model
{
    public function posts(): HasManyThrough
    {
        return $this->hasManyThrough(Post::class, User::class);
    }
}

// Polymorphic Relations
class Image extends Model
{
    public function imageable(): MorphTo
    {
        return $this->morphTo();
    }
}

class Post extends Model
{
    public function images(): MorphMany
    {
        return $this->morphMany(Image::class, 'imageable');
    }
}

// Many-to-Many Polymorphic
class Tag extends Model
{
    public function posts(): MorphToMany
    {
        return $this->morphedByMany(Post::class, 'taggable');
    }

    public function videos(): MorphToMany
    {
        return $this->morphedByMany(Video::class, 'taggable');
    }
}
```

## Query Scopes

```php
class Post extends Model
{
    // Local scope
    public function scopePublished($query): void
    {
        $query->whereNotNull('published_at')
            ->where('published_at', '<=', now());
    }

    public function scopePopular($query, int $threshold = 100): void
    {
        $query->where('views', '>=', $threshold);
    }

    // Global scope
    protected static function booted(): void
    {
        static::addGlobalScope('active', function ($query) {
            $query->where('status', 'active');
        });
    }
}

// Usage
$posts = Post::published()->popular(500)->get();

// Custom Scope Class
namespace App\Models\Scopes;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Scope;

class AncientScope implements Scope
{
    public function apply(Builder $builder, Model $model): void
    {
        $builder->where('created_at', '<', now()->subYears(10));
    }
}

// Apply in model
protected static function booted(): void
{
    static::addGlobalScope(new AncientScope);
}
```

## Custom Casts

```php
namespace App\Casts;

use Illuminate\Contracts\Database\Eloquent\CastsAttributes;

class Money implements CastsAttributes
{
    public function get($model, string $key, $value, array $attributes): float
    {
        return $value / 100; // Store cents, return dollars
    }

    public function set($model, string $key, $value, array $attributes): int
    {
        return (int) ($value * 100);
    }
}

// In model
protected $casts = [
    'price' => Money::class,
];
```

## Query Optimization

```php
// Eager Loading (prevent N+1)
$posts = Post::with(['user', 'comments.user'])->get();

// Lazy Eager Loading
$posts = Post::all();
$posts->load('user');

// Eager Load with Constraints
$users = User::with(['posts' => function ($query) {
    $query->where('published', true)->orderBy('created_at', 'desc');
}])->get();

// Count relationships efficiently
$posts = Post::withCount('comments')->get();
foreach ($posts as $post) {
    echo $post->comments_count;
}

// Exists checks
$users = User::withExists('posts')->get();

// Chunk for large datasets
Post::chunk(100, function ($posts) {
    foreach ($posts as $post) {
        // Process post
    }
});

// Lazy collection for memory efficiency
Post::lazy()->each(function ($post) {
    // Process one at a time
});
```

## Model Events

```php
class Post extends Model
{
    protected static function booted(): void
    {
        static::creating(function ($post) {
            $post->slug = str($post->title)->slug();
        });

        static::updating(function ($post) {
            if ($post->isDirty('title')) {
                $post->slug = str($post->title)->slug();
            }
        });

        static::deleted(function ($post) {
            $post->images()->delete();
        });
    }
}

// Using Observers
namespace App\Observers;

class PostObserver
{
    public function creating(Post $post): void
    {
        $post->user_id = auth()->id();
    }

    public function updated(Post $post): void
    {
        cache()->forget("post.{$post->id}");
    }
}

// Register in AppServiceProvider
use App\Models\Post;
use App\Observers\PostObserver;

public function boot(): void
{
    Post::observe(PostObserver::class);
}
```

## Advanced Queries

```php
// Subqueries
$users = User::select(['id', 'name'])
    ->addSelect(['latest_post_title' => Post::select('title')
        ->whereColumn('user_id', 'users.id')
        ->latest()
        ->limit(1)
    ])->get();

// When conditional queries
$posts = Post::query()
    ->when($search, fn ($query) => $query->where('title', 'like', "%{$search}%"))
    ->when($category, fn ($query) => $query->where('category_id', $category))
    ->get();

// Database transactions
DB::transaction(function () {
    $user = User::create([...]);
    $user->profile()->create([...]);
    $user->assignRole('member');
});

// Pessimistic locking
$user = User::where('id', 1)->lockForUpdate()->first();

// Upserts
User::upsert(
    [
        ['email' => 'john@example.com', 'name' => 'John'],
        ['email' => 'jane@example.com', 'name' => 'Jane'],
    ],
    ['email'], // Unique columns
    ['name']   // Columns to update
);
```

## Performance Tips

1. **Always eager load relationships** - Avoid N+1 queries
2. **Use chunking for large datasets** - Prevent memory exhaustion
3. **Index foreign keys** - Speed up joins
4. **Use select() to limit columns** - Reduce data transfer
5. **Cache expensive queries** - Use Redis/Memcached
6. **Use database indexing** - Add indexes in migrations
7. **Avoid using model events for heavy operations** - Use queues instead
8. **Use lazy collections** - For processing large datasets
