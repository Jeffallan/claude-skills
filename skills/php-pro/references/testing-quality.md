# Testing & Quality Assurance

> Reference for: PHP Pro
> Load when: PHPUnit, testing, PHPStan, Psalm, code quality, mocking

## PHPUnit with Strict Types

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Service;

use App\Repository\UserRepositoryInterface;
use App\Service\UserService;
use App\Service\EmailService;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\MockObject\MockObject;

final class UserServiceTest extends TestCase
{
    private UserRepositoryInterface&MockObject $userRepository;
    private EmailService&MockObject $emailService;
    private UserService $userService;

    protected function setUp(): void
    {
        $this->userRepository = $this->createMock(UserRepositoryInterface::class);
        $this->emailService = $this->createMock(EmailService::class);
        $this->userService = new UserService(
            $this->userRepository,
            $this->emailService
        );
    }

    public function testCreateUserSuccessfully(): void
    {
        $email = 'test@example.com';
        $password = 'SecurePass123!';

        $this->userRepository
            ->expects($this->once())
            ->method('findByEmail')
            ->with($email)
            ->willReturn(null);

        $this->userRepository
            ->expects($this->once())
            ->method('create')
            ->willReturn($this->createUser($email));

        $this->emailService
            ->expects($this->once())
            ->method('sendWelcomeEmail');

        $user = $this->userService->createUser($email, $password);

        $this->assertSame($email, $user->email);
    }

    public function testCreateUserThrowsExceptionWhenEmailExists(): void
    {
        $this->expectException(\DomainException::class);
        $this->expectExceptionMessage('Email already exists');

        $this->userRepository
            ->method('findByEmail')
            ->willReturn($this->createUser('test@example.com'));

        $this->userService->createUser('test@example.com', 'password');
    }

    private function createUser(string $email): User
    {
        return new User(
            id: 1,
            email: $email,
            password: password_hash('password', PASSWORD_ARGON2ID),
        );
    }
}
```

## Data Providers

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Validator;

use App\Validator\EmailValidator;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Test;
use PHPUnit\Framework\TestCase;

final class EmailValidatorTest extends TestCase
{
    #[Test]
    #[DataProvider('validEmailProvider')]
    public function itValidatesCorrectEmails(string $email): void
    {
        $validator = new EmailValidator();
        $this->assertTrue($validator->isValid($email));
    }

    #[Test]
    #[DataProvider('invalidEmailProvider')]
    public function itRejectsInvalidEmails(string $email): void
    {
        $validator = new EmailValidator();
        $this->assertFalse($validator->isValid($email));
    }

    public static function validEmailProvider(): array
    {
        return [
            ['user@example.com'],
            ['john.doe@company.co.uk'],
            ['test+filter@domain.org'],
        ];
    }

    public static function invalidEmailProvider(): array
    {
        return [
            ['invalid'],
            ['@example.com'],
            ['user@'],
            ['user space@example.com'],
        ];
    }
}
```

## Laravel Feature Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithFaker;
use Tests\TestCase;

final class UserControllerTest extends TestCase
{
    use RefreshDatabase, WithFaker;

    public function testUserCanViewTheirProfile(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->get('/api/users/me');

        $response->assertOk()
            ->assertJson([
                'data' => [
                    'id' => $user->id,
                    'email' => $user->email,
                ],
            ]);
    }

    public function testUserCanUpdateTheirProfile(): void
    {
        $user = User::factory()->create();
        $newName = $this->faker->name();

        $response = $this->actingAs($user)->putJson('/api/users/me', [
            'name' => $newName,
        ]);

        $response->assertOk();

        $this->assertDatabaseHas('users', [
            'id' => $user->id,
            'name' => $newName,
        ]);
    }

    public function testUnauthorizedUserCannotAccessProfile(): void
    {
        $response = $this->getJson('/api/users/me');

        $response->assertUnauthorized();
    }

    public function testValidationFailsWithInvalidData(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->putJson('/api/users/me', [
            'email' => 'not-an-email',
        ]);

        $response->assertUnprocessable()
            ->assertJsonValidationErrors(['email']);
    }
}
```

## Pest Testing (Modern Alternative)

```php
<?php

declare(strict_types=1);

use App\Models\User;
use App\Services\UserService;

beforeEach(function () {
    $this->userService = app(UserService::class);
});

it('creates a user successfully', function () {
    $user = $this->userService->createUser(
        email: 'test@example.com',
        password: 'SecurePass123!'
    );

    expect($user)
        ->toBeInstanceOf(User::class)
        ->email->toBe('test@example.com');
});

it('validates email format', function (string $email, bool $valid) {
    $validator = new EmailValidator();

    expect($validator->isValid($email))->toBe($valid);
})->with([
    ['test@example.com', true],
    ['invalid', false],
    ['@example.com', false],
]);

test('authenticated user can view profile', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->get('/api/users/me')
        ->assertOk()
        ->assertJson(['data' => ['email' => $user->email]]);
});

test('guest cannot access protected routes', function () {
    $this->getJson('/api/users/me')
        ->assertUnauthorized();
});
```

## PHPStan Configuration

```neon
# phpstan.neon
parameters:
    level: 9
    paths:
        - src
        - tests
    excludePaths:
        - src/bootstrap.php
        - vendor
    checkMissingIterableValueType: true
    checkGenericClassInNonGenericObjectType: true
    reportUnmatchedIgnoredErrors: true
    tmpDir: var/cache/phpstan

    ignoreErrors:
        # Ignore specific Laravel magic
        - '#Call to an undefined method Illuminate\\Database\\Eloquent\\Builder#'

    type_coverage:
        return_type: 100
        param_type: 100
        property_type: 100

includes:
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon
```

## PHPStan Annotations

```php
<?php

declare(strict_types=1);

namespace App\Repository;

use App\Entity\User;
use Doctrine\ORM\EntityRepository;

/**
 * @extends EntityRepository<User>
 */
final class UserRepository extends EntityRepository
{
    /**
     * @return User[]
     */
    public function findActive(): array
    {
        return $this->createQueryBuilder('u')
            ->where('u.status = :status')
            ->setParameter('status', 'active')
            ->getQuery()
            ->getResult();
    }

    /**
     * @param int[] $ids
     * @return User[]
     */
    public function findByIds(array $ids): array
    {
        return $this->createQueryBuilder('u')
            ->where('u.id IN (:ids)')
            ->setParameter('ids', $ids)
            ->getQuery()
            ->getResult();
    }
}

/**
 * @template T
 */
final readonly class Result
{
    /**
     * @param T $data
     */
    public function __construct(
        public mixed $data,
        public bool $success,
    ) {}

    /**
     * @return T
     */
    public function getData(): mixed
    {
        return $this->data;
    }
}
```

## Mockery (Advanced Mocking)

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Service;

use App\Repository\UserRepository;
use App\Service\NotificationService;
use Mockery;
use Mockery\Adapter\Phpunit\MockeryPHPUnitIntegration;
use PHPUnit\Framework\TestCase;

final class NotificationServiceTest extends TestCase
{
    use MockeryPHPUnitIntegration;

    public function testSendsNotificationToActiveUsers(): void
    {
        $repository = Mockery::mock(UserRepository::class);
        $repository->shouldReceive('findActive')
            ->once()
            ->andReturn([
                $this->createUser('user1@example.com'),
                $this->createUser('user2@example.com'),
            ]);

        $service = new NotificationService($repository);
        $result = $service->notifyActiveUsers('Important message');

        $this->assertSame(2, $result->count());
    }

    public function testHandlesEmailServiceFailure(): void
    {
        $emailService = Mockery::mock(EmailService::class);
        $emailService->shouldReceive('send')
            ->once()
            ->andThrow(new \RuntimeException('Email service down'));

        $service = new NotificationService($emailService);

        $this->expectException(\RuntimeException::class);
        $service->sendNotification('test@example.com', 'Hello');
    }

    private function createUser(string $email): User
    {
        return new User(id: 1, email: $email, password: 'hashed');
    }
}
```

## Code Coverage

```xml
<!-- phpunit.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true"
         failOnRisky="true"
         failOnWarning="true"
         stopOnFailure="false">
    <testsuites>
        <testsuite name="Unit">
            <directory>tests/Unit</directory>
        </testsuite>
        <testsuite name="Feature">
            <directory>tests/Feature</directory>
        </testsuite>
    </testsuites>
    <coverage>
        <include>
            <directory suffix=".php">src</directory>
        </include>
        <exclude>
            <directory>src/bootstrap</directory>
            <file>src/Kernel.php</file>
        </exclude>
        <report>
            <html outputDirectory="coverage/html"/>
            <clover outputFile="coverage/clover.xml"/>
        </report>
    </coverage>
    <php>
        <env name="APP_ENV" value="testing"/>
        <env name="DB_CONNECTION" value="sqlite"/>
        <env name="DB_DATABASE" value=":memory:"/>
    </php>
</phpunit>
```

## Quick Reference

| Tool | Purpose | Command |
|------|---------|---------|
| PHPUnit | Unit/Feature tests | `./vendor/bin/phpunit` |
| Pest | Modern testing | `./vendor/bin/pest` |
| PHPStan | Static analysis | `./vendor/bin/phpstan analyse` |
| Psalm | Alternative static analysis | `./vendor/bin/psalm` |
| PHP-CS-Fixer | Code style | `./vendor/bin/php-cs-fixer fix` |
| PHPMD | Mess detector | `./vendor/bin/phpmd src text cleancode` |

| Assertion | PHPUnit | Pest |
|-----------|---------|------|
| Equality | `$this->assertSame()` | `expect()->toBe()` |
| Type | `$this->assertInstanceOf()` | `expect()->toBeInstanceOf()` |
| Array | `$this->assertContains()` | `expect()->toContain()` |
| Exception | `$this->expectException()` | `expect()->toThrow()` |
| Count | `$this->assertCount()` | `expect()->toHaveCount()` |
