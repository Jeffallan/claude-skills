# Broadcasting

## Installation

```shell
# Install with Reverb (first-party WebSocket server)
php artisan install:broadcasting --reverb

# Install with Pusher Channels
php artisan install:broadcasting --pusher

# Install without a driver (for Ably or manual setup)
php artisan install:broadcasting
```

## Server-Side Drivers

### Reverb (First-Party)

```shell
composer require laravel/reverb
php artisan reverb:install
php artisan reverb:start
```

Configure in `.env`:

```
REVERB_APP_ID=my-app-id
REVERB_APP_KEY=my-app-key
REVERB_APP_SECRET=my-app-secret
REVERB_HOST="0.0.0.0"
REVERB_PORT=8080
REVERB_SCHEME=http

VITE_REVERB_APP_KEY="${REVERB_APP_KEY}"
VITE_REVERB_HOST="${REVERB_HOST}"
VITE_REVERB_PORT="${REVERB_PORT}"
VITE_REVERB_SCHEME="${REVERB_SCHEME}"
```

### Pusher Channels

```
PUSHER_APP_ID=my-app-id
PUSHER_APP_KEY=my-app-key
PUSHER_APP_SECRET=my-app-secret
PUSHER_HOST=
PUSHER_PORT=443
PUSHER_SCHEME=https
PUSHER_APP_CLUSTER=mt1

VITE_PUSHER_APP_KEY="${PUSHER_APP_KEY}"
VITE_PUSHER_APP_CLUSTER="${PUSHER_APP_CLUSTER}"
```

### Ably

```
ABLY_KEY=my-ably-key
VITE_ABLY_PUBLIC_KEY=my-ably-public-key
```

Ensure Pusher protocol support is enabled in Ably app settings.

## Client-Side Installation (Laravel Echo)

### JavaScript (Pusher Protocol)

```js
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

window.Pusher = Pusher;

window.Echo = new Echo({
    broadcaster: 'pusher',
    key: import.meta.env.VITE_PUSHER_APP_KEY,
    cluster: import.meta.env.VITE_PUSHER_APP_CLUSTER,
    forceTLS: true,
});
```

### JavaScript (Reverb)

```js
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

window.Pusher = Pusher;

window.Echo = new Echo({
    broadcaster: 'reverb',
    key: import.meta.env.VITE_REVERB_APP_KEY,
    wsHost: import.meta.env.VITE_REVERB_HOST,
    wsPort: import.meta.env.VITE_REVERB_PORT ?? 80,
    wssPort: import.meta.env.VITE_REVERB_PORT ?? 443,
    forceTLS: (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https',
    enabledTransports: ['ws', 'wss'],
});
```

### JavaScript (Ably)

```js
import Echo from 'laravel-echo';
import Pusher from 'pusher-js';

window.Pusher = Pusher;

window.Echo = new Echo({
    broadcaster: 'pusher',
    key: import.meta.env.VITE_ABLY_PUBLIC_KEY,
    wsHost: 'realtime-pusher.ably.io',
    wsPort: 443,
    disableStats: true,
    encrypted: true,
});
```

### React

```js
import { configureEcho } from "@laravel/echo-react";

configureEcho({
    broadcaster: "reverb",
    key: import.meta.env.VITE_REVERB_APP_KEY,
    wsHost: import.meta.env.VITE_REVERB_HOST,
    wsPort: import.meta.env.VITE_REVERB_PORT,
    wssPort: import.meta.env.VITE_REVERB_PORT,
    forceTLS: (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https',
    enabledTransports: ['ws', 'wss'],
});
```

### Vue

```js
import { configureEcho } from "@laravel/echo-vue";

configureEcho({
    broadcaster: "reverb",
    key: import.meta.env.VITE_REVERB_APP_KEY,
    wsHost: import.meta.env.VITE_REVERB_HOST,
    wsPort: import.meta.env.VITE_REVERB_PORT,
    wssPort: import.meta.env.VITE_REVERB_PORT,
    forceTLS: (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https',
    enabledTransports: ['ws', 'wss'],
});
```

### Svelte

```js
import { configureEcho } from "@laravel/echo-svelte";

configureEcho({
    broadcaster: "reverb",
    key: import.meta.env.VITE_REVERB_APP_KEY,
    wsHost: import.meta.env.VITE_REVERB_HOST,
    wsPort: import.meta.env.VITE_REVERB_PORT,
    wssPort: import.meta.env.VITE_REVERB_PORT,
    forceTLS: (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https',
    enabledTransports: ['ws', 'wss'],
});
```

## Defining Broadcast Events

Implement `ShouldBroadcast` on any event class:

```php
<?php

namespace App\Events;

use App\Models\Order;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Queue\SerializesModels;

class OrderShipped implements ShouldBroadcast
{
    use InteractsWithSockets, SerializesModels;

    public function __construct(
        public Order $order,
    ) {}

    public function broadcastOn(): array
    {
        return [
            new PrivateChannel('user.' . $this->order->user_id),
        ];
    }
}
```

Use `ShouldBroadcastNow` to dispatch synchronously (not queued):

```php
use Illuminate\Contracts\Broadcasting\ShouldBroadcastNow;

class OrderShipped implements ShouldBroadcastNow
{
    // ...
}
```

### Customizing the Event Name

```php
public function broadcastAs(): string
{
    return 'order.shipped';
}
```

On the client, listen with the custom name:

```js
Echo.private('user.1')
    .listen('.order.shipped', (e) => {
        console.log(e.order);
    });
```

### Customizing the Data Payload

```php
public function broadcastWith(): array
{
    return ['id' => $this->order->id, 'status' => 'shipped'];
}
```

### Conditional Broadcasting

```php
public function broadcastWhen(): bool
{
    return $this->order->status === 'shipped';
}
```

## Channel Types

```php
use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Broadcasting\PresenceChannel;

// Public — anyone can listen
new Channel('orders');

// Private — requires authorization
new PrivateChannel('user.' . $userId);

// Presence — auth + member tracking
new PresenceChannel('chat.' . $roomId);
```

## Authorizing Channels

Define authorization in `routes/channels.php`:

```php
use App\Models\Order;
use App\Models\User;

// Simple callback
Broadcast::channel('orders.{orderId}', function (User $user, int $orderId) {
    return $user->id === Order::findOrNew($orderId)->user_id;
});

// With model binding
Broadcast::channel('orders.{order}', function (User $user, Order $order) {
    return $user->id === $order->user_id;
});
```

### Channel Classes

```php
<?php

namespace App\Broadcasting;

use App\Models\Order;
use App\Models\User;

class OrderChannel
{
    public function join(User $user, Order $order): bool
    {
        return $user->id === $order->user_id;
    }
}
```

Register in `routes/channels.php`:

```php
use App\Broadcasting\OrderChannel;

Broadcast::channel('orders.{order}', OrderChannel::class);
```

## Broadcasting Events

```php
// Via the event helper
event(new OrderShipped($order));

// Via the broadcast facade
use Illuminate\Support\Facades\Broadcast;

Broadcast::event(new OrderShipped($order));

// Via the broadcast helper (returns the event for chaining)
broadcast(new OrderShipped($order));
```

### Broadcasting to Others

Exclude the current user from receiving the broadcast:

```php
broadcast(new OrderShipped($order))->toOthers();
```

The receiving client must enable the `wh-channel` header:

```js
window.Echo = new Echo({
    broadcaster: 'reverb',
    // ...
    whChannel: 'App.Models.User.' + userId,
});
```

### Anonymous Events (No Event Class)

```php
use Illuminate\Support\Facades\Broadcast;

// Public channel
Broadcast::on('orders.' . $order->id)->send();

// With custom name and data
Broadcast::on('orders.' . $order->id)
    ->as('OrderPlaced')
    ->with($order)
    ->send();

// Private channel
Broadcast::private('orders.' . $order->id)->send();

// Presence channel
Broadcast::presence('channels.' . $channel->id)->send();

// Exclude current user
Broadcast::on('orders.' . $order->id)
    ->toOthers()
    ->send();
```

## Receiving Broadcasts via Echo

### React

```jsx
import { useEcho } from "@laravel/echo-react";

function OrderStatus({ orderId }) {
    useEcho(`orders.${orderId}`, (e) => {
        console.log('Order updated:', e);
    });

    useEcho(`orders.${orderId}`, {
        onOrderShipped: (e) => console.log('Shipped:', e),
    });
}
```

### Vue

```vue
<script setup>
import { useEcho } from "@laravel/echo-vue";

useEcho(`orders.${props.orderId}`, (e) => {
    console.log('Order updated:', e);
});

useEcho(`orders.${props.orderId}`, {
    onOrderShipped: (e) => console.log('Shipped:', e),
});
</script>
```

### Svelte

```svelte
<script>
    import { useEcho } from "@laravel/echo-svelte";

    useEcho(`orders.${orderId}`, (e) => {
        console.log('Order updated:', e);
    });

    useEcho(`orders.${orderId}`, {
        onOrderShipped: (e) => console.log('Shipped:', e),
    });
</script>
```

### Vanilla JS

```js
// Private channel
Echo.private('orders.' + orderId)
    .listen('OrderShipped', (e) => {
        console.log(e.order);
    })
    .listen('.order.shipped', (e) => {
        console.log('Custom event name:', e);
    })
    .notification((notification) => {
        console.log('Broadcast notification:', notification);
    });

// Public channel
Echo.channel('orders')
    .listen('OrderCreated', (e) => {
        console.log(e.order);
    });

// Listening for a single event
Echo.private('orders.' + orderId)
    .listenOnce('OrderShipped', (e) => {
        console.log('First shipment only:', e);
    });
```

## Presence Channels

```php
<?php

namespace App\Events;

use App\Models\Message;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Broadcasting\PresenceChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;

class NewMessage implements ShouldBroadcast
{
    use InteractsWithSockets;

    public function __construct(
        public Message $message,
    ) {}

    public function broadcastOn(): array
    {
        return [
            new PresenceChannel('chat.' . $this->message->room_id),
        ];
    }
}
```

### Authorizing Presence Channels

```php
use App\Models\ChatRoom;
use App\Models\User;

Broadcast::channel('chat.{room}', function (User $user, ChatRoom $room) {
    return $room->members->contains($user)
        ? ['id' => $user->id, 'name' => $user->name, 'avatar' => $user->avatar_url]
        : false;
});
```

### Client-Side Presence

```js
Echo.join(`chat.${roomId}`)
    .here((members) => {
        console.log('Current members:', members);
    })
    .joining((member) => {
        console.log('Joined:', member);
    })
    .leaving((member) => {
        console.log('Left:', member);
    })
    .listen('NewMessage', (e) => {
        console.log('Message:', e.message);
    })
    .error((error) => {
        console.error('Presence error:', error);
    });
```

## Model Broadcasting

Use the `BroadcastsEvents` trait on an Eloquent model:

```php
<?php

namespace App\Models;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Database\Eloquent\BroadcastsEvents;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    use BroadcastsEvents, HasFactory;

    public function broadcastOn(string $event): array
    {
        return [$this, $this->user];
    }

    public function broadcastAs(string $event): string|null
    {
        return match ($event) {
            'created' => 'post.created',
            'updated' => 'post.updated',
            'deleted' => 'post.deleted',
            default => null,
        };
    }

    public function broadcastWith(string $event): array
    {
        return match ($event) {
            'created' => ['title' => $this->title],
            default => ['model' => $this],
        };
    }

    public function broadcastWhen(string $event): bool
    {
        return match ($event) {
            'deleted' => false,
            default => true,
        };
    }
}
```

Model events `created`, `updated`, `deleted`, `trashed`, and `restored` are broadcast automatically.

### Listening to Model Broadcasts

```js
Echo.private(`App.Models.User.${this.user.id}`)
    .listen('.post.created', (e) => {
        console.log('New post:', e.model);
    });

Echo.private(`App.Models.Post.${postId}`)
    .listen('.post.updated', (e) => {
        console.log('Post updated:', e.model);
    });
```

## Client Events

Broadcast directly from the client without hitting your server:

```js
Echo.private('orders.1')
    .whisper('typing', { username: user.name });

Echo.private('orders.1')
    .listenForWhisper('typing', (e) => {
        console.log(`${e.username} is typing...`);
    });
```

Enable on the server in `config/broadcasting.php`:

```php
'connections' => [
    'reverb' => [
        // ...
        'client_events' => [
            'typing',
            'cancel-typing',
        ],
    ],
],
```

## Notifications via Broadcast Channel

```php
<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Notification;

class InvoicePaid extends Notification
{
    use Queueable;

    public function __construct(
        private int $invoiceId,
    ) {}

    public function via(object $notifiable): array
    {
        return ['broadcast'];
    }

    public function toBroadcast(object $notifiable): array
    {
        return [
            'invoice_id' => $this->invoiceId,
            'amount' => 100,
        ];
    }

    public function broadcastType(): string
    {
        return 'invoice.paid';
    }
}
```

### Receiving Broadcast Notifications

```js
Echo.private('App.Models.User.' + userId)
    .notification((notification) => {
        console.log('New notification:', notification);
    });
```

## Best Practices

1. **Always use private/presence channels for user-specific data** — never send sensitive data over public channels
2. **Use `broadcastAs()` to define custom event names** — decouples client from class names
3. **Use `broadcastWith()` to control payload size** — only send what the client needs
4. **Use `toOthers()` to prevent duplicate processing** — the sender already has the state
5. **Name channels using dot notation** — `orders.{id}`, `users.{id}`, `chat.{room}`
6. **Keep model broadcasting payloads small** — avoid sending full model graphs
7. **Enable `client_events` sparingly** — validate on the server if needed
8. **Use `broadcastWhen()` to avoid unnecessary broadcasts** — especially for model events
9. **Use Echo framework packages** — `@laravel/echo-react`, `@laravel/echo-vue`, `@laravel/echo-svelte` provide lifecycle-aware hooks
10. **Use notifications for ephemeral alerts** — the broadcast channel is ideal for real-time push notifications
