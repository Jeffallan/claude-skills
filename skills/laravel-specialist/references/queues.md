# Queue System

## Job Patterns

```php
namespace App\Jobs;

use App\Models\Post;
use App\Models\User;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ProcessPost implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 3;
    public $timeout = 120;
    public $maxExceptions = 3;
    public $backoff = [60, 120, 300]; // Exponential backoff

    public function __construct(
        public Post $post,
        public ?User $user = null,
    ) {}

    public function handle(): void
    {
        // Process the post
        $this->post->update(['processed' => true]);

        // Can access injected dependencies
        $analytics = app(AnalyticsService::class);
        $analytics->trackPostProcessed($this->post);
    }

    public function failed(\Throwable $exception): void
    {
        // Handle job failure
        \Log::error('Post processing failed', [
            'post_id' => $this->post->id,
            'error' => $exception->getMessage(),
        ]);
    }
}
```

## Dispatching Jobs

```php
use App\Jobs\ProcessPost;

// Dispatch immediately
ProcessPost::dispatch($post);

// Dispatch to specific queue
ProcessPost::dispatch($post)->onQueue('processing');

// Delayed dispatch
ProcessPost::dispatch($post)->delay(now()->addMinutes(10));

// Dispatch after database commit
ProcessPost::dispatch($post)->afterCommit();

// Dispatch conditionally
ProcessPost::dispatchIf($condition, $post);
ProcessPost::dispatchUnless($condition, $post);

// Synchronous dispatch (no queue)
ProcessPost::dispatchSync($post);

// Dispatch after response
ProcessPost::dispatchAfterResponse($post);
```

## Job Chaining

```php
use App\Jobs\{OptimizeImage, GenerateThumbnail, PublishPost};

// Chain jobs
OptimizeImage::withChain([
    new GenerateThumbnail($post),
    new PublishPost($post),
])->dispatch($post);

// Catch failures in chain
Bus::chain([
    new ProcessPost($post),
    new NotifyUser($user),
])->catch(function (\Throwable $e) {
    // Handle failure
})->dispatch();
```

## Job Batching

```php
use Illuminate\Bus\Batch;
use Illuminate\Support\Facades\Bus;

$batch = Bus::batch([
    new ProcessPost($post1),
    new ProcessPost($post2),
    new ProcessPost($post3),
])->then(function (Batch $batch) {
    // All jobs completed successfully
})->catch(function (Batch $batch, \Throwable $e) {
    // First batch job failure detected
})->finally(function (Batch $batch) {
    // The batch has finished executing
})->name('Process Posts')
->allowFailures()
->dispatch();

// Check batch status
$batch = Bus::findBatch($batchId);
if ($batch->finished()) {
    // Batch is complete
}
if ($batch->cancelled()) {
    // Batch was cancelled
}

// Add jobs to existing batch
$batch->add([
    new ProcessPost($post4),
]);
```

## Rate Limiting

```php
use Illuminate\Support\Facades\Redis;

class ProcessPost implements ShouldQueue
{
    public function handle(): void
    {
        Redis::throttle('process-posts')
            ->block(0)
            ->allow(10)
            ->every(60)
            ->then(function () {
                // Lock acquired, process job
            }, function () {
                // Could not acquire lock, release job back
                $this->release(10);
            });
    }
}

// Or using middleware
use Illuminate\Queue\Middleware\RateLimited;

public function middleware(): array
{
    return [new RateLimited('process-posts')];
}
```

## Job Middleware

```php
namespace App\Jobs\Middleware;

class RateLimitedByUser
{
    public function handle($job, $next): void
    {
        Redis::throttle("user:{$job->user->id}")
            ->allow(10)
            ->every(60)
            ->then(function () use ($job, $next) {
                $next($job);
            }, function () use ($job) {
                $job->release(10);
            });
    }
}

// Use in job
use App\Jobs\Middleware\RateLimitedByUser;

public function middleware(): array
{
    return [new RateLimitedByUser];
}

// Skip middleware
use Illuminate\Queue\Middleware\WithoutOverlapping;

public function middleware(): array
{
    return [
        (new WithoutOverlapping($this->user->id))->expireAfter(180),
    ];
}
```

## Unique Jobs

```php
use Illuminate\Contracts\Queue\ShouldBeUnique;

class ProcessPost implements ShouldQueue, ShouldBeUnique
{
    public int $uniqueFor = 3600;

    public function __construct(
        public Post $post,
    ) {}

    public function uniqueId(): string
    {
        return $this->post->id;
    }
}

// Or use unique until processing
use Illuminate\Contracts\Queue\ShouldBeUniqueUntilProcessing;

class ProcessPost implements ShouldQueue, ShouldBeUniqueUntilProcessing
{
    // ...
}
```

## Failed Jobs

```php
// Retry failed job
php artisan queue:retry <job-id>

// Retry all failed jobs
php artisan queue:retry all

// Flush failed jobs
php artisan queue:flush

// Prune failed jobs
php artisan queue:prune-failed --hours=48

// Handle in code
use Illuminate\Support\Facades\Queue;

Queue::failing(function (JobFailed $event) {
    \Log::error('Job failed', [
        'connection' => $event->connectionName,
        'queue' => $event->job->getQueue(),
        'exception' => $event->exception->getMessage(),
    ]);
});
```

## Queue Workers

```bash
# Start worker
php artisan queue:work

# Process specific queue
php artisan queue:work --queue=high,default

# Process one job
php artisan queue:work --once

# Stop worker gracefully
php artisan queue:restart

# Timeout settings
php artisan queue:work --timeout=60

# Memory limit
php artisan queue:work --memory=512

# Max jobs before restart
php artisan queue:work --max-jobs=1000

# Max time before restart
php artisan queue:work --max-time=3600
```

## Horizon Setup

```php
// config/horizon.php
return [
    'environments' => [
        'production' => [
            'supervisor-1' => [
                'connection' => 'redis',
                'queue' => ['default'],
                'balance' => 'auto',
                'maxProcesses' => 10,
                'maxTime' => 0,
                'maxJobs' => 0,
                'memory' => 512,
                'tries' => 3,
                'timeout' => 60,
                'nice' => 0,
            ],
            'supervisor-2' => [
                'connection' => 'redis',
                'queue' => ['high', 'default'],
                'balance' => 'auto',
                'maxProcesses' => 5,
                'tries' => 3,
            ],
        ],
    ],
];

// Start Horizon
php artisan horizon

// Terminate Horizon
php artisan horizon:terminate

// Pause workers
php artisan horizon:pause

// Continue workers
php artisan horizon:continue

// Check status
php artisan horizon:status
```

## Monitoring

```php
use Illuminate\Queue\Events\JobProcessed;
use Illuminate\Queue\Events\JobFailed;
use Illuminate\Support\Facades\Queue;

// In AppServiceProvider
public function boot(): void
{
    Queue::before(function (JobProcessing $event) {
        // Called before job is processed
    });

    Queue::after(function (JobProcessed $event) {
        // Called after job is processed
        \Log::info('Job processed', [
            'job' => $event->job->resolveName(),
            'time' => $event->job->processingTime(),
        ]);
    });

    Queue::failing(function (JobFailed $event) {
        // Called when job fails
        \Log::error('Job failed', [
            'job' => $event->job->resolveName(),
            'exception' => $event->exception,
        ]);
    });
}
```

## Queue Configuration

```php
// config/queue.php
return [
    'default' => env('QUEUE_CONNECTION', 'sync'),

    'connections' => [
        'sync' => [
            'driver' => 'sync',
        ],

        'database' => [
            'driver' => 'database',
            'table' => 'jobs',
            'queue' => 'default',
            'retry_after' => 90,
            'after_commit' => false,
        ],

        'redis' => [
            'driver' => 'redis',
            'connection' => 'default',
            'queue' => env('REDIS_QUEUE', 'default'),
            'retry_after' => 90,
            'block_for' => null,
            'after_commit' => false,
        ],

        'sqs' => [
            'driver' => 'sqs',
            'key' => env('AWS_ACCESS_KEY_ID'),
            'secret' => env('AWS_SECRET_ACCESS_KEY'),
            'prefix' => env('SQS_PREFIX'),
            'queue' => env('SQS_QUEUE'),
            'region' => env('AWS_DEFAULT_REGION'),
        ],
    ],

    'failed' => [
        'driver' => env('QUEUE_FAILED_DRIVER', 'database-uuids'),
        'database' => env('DB_CONNECTION', 'mysql'),
        'table' => 'failed_jobs',
    ],
];
```

## Best Practices

1. **Keep jobs small and focused** - Single responsibility
2. **Make jobs idempotent** - Safe to run multiple times
3. **Use type hints** - Better error detection
4. **Set reasonable timeouts** - Prevent hanging jobs
5. **Monitor failed jobs** - Set up alerts
6. **Use batching for bulk operations** - Better performance
7. **Implement proper error handling** - Use failed() method
8. **Use unique jobs** - Prevent duplicate processing
9. **Queue long-running tasks** - Don't block requests
10. **Use Horizon for Redis queues** - Better monitoring
