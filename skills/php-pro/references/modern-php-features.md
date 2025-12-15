# Modern PHP 8.3+ Features

> Reference for: PHP Pro
> Load when: Using PHP 8.3 features, strict typing, enums, readonly, attributes

## Strict Types & Type Declarations

```php
<?php

declare(strict_types=1);

namespace App\Domain\User;

final readonly class User
{
    public function __construct(
        public int $id,
        public string $email,
        public UserStatus $status,
        public \DateTimeImmutable $createdAt,
    ) {}
}

function calculateTotal(int $price, float $taxRate): float
{
    return $price * (1 + $taxRate);
}

// Union types
function processId(int|string $id): string
{
    return is_int($id) ? (string)$id : $id;
}

// Intersection types
interface Timestamped {}
interface Authenticatable {}

function handleUser(Timestamped&Authenticatable $user): void {}
```

## Enums with Methods

```php
<?php

declare(strict_types=1);

enum UserStatus: string
{
    case ACTIVE = 'active';
    case SUSPENDED = 'suspended';
    case DELETED = 'deleted';

    public function label(): string
    {
        return match($this) {
            self::ACTIVE => 'Active User',
            self::SUSPENDED => 'Suspended',
            self::DELETED => 'Deleted User',
        };
    }

    public function canLogin(): bool
    {
        return $this === self::ACTIVE;
    }

    public static function fromString(string $value): self
    {
        return self::from(strtolower($value));
    }
}

enum HttpStatus: int
{
    case OK = 200;
    case CREATED = 201;
    case BAD_REQUEST = 400;
    case UNAUTHORIZED = 401;
    case NOT_FOUND = 404;
    case SERVER_ERROR = 500;

    public function isSuccess(): bool
    {
        return $this->value >= 200 && $this->value < 300;
    }
}
```

## Readonly Properties & Classes

```php
<?php

declare(strict_types=1);

// Readonly class (PHP 8.2+)
final readonly class Money
{
    public function __construct(
        public int $amount,
        public string $currency,
    ) {
        if ($amount < 0) {
            throw new \InvalidArgumentException('Amount cannot be negative');
        }
    }

    public function add(Money $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new \InvalidArgumentException('Currency mismatch');
        }
        return new self($this->amount + $other->amount, $this->currency);
    }
}

// Individual readonly properties
class Configuration
{
    public function __construct(
        public readonly string $apiKey,
        public readonly string $apiSecret,
        private string $cache = '',
    ) {}
}
```

## Attributes (Metadata)

```php
<?php

declare(strict_types=1);

#[\Attribute(\Attribute::TARGET_CLASS)]
final readonly class Route
{
    public function __construct(
        public string $path,
        public string $method = 'GET',
        public array $middleware = [],
    ) {}
}

#[\Attribute(\Attribute::TARGET_PROPERTY)]
final readonly class Validate
{
    public function __construct(
        public ?string $rule = null,
        public ?int $min = null,
        public ?int $max = null,
    ) {}
}

// Using attributes
#[Route('/api/users', method: 'POST', middleware: ['auth'])]
final class CreateUserController
{
    public function __invoke(CreateUserRequest $request): JsonResponse
    {
        // ...
    }
}

class UserDto
{
    #[Validate(rule: 'email')]
    public string $email;

    #[Validate(min: 8, max: 100)]
    public string $password;
}
```

## First-Class Callables

```php
<?php

declare(strict_types=1);

class UserService
{
    public function findById(int $id): ?User {}
    public function create(array $data): User {}
}

$service = new UserService();

// PHP 8.1+ first-class callable syntax
$finder = $service->findById(...);
$user = $finder(42);

// Array operations
$numbers = [1, 2, 3, 4, 5];
$doubled = array_map(fn($n) => $n * 2, $numbers);

// Named arguments with callable
$result = array_filter(
    array: $numbers,
    callback: fn($n) => $n % 2 === 0,
);
```

## Match Expressions

```php
<?php

declare(strict_types=1);

function getStatusColor(UserStatus $status): string
{
    return match ($status) {
        UserStatus::ACTIVE => 'green',
        UserStatus::SUSPENDED => 'yellow',
        UserStatus::DELETED => 'red',
    };
}

function calculateShipping(int $weight, string $zone): float
{
    return match (true) {
        $weight < 1000 => 5.00,
        $weight < 5000 && $zone === 'local' => 10.00,
        $weight < 5000 => 15.00,
        default => 25.00,
    };
}

// Match with multiple conditions
function getHttpMessage(int $code): string
{
    return match ($code) {
        200, 201, 204 => 'Success',
        400, 422 => 'Client Error',
        401, 403 => 'Unauthorized',
        500, 502, 503 => 'Server Error',
        default => 'Unknown',
    };
}
```

## Fibers (PHP 8.1+)

```php
<?php

declare(strict_types=1);

// Basic fiber example
$fiber = new \Fiber(function (): void {
    $value = \Fiber::suspend('fiber started');
    echo "Received: {$value}\n";
    \Fiber::suspend('second suspend');
    echo "Fiber completed\n";
});

$result1 = $fiber->start();
echo "First result: {$result1}\n";

$result2 = $fiber->resume('data from main');
echo "Second result: {$result2}\n";

$fiber->resume('final data');

// Async-style with fibers
function async(callable $callback): \Fiber
{
    return new \Fiber($callback);
}

function await(\Fiber $fiber): mixed
{
    if (!$fiber->isStarted()) {
        return $fiber->start();
    }
    return $fiber->resume();
}
```

## Never Type

```php
<?php

declare(strict_types=1);

function redirect(string $url): never
{
    header("Location: {$url}");
    exit;
}

function abort(int $code, string $message): never
{
    http_response_code($code);
    echo json_encode(['error' => $message]);
    exit;
}

class NotFoundException extends \Exception
{
    public static function throw(string $resource): never
    {
        throw new self("Resource not found: {$resource}");
    }
}
```

## Quick Reference

| Feature | PHP Version | Usage |
|---------|-------------|-------|
| Readonly properties | 8.1+ | `public readonly string $name` |
| Readonly classes | 8.2+ | `readonly class User {}` |
| Enums | 8.1+ | `enum Status: string {}` |
| First-class callables | 8.1+ | `$fn = $obj->method(...)` |
| Never type | 8.1+ | `function exit(): never` |
| Fibers | 8.1+ | `new \Fiber(fn() => ...)` |
| Pure intersection types | 8.1+ | `A&B $param` |
| DNF types | 8.2+ | `(A&B)|C $param` |
| Constants in traits | 8.2+ | `trait T { const X = 1; }` |
