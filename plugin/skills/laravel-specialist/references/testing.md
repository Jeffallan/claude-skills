# Testing

## Feature Tests

```php
namespace Tests\Feature;

use Tests\TestCase;
use App\Models\{User, Post};
use Illuminate\Foundation\Testing\RefreshDatabase;

class PostTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_create_post(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'This is a test post content.',
        ]);

        $response->assertStatus(201)
            ->assertJson([
                'data' => [
                    'title' => 'Test Post',
                ],
            ]);

        $this->assertDatabaseHas('posts', [
            'title' => 'Test Post',
            'user_id' => $user->id,
        ]);
    }

    public function test_guest_cannot_create_post(): void
    {
        $response = $this->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content',
        ]);

        $response->assertStatus(401);
    }

    public function test_post_requires_valid_data(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post('/api/posts', [
            'title' => 'AB', // Too short
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['title', 'content']);
    }

    public function test_user_can_view_their_posts(): void
    {
        $user = User::factory()->create();
        $posts = Post::factory()->count(3)->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->get('/api/posts');

        $response->assertStatus(200)
            ->assertJsonCount(3, 'data')
            ->assertJsonStructure([
                'data' => [
                    '*' => ['id', 'title', 'content', 'created_at'],
                ],
            ]);
    }

    public function test_user_can_update_own_post(): void
    {
        $user = User::factory()->create();
        $post = Post::factory()->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->put("/api/posts/{$post->id}", [
            'title' => 'Updated Title',
            'content' => $post->content,
        ]);

        $response->assertStatus(200);

        $this->assertDatabaseHas('posts', [
            'id' => $post->id,
            'title' => 'Updated Title',
        ]);
    }

    public function test_user_cannot_update_others_post(): void
    {
        $user = User::factory()->create();
        $otherUser = User::factory()->create();
        $post = Post::factory()->create(['user_id' => $otherUser->id]);

        $response = $this->actingAs($user)->put("/api/posts/{$post->id}", [
            'title' => 'Updated Title',
        ]);

        $response->assertStatus(403);
    }
}
```

## Unit Tests

```php
namespace Tests\Unit;

use Tests\TestCase;
use App\Models\Post;
use App\Services\PostService;
use Illuminate\Foundation\Testing\RefreshDatabase;

class PostServiceTest extends TestCase
{
    use RefreshDatabase;

    public function test_generates_unique_slug(): void
    {
        $service = new PostService();

        $slug = $service->generateSlug('Test Post');

        $this->assertEquals('test-post', $slug);
    }

    public function test_increments_slug_on_duplicate(): void
    {
        Post::factory()->create(['slug' => 'test-post']);

        $service = new PostService();
        $slug = $service->generateSlug('Test Post');

        $this->assertEquals('test-post-1', $slug);
    }

    public function test_post_excerpt_returns_limited_content(): void
    {
        $post = new Post(['content' => str_repeat('a', 200)]);

        $excerpt = $post->excerpt;

        $this->assertLessThanOrEqual(100, strlen($excerpt));
    }
}
```

## Pest PHP

```php
<?php

use App\Models\{User, Post};

it('allows authenticated users to create posts', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content',
        ])
        ->assertStatus(201);

    expect(Post::count())->toBe(1);
});

it('prevents guests from creating posts', function () {
    $this->post('/api/posts', [
        'title' => 'Test Post',
        'content' => 'Content',
    ])->assertStatus(401);
});

test('post requires title and content', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/api/posts', [])
        ->assertJsonValidationErrors(['title', 'content']);
});

// Datasets
it('validates title length', function (string $title, bool $shouldPass) {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->post('/api/posts', [
        'title' => $title,
        'content' => 'Content',
    ]);

    if ($shouldPass) {
        $response->assertStatus(201);
    } else {
        $response->assertJsonValidationErrors(['title']);
    }
})->with([
    ['AB', false],        // Too short
    ['ABC', true],        // Minimum valid
    [str_repeat('A', 255), true],  // Maximum valid
    [str_repeat('A', 256), false], // Too long
]);

// Hooks
beforeEach(function () {
    $this->user = User::factory()->create();
});

afterEach(function () {
    // Cleanup
});
```

## Factories

```php
namespace Database\Factories;

use App\Models\{User, Category};
use Illuminate\Database\Eloquent\Factories\Factory;

class PostFactory extends Factory
{
    public function definition(): array
    {
        return [
            'title' => fake()->sentence(),
            'slug' => fake()->slug(),
            'content' => fake()->paragraphs(3, true),
            'excerpt' => fake()->text(100),
            'published_at' => fake()->dateTimeBetween('-1 year', 'now'),
            'user_id' => User::factory(),
            'category_id' => Category::factory(),
        ];
    }

    public function unpublished(): static
    {
        return $this->state(fn (array $attributes) => [
            'published_at' => null,
        ]);
    }

    public function published(): static
    {
        return $this->state(fn (array $attributes) => [
            'published_at' => now(),
        ]);
    }

    public function forUser(User $user): static
    {
        return $this->state(fn (array $attributes) => [
            'user_id' => $user->id,
        ]);
    }

    public function configure(): static
    {
        return $this->afterCreating(function (Post $post) {
            $post->tags()->attach(
                Tag::factory()->count(3)->create()
            );
        });
    }
}

// Usage
$post = Post::factory()->create();
$unpublished = Post::factory()->unpublished()->create();
$posts = Post::factory()->count(10)->create();
$userPosts = Post::factory()->forUser($user)->count(5)->create();

// With relationships
$post = Post::factory()
    ->has(Comment::factory()->count(3))
    ->create();

// For relationship
$posts = Post::factory()
    ->count(3)
    ->for($user)
    ->create();
```

## Mocking

```php
use App\Services\ExternalApiService;
use Illuminate\Support\Facades\Http;

public function test_fetches_data_from_external_api(): void
{
    Http::fake([
        'api.example.com/*' => Http::response([
            'data' => ['id' => 1, 'name' => 'Test'],
        ], 200),
    ]);

    $service = new ExternalApiService();
    $result = $service->fetchData();

    $this->assertEquals('Test', $result['name']);

    Http::assertSent(function ($request) {
        return $request->url() === 'https://api.example.com/data' &&
               $request->hasHeader('Authorization');
    });
}

// Mock events
use Illuminate\Support\Facades\Event;

Event::fake([PostCreated::class]);

// Test code that dispatches events

Event::assertDispatched(PostCreated::class, function ($event) {
    return $event->post->id === 1;
});

// Mock queues
use Illuminate\Support\Facades\Queue;

Queue::fake();

// Test code that dispatches jobs

Queue::assertPushed(ProcessPost::class);
Queue::assertPushed(ProcessPost::class, 2);
Queue::assertPushed(ProcessPost::class, function ($job) {
    return $job->post->id === 1;
});

// Mock notifications
use Illuminate\Support\Facades\Notification;

Notification::fake();

// Test code that sends notifications

Notification::assertSentTo($user, PostPublished::class);

// Mock storage
use Illuminate\Support\Facades\Storage;

Storage::fake('public');

// Test file upload

Storage::disk('public')->assertExists('file.jpg');
Storage::disk('public')->assertMissing('missing.jpg');
```

## Database Testing

```php
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\DatabaseTransactions;

class PostTest extends TestCase
{
    use RefreshDatabase; // Migrate database before each test

    // Or use transactions
    use DatabaseTransactions; // Rollback after each test

    public function test_database_assertions(): void
    {
        $post = Post::factory()->create([
            'title' => 'Test Post',
        ]);

        $this->assertDatabaseHas('posts', [
            'title' => 'Test Post',
        ]);

        $post->delete();

        $this->assertDatabaseMissing('posts', [
            'id' => $post->id,
        ]);

        $this->assertSoftDeleted('posts', [
            'id' => $post->id,
        ]);
    }

    public function test_model_exists(): void
    {
        $post = Post::factory()->create();

        $this->assertModelExists($post);

        $post->delete();

        $this->assertModelMissing($post);
    }
}
```

## API Testing

```php
public function test_api_returns_paginated_posts(): void
{
    Post::factory()->count(30)->create();

    $response = $this->get('/api/posts');

    $response->assertStatus(200)
        ->assertJsonStructure([
            'data' => [
                '*' => ['id', 'title', 'content'],
            ],
            'meta' => ['total', 'current_page', 'last_page'],
            'links' => ['first', 'last', 'prev', 'next'],
        ])
        ->assertJsonCount(15, 'data'); // Default per page
}

public function test_api_filters_posts_by_category(): void
{
    $category = Category::factory()->create();
    Post::factory()->count(5)->create(['category_id' => $category->id]);
    Post::factory()->count(5)->create();

    $response = $this->get("/api/posts?category={$category->id}");

    $response->assertJsonCount(5, 'data')
        ->assertJson([
            'data' => [
                ['category_id' => $category->id],
            ],
        ]);
}
```

## Authentication Testing

```php
use Laravel\Sanctum\Sanctum;

public function test_authenticated_user_can_access_endpoint(): void
{
    $user = User::factory()->create();

    Sanctum::actingAs($user, ['*']);

    $response = $this->get('/api/user');

    $response->assertStatus(200)
        ->assertJson([
            'data' => [
                'id' => $user->id,
                'email' => $user->email,
            ],
        ]);
}

public function test_user_with_wrong_ability_cannot_access(): void
{
    $user = User::factory()->create();

    Sanctum::actingAs($user, ['view-posts']);

    $response = $this->post('/api/posts', [
        'title' => 'Test',
        'content' => 'Content',
    ]);

    $response->assertStatus(403);
}
```

## Running Tests

```bash
# Run all tests
php artisan test

# Run specific test
php artisan test --filter=test_user_can_create_post

# Run test file
php artisan test tests/Feature/PostTest.php

# Parallel testing
php artisan test --parallel

# With coverage
php artisan test --coverage

# Coverage minimum
php artisan test --coverage --min=80

# Stop on failure
php artisan test --stop-on-failure

# Pest specific
./vendor/bin/pest
./vendor/bin/pest --filter=PostTest
./vendor/bin/pest --coverage
```

## Best Practices

1. **Use RefreshDatabase** - Clean database for each test
2. **Use factories** - Don't manually create test data
3. **Test one thing** - Each test should verify one behavior
4. **Use descriptive names** - test_user_can_create_post
5. **AAA pattern** - Arrange, Act, Assert
6. **Mock external services** - Don't make real API calls
7. **Fake queues and events** - Test async code synchronously
8. **Test edge cases** - Invalid data, permissions, etc.
9. **Achieve >85% coverage** - Test critical paths
10. **Run tests in CI/CD** - Automate test execution
