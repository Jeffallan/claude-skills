# Routing & API Resources

## Route Patterns

```php
// routes/web.php
use App\Http\Controllers\PostController;
use Illuminate\Support\Facades\Route;

// Resource routes
Route::resource('posts', PostController::class);

// API resource (excludes create/edit)
Route::apiResource('posts', PostController::class);

// Partial resource
Route::resource('posts', PostController::class)->only(['index', 'show']);
Route::resource('posts', PostController::class)->except(['destroy']);

// Nested resources
Route::resource('posts.comments', CommentController::class);

// Route groups
Route::prefix('admin')->middleware('auth')->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index']);
    Route::resource('users', UserController::class);
});

// Named routes
Route::get('/posts/{post}', [PostController::class, 'show'])->name('posts.show');

// Route model binding
Route::get('/posts/{post:slug}', [PostController::class, 'show']);

// Multiple bindings
Route::get('/users/{user}/posts/{post:slug}', function (User $user, Post $post) {
    return view('posts.show', compact('user', 'post'));
});
```

## API Routes

```php
// routes/api.php
use App\Http\Controllers\Api\V1\PostController;

Route::prefix('v1')->group(function () {
    // Public routes
    Route::get('/posts', [PostController::class, 'index']);
    Route::get('/posts/{post}', [PostController::class, 'show']);

    // Protected routes
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('/posts', [PostController::class, 'store']);
        Route::put('/posts/{post}', [PostController::class, 'update']);
        Route::delete('/posts/{post}', [PostController::class, 'destroy']);
    });
});

// Rate limiting
Route::middleware('throttle:60,1')->group(function () {
    Route::apiResource('posts', PostController::class);
});
```

## Controllers

```php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StorePostRequest;
use App\Http\Requests\UpdatePostRequest;
use App\Http\Resources\PostResource;
use App\Http\Resources\PostCollection;
use App\Models\Post;
use Illuminate\Http\Response;

class PostController extends Controller
{
    public function index()
    {
        $posts = Post::with('user')
            ->published()
            ->paginate(15);

        return new PostCollection($posts);
    }

    public function store(StorePostRequest $request)
    {
        $post = Post::create($request->validated());

        return new PostResource($post);
    }

    public function show(Post $post)
    {
        $post->load(['user', 'comments.user']);

        return new PostResource($post);
    }

    public function update(UpdatePostRequest $request, Post $post)
    {
        $post->update($request->validated());

        return new PostResource($post);
    }

    public function destroy(Post $post)
    {
        $post->delete();

        return response()->noContent();
    }
}
```

## Form Requests

```php
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StorePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // Or check user permissions
    }

    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'slug' => ['required', 'string', 'unique:posts,slug'],
            'content' => ['required', 'string'],
            'category_id' => ['required', 'exists:categories,id'],
            'tags' => ['array'],
            'tags.*' => ['exists:tags,id'],
            'published_at' => ['nullable', 'date', 'after:now'],
        ];
    }

    public function messages(): array
    {
        return [
            'title.required' => 'Please provide a post title',
            'slug.unique' => 'This slug is already taken',
        ];
    }

    // Prepare data before validation
    protected function prepareForValidation(): void
    {
        $this->merge([
            'slug' => str($this->title)->slug(),
        ]);
    }
}

class UpdatePostRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'title' => ['sometimes', 'string', 'max:255'],
            'slug' => [
                'sometimes',
                'string',
                Rule::unique('posts', 'slug')->ignore($this->post)
            ],
            'content' => ['sometimes', 'string'],
        ];
    }
}
```

## API Resources

```php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class PostResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'slug' => $this->slug,
            'excerpt' => $this->excerpt,
            'content' => $this->when($request->route()->named('posts.show'), $this->content),
            'published_at' => $this->published_at?->toISOString(),
            'created_at' => $this->created_at->toISOString(),

            // Relationships
            'author' => new UserResource($this->whenLoaded('user')),
            'comments' => CommentResource::collection($this->whenLoaded('comments')),
            'comments_count' => $this->when($this->comments_count !== null, $this->comments_count),

            // Conditional fields
            'is_published' => $this->when($request->user()?->isAdmin(), $this->isPublished()),

            // Pivot data
            'role' => $this->whenPivotLoaded('role_user', function () {
                return $this->pivot->role_name;
            }),

            // Links
            'links' => [
                'self' => route('api.posts.show', $this->id),
            ],
        ];
    }

    public function with(Request $request): array
    {
        return [
            'meta' => [
                'version' => '1.0.0',
            ],
        ];
    }
}
```

## Resource Collections

```php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\ResourceCollection;

class PostCollection extends ResourceCollection
{
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
            'meta' => [
                'total' => $this->total(),
                'current_page' => $this->currentPage(),
                'last_page' => $this->lastPage(),
            ],
            'links' => [
                'self' => $request->url(),
            ],
        ];
    }
}

// Or use anonymous collection
return PostResource::collection($posts);
```

## Middleware

```php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class EnsureUserIsAdmin
{
    public function handle(Request $request, Closure $next)
    {
        if (!$request->user()?->isAdmin()) {
            abort(403, 'Unauthorized action.');
        }

        return $next($request);
    }
}

// Register in app/Http/Kernel.php
protected $middlewareAliases = [
    'admin' => \App\Http\Middleware\EnsureUserIsAdmin::class,
];

// Use in routes
Route::middleware('admin')->group(function () {
    Route::resource('users', UserController::class);
});
```

## Response Helpers

```php
// JSON responses
return response()->json(['data' => $posts], 200);

// Created response
return response()->json($post, 201);

// No content
return response()->noContent();

// Custom headers
return response()->json($data)->header('X-Custom-Header', 'Value');

// Download
return response()->download($pathToFile);

// Stream
return response()->streamDownload(function () {
    echo 'CSV content...';
}, 'export.csv');
```

## Route Caching

```bash
# Generate route cache
php artisan route:cache

# Clear route cache
php artisan route:clear

# List all routes
php artisan route:list

# Filter routes
php artisan route:list --name=api
php artisan route:list --path=posts
```

## API Versioning

```php
// routes/api.php
Route::prefix('v1')->name('v1.')->group(function () {
    Route::apiResource('posts', \App\Http\Controllers\Api\V1\PostController::class);
});

Route::prefix('v2')->name('v2.')->group(function () {
    Route::apiResource('posts', \App\Http\Controllers\Api\V2\PostController::class);
});
```

## CORS Configuration

```php
// config/cors.php
return [
    'paths' => ['api/*', 'sanctum/csrf-cookie'],
    'allowed_methods' => ['*'],
    'allowed_origins' => ['http://localhost:3000'],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => true,
];
```
