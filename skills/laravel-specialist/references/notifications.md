# Notifications

## Generating Notifications

```bash
php artisan make:notification PostPublished
```

```php
<?php

namespace App\Notifications;

use App\Models\Post;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Notification;

class PostPublished extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Post $post
    ) {}
}
```

## Sending Notifications

```php
<?php

use App\Models\User;
use App\Notifications\PostPublished;
use Illuminate\Support\Facades\Notification;

// Using the Notifiable trait
$user->notify(new PostPublished($post));

// Using the Notification facade
Notification::send($users, new PostPublished($post));

// Send immediately (not queued)
Notification::sendNow($users, new PostPublished($post));
```

## Defining Channels (via Method)

```php
<?php

namespace App\Notifications;

use App\Models\Post;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\BroadcastMessage;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class PostPublished extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Post $post
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database', 'broadcast'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $url = route('posts.show', $this->post);

        return (new MailMessage)
            ->greeting('Hello!')
            ->line('Your post has been published.')
            ->action('View Post', $url)
            ->line('Thank you for using our application!');
    }

    public function toDatabase(object $notifiable): array
    {
        return [
            'post_id' => $this->post->id,
            'post_title' => $this->post->title,
            'message' => "Your post \"{$this->post->title}\" has been published.",
        ];
    }

    public function toBroadcast(object $notifiable): BroadcastMessage
    {
        return new BroadcastMessage([
            'post_id' => $this->post->id,
            'post_title' => $this->post->title,
        ]);
    }
}
```

## Queueing Notifications

```php
<?php

namespace App\Notifications;

use App\Models\Post;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Notification;

class PostPublished extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Post $post
    ) {
        $this->delay(now()->addMinutes(5));
    }
}

// At send time
$user->notify((new PostPublished($post))->delay(now()->addMinutes(10)));

// Specify connection and queue
$user->notify((new PostPublished($post))
    ->onConnection('redis')
    ->onQueue('notifications'));
```

## On-Demand Notifications

```php
<?php

use App\Notifications\InvoicePaid;
use Illuminate\Support\Facades\Notification;

Notification::route('mail', 'guest@example.com')
    ->route('vonage', '15556667777')
    ->route('slack', '#notifications')
    ->notify(new InvoicePaid($invoice));

// Custom routing
Notification::routes(function ($notifiable) {
    $notifiable->route('mail', $this->email);
    $notifiable->route('vonage', $this->phone);
})->notify(new InvoicePaid($invoice));
```

## Mail Notifications

```php
<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class InvoicePaid extends Notification implements ShouldQueue
{
    use Queueable;

    public function via(object $notifiable): array
    {
        return ['mail'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $url = route('invoices.show', $this->invoice);

        return (new MailMessage)
            ->greeting('Hi '.$notifiable->name.',')
            ->line('Your invoice has been paid successfully.')
            ->lineIf($this->invoice->discount > 0, "You saved \${$this->invoice->discount}!")
            ->action('View Invoice', $url)
            ->line('Thank you for your business!');
    }
}
```

### MailMessage with Error Style

```php
return (new MailMessage)
    ->error()
    ->subject('Payment Failed')
    ->greeting('Oops!')
    ->line('Your payment could not be processed.')
    ->action('Try Again', $url);
```

### Markdown Mail

```php
return (new MailMessage)
    ->subject('Post Published')
    ->markdown('emails.post-published', [
        'post' => $this->post,
        'url' => $url,
    ]);
```

## Database Notifications

```bash
php artisan notifications:table
php artisan migrate
```

```php
public function via(object $notifiable): array
{
    return ['database'];
}

public function toDatabase(object $notifiable): array
{
    return [
        'post_id' => $this->post->id,
        'type' => 'post_published',
        'message' => "Your post \"{$this->post->title}\" was published.",
    ];
}
```

### Accessing Notifications

```php
<?php

use App\Models\User;

$user = User::find(1);

// All notifications
$notifications = $user->notifications;

// Unread notifications
$unread = $user->unreadNotifications;

// Marking as read
$user->unreadNotifications->markAsRead();

// Using the specific model
$notification = $user->notifications()->first();
$notification->markAsRead();

// Delete notification
$notification->delete();
```

```php
// routes/api.php
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/notifications', function (Request $request) {
        return $request->user()->notifications()->paginate(20);
    });

    Route::get('/notifications/unread', function (Request $request) {
        return $request->user()->unreadNotifications;
    });

    Route::post('/notifications/{notification}/read', function (Request $request, $notification) {
        $request->user()->notifications()
            ->where('id', $notification)
            ->firstOrFail()
            ->markAsRead();

        return response()->noContent();
    });

    Route::post('/notifications/mark-all-read', function (Request $request) {
        $request->user()->unreadNotifications->markAsRead();

        return response()->noContent();
    });
});
```

## Broadcast Notifications

```php
<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\BroadcastMessage;
use Illuminate\Notifications\Notification;

class PostPublished extends Notification implements ShouldQueue
{
    use Queueable;

    public function via(object $notifiable): array
    {
        return ['broadcast'];
    }

    public function toBroadcast(object $notifiable): BroadcastMessage
    {
        return new BroadcastMessage([
            'post_id' => $this->post->id,
            'title' => $this->post->title,
            'excerpt' => $this->post->excerpt,
        ]);
    }

    public function broadcastType(): string
    {
        return 'post.published';
    }
}
```

### Listening with Echo

```typescript
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

window.Echo = new Echo({
    broadcaster: 'pusher',
    key: import.meta.env.VITE_PUSHER_APP_KEY,
    cluster: import.meta.env.VITE_PUSHER_APP_CLUSTER,
});

window.Echo.private(`App.Models.User.${userId}`)
    .notification((notification) => {
        console.log(notification.title);
    });
```

## SMS / Vonage Notifications

```bash
composer require laravel/vonage-notification-channel
```

```php
<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\VonageMessage;
use Illuminate\Notifications\Notification;

class OrderShipped extends Notification implements ShouldQueue
{
    use Queueable;

    public function via(object $notifiable): array
    {
        return ['vonage'];
    }

    public function toVonage(object $notifiable): VonageMessage
    {
        return (new VonageMessage)
            ->content('Your order has shipped! Tracking: ABC123')
            ->from('15556667777')
            ->unicode();
    }
}
```

## Slack Notifications

```bash
composer require laravel/slack-notification-channel
```

```php
<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\SlackMessage;
use Illuminate\Notifications\Notification;

class DeploymentSucceeded extends Notification implements ShouldQueue
{
    use Queueable;

    public function via(object $notifiable): array
    {
        return ['slack'];
    }

    public function toSlack(object $notifiable): SlackMessage
    {
        return (new SlackMessage)
            ->success()
            ->content('Deployment succeeded!')
            ->attachment(function ($attachment) {
                $attachment->title('Deployment #42', 'https://deploy.example.com/42')
                    ->fields([
                        'Environment' => 'Production',
                        'Branch' => 'main',
                        'Commit' => 'a1b2c3d',
                        'Duration' => '2m 34s',
                    ]);
            });
    }
}
```

### Slack with Interactivity

```php
return (new SlackMessage)
    ->warning()
    ->content('Deployment requires approval.')
    ->attachment(function ($attachment) {
        $attachment
            ->title('Deployment #43', 'https://deploy.example.com/43')
            ->fields([
                'Environment' => 'Production',
                'Requester' => 'Jane Doe',
            ])
            ->actions([
                actionButton('Approve', 'https://deploy.example.com/43/approve'),
                actionButton('Reject', 'https://deploy.example.com/43/reject'),
            ]);
    });
```

## Custom Channels

```php
<?php

namespace App\Notifications\Channels;

use App\Models\User;
use RuntimeException;

class SmsChannel
{
    public function send(object $notifiable, Notification $notification): void
    {
        $message = $notification->toSms($notifiable);

        $phone = $notifiable->phone_number;

        if (empty($phone)) {
            throw new RuntimeException('No phone number found.');
        }

        // Send SMS via external provider
        SmsProvider::send($phone, $message);
    }
}
```

```php
<?php

namespace App\Notifications;

use App\Notifications\Channels\SmsChannel;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Notification;

class OrderConfirmed extends Notification implements ShouldQueue
{
    use Queueable;

    public function via(object $notifiable): array
    {
        return [SmsChannel::class, 'mail'];
    }

    public function toSms(object $notifiable): string
    {
        return "Order #{$this->order->id} confirmed!";
    }
}
```

## Testing

```php
<?php

namespace Tests\Feature;

use App\Models\User;
use App\Notifications\PostPublished;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Notification;
use Tests\TestCase;

class PostTest extends TestCase
{
    use RefreshDatabase;

    public function test_post_published_sends_notification(): void
    {
        Notification::fake();

        $user = User::factory()->create();
        $post = Post::factory()->create(['user_id' => $user->id]);

        $this->actingAs($user)->post("/posts/{$post->id}/publish");

        Notification::assertSentTo(
            $user,
            PostPublished::class,
            function ($notification, $channels) use ($post) {
                return $notification->post->id === $post->id;
            }
        );
    }

    public function test_notification_is_not_sent_on_draft(): void
    {
        Notification::fake();

        $user = User::factory()->create();

        $this->actingAs($user)->post('/posts', [
            'title' => 'Draft',
            'content' => 'Not published yet.',
        ]);

        Notification::assertNotSentTo($user, PostPublished::class);
    }

    public function test_notification_sent_to_specific_users(): void
    {
        Notification::fake();

        $users = User::factory()->count(3)->create();
        $post = Post::factory()->create();

        $this->actingAs($users[0])->post("/posts/{$post->id}/publish");

        Notification::assertSentTo($users[0], PostPublished::class);
        Notification::assertNotSentTo($users[1], PostPublished::class);
        Notification::assertNotSentTo($users[2], PostPublished::class);
    }

    public function test_notification_count(): void
    {
        Notification::fake();

        $users = User::factory()->count(2)->create();

        Notification::assertNothingSent();

        $this->actingAs($users[0])->post('/posts', [
            'title' => 'Test',
            'content' => 'Content',
        ]);

        Notification::assertCount(1);
    }

    public function test_on_demand_notification(): void
    {
        Notification::fake();

        Notification::route('mail', 'test@example.com')
            ->notify(new PostPublished(Post::factory()->create()));

        Notification::assertSentTo(
            Notification::route('mail', 'test@example.com'),
            PostPublished::class
        );
    }
}
```

## PHP 8 Attributes

```php
<?php

namespace App\Notifications;

use App\Models\Post;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Attributes\MaxExceptions;
use Illuminate\Notifications\Attributes\Tries;
use Illuminate\Notifications\Notification;

#[Tries(3)]
#[MaxExceptions(5)]
class PostPublished extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Post $post
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail', 'database'];
    }

    public function viaQueues(): array
    {
        return [
            'mail' => 'mail-queue',
            'database' => 'default',
        ];
    }
}

// Inline alternative
(new PostPublished($post))->tries(5);
```

## Best Practices

1. **Always implement ShouldQueue** - Keep notification sending out of the request lifecycle
2. **Use specific channels per use case** - Email for critical, database for in-app, broadcast for real-time
3. **Keep toMail/toDatabase clean** - Delegate complex view logic to Mailables or markdown templates
4. **Use on-demand for ad-hoc** - Send notifications to non-user recipients via `Notification::route()`
5. **Mark database notifications as read** - Let users see unread counts and dismiss notifications
6. **Use broadcastType()** - Define custom broadcast event types for frontend routing
7. **Avoid heavy logic in notifications** - Notifications are data carriers, not business logic containers
8. **Set queue and connection explicitly** - Route notification channels to appropriate queues
9. **Test notification assertions** - Use `Notification::fake()` and `assertSentTo` in feature tests
10. **Use `#[Tries]` / `#[MaxExceptions]`** - Configure retry behavior on queued notifications
