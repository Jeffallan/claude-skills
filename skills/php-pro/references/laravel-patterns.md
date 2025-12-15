# Laravel Patterns

> Reference for: PHP Pro
> Load when: Laravel development, repositories, services, resources, jobs

## Service Layer Pattern

```php
<?php

declare(strict_types=1);

namespace App\Services;

use App\DTOs\CreateUserData;
use App\Models\User;
use App\Repositories\UserRepositoryInterface;
use Illuminate\Support\Facades\Hash;

final readonly class UserService
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private EmailService $emailService,
    ) {}

    public function createUser(CreateUserData $data): User
    {
        $user = $this->userRepository->create([
            'name' => $data->name,
            'email' => $data->email,
            'password' => Hash::make($data->password),
        ]);

        $this->emailService->sendWelcomeEmail($user);

        return $user;
    }

    public function suspendUser(int $userId, string $reason): void
    {
        $user = $this->userRepository->findOrFail($userId);

        $this->userRepository->update($user->id, [
            'status' => UserStatus::SUSPENDED,
            'suspension_reason' => $reason,
            'suspended_at' => now(),
        ]);

        $this->emailService->sendSuspensionNotice($user, $reason);
    }
}
```

## Repository Pattern

```php
<?php

declare(strict_types=1);

namespace App\Repositories;

use App\Models\User;
use Illuminate\Database\Eloquent\Collection;

interface UserRepositoryInterface
{
    public function findOrFail(int $id): User;
    public function findByEmail(string $email): ?User;
    public function create(array $data): User;
    public function update(int $id, array $data): User;
    public function delete(int $id): void;
    public function getActive(): Collection;
}

final class UserRepository implements UserRepositoryInterface
{
    public function findOrFail(int $id): User
    {
        return User::findOrFail($id);
    }

    public function findByEmail(string $email): ?User
    {
        return User::where('email', $email)->first();
    }

    public function create(array $data): User
    {
        return User::create($data);
    }

    public function update(int $id, array $data): User
    {
        $user = $this->findOrFail($id);
        $user->update($data);
        return $user->fresh();
    }

    public function delete(int $id): void
    {
        $this->findOrFail($id)->delete();
    }

    public function getActive(): Collection
    {
        return User::where('status', UserStatus::ACTIVE)
            ->orderBy('created_at', 'desc')
            ->get();
    }
}
```

## Form Requests with Enums

```php
<?php

declare(strict_types=1);

namespace App\Http\Requests;

use App\Enums\UserRole;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;
use Illuminate\Validation\Rules\Password;

final class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()?->can('create', User::class) ?? false;
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'email', 'unique:users,email'],
            'password' => ['required', Password::min(8)->mixedCase()->numbers()],
            'role' => ['required', new Enum(UserRole::class)],
            'settings' => ['sometimes', 'array'],
            'settings.theme' => ['string', Rule::in(['light', 'dark'])],
        ];
    }

    public function toDto(): CreateUserData
    {
        return new CreateUserData(
            name: $this->validated('name'),
            email: $this->validated('email'),
            password: $this->validated('password'),
            role: UserRole::from($this->validated('role')),
        );
    }
}
```

## API Resources

```php
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\User
 */
final class UserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'status' => $this->status->value,
            'role' => $this->role->value,
            'created_at' => $this->created_at->toIso8601String(),

            // Conditional relationships
            'posts' => PostResource::collection($this->whenLoaded('posts')),
            'profile' => new ProfileResource($this->whenLoaded('profile')),

            // Conditional attributes
            'is_admin' => $this->when($this->role === UserRole::ADMIN, true),

            // Pivot data
            'team_role' => $this->whenPivotLoaded('team_user', fn() =>
                $this->pivot->role
            ),
        ];
    }
}

final class UserCollection extends ResourceCollection
{
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
            'meta' => [
                'total' => $this->total(),
                'per_page' => $this->perPage(),
            ],
        ];
    }
}
```

## Controllers with DTOs

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\CreateUserRequest;
use App\Http\Resources\UserResource;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

final class UserController extends Controller
{
    public function __construct(
        private readonly UserService $userService,
    ) {}

    public function index(): AnonymousResourceCollection
    {
        $users = User::with('profile')
            ->where('status', UserStatus::ACTIVE)
            ->paginate(20);

        return UserResource::collection($users);
    }

    public function store(CreateUserRequest $request): JsonResponse
    {
        $user = $this->userService->createUser($request->toDto());

        return (new UserResource($user))
            ->response()
            ->setStatusCode(201);
    }

    public function show(User $user): UserResource
    {
        $user->load(['posts', 'profile']);
        return new UserResource($user);
    }

    public function destroy(User $user): JsonResponse
    {
        $this->authorize('delete', $user);

        $this->userService->deleteUser($user->id);

        return response()->json(null, 204);
    }
}
```

## Jobs & Queues

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\User;
use App\Services\EmailService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

final class SendWelcomeEmail implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $timeout = 30;

    public function __construct(
        private readonly int $userId,
    ) {}

    public function handle(EmailService $emailService): void
    {
        $user = User::findOrFail($this->userId);
        $emailService->sendWelcomeEmail($user);
    }

    public function failed(\Throwable $exception): void
    {
        \Log::error('Failed to send welcome email', [
            'user_id' => $this->userId,
            'error' => $exception->getMessage(),
        ]);
    }
}

// Dispatching jobs
SendWelcomeEmail::dispatch($user->id);
SendWelcomeEmail::dispatch($user->id)->delay(now()->addMinutes(5));
SendWelcomeEmail::dispatch($user->id)->onQueue('emails');
```

## Event Listeners

```php
<?php

declare(strict_types=1);

namespace App\Events;

use App\Models\User;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

final readonly class UserRegistered
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public User $user,
    ) {}
}

namespace App\Listeners;

use App\Events\UserRegistered;
use App\Jobs\SendWelcomeEmail;
use Illuminate\Contracts\Queue\ShouldQueue;

final class SendWelcomeNotification implements ShouldQueue
{
    public function handle(UserRegistered $event): void
    {
        SendWelcomeEmail::dispatch($event->user->id);
    }
}

// In EventServiceProvider
protected $listen = [
    UserRegistered::class => [
        SendWelcomeNotification::class,
        UpdateUserStatistics::class,
    ],
];
```

## Quick Reference

| Pattern | Purpose | File Location |
|---------|---------|---------------|
| Service | Business logic | `app/Services/` |
| Repository | Data access | `app/Repositories/` |
| Form Request | Validation | `app/Http/Requests/` |
| Resource | API responses | `app/Http/Resources/` |
| Job | Async tasks | `app/Jobs/` |
| Event | Domain events | `app/Events/` |
| DTO | Data transfer | `app/DTOs/` |
| Policy | Authorization | `app/Policies/` |
