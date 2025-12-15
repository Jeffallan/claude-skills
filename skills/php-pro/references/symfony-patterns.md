# Symfony Patterns

> Reference for: PHP Pro
> Load when: Symfony development, dependency injection, events, commands

## Dependency Injection

```php
<?php

declare(strict_types=1);

namespace App\Service;

use App\Repository\UserRepositoryInterface;
use Psr\Log\LoggerInterface;
use Symfony\Component\Mailer\MailerInterface;

final readonly class UserService
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private MailerInterface $mailer,
        private LoggerInterface $logger,
    ) {}

    public function createUser(string $email, string $password): User
    {
        $user = new User($email, password_hash($password, PASSWORD_ARGON2ID));

        $this->userRepository->save($user);
        $this->logger->info('User created', ['email' => $email]);

        return $user;
    }
}
```

## Service Configuration (services.yaml)

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true
        bind:
            string $projectDir: '%kernel.project_dir%'
            bool $isDebug: '%kernel.debug%'

    App\:
        resource: '../src/'
        exclude:
            - '../src/DependencyInjection/'
            - '../src/Entity/'
            - '../src/Kernel.php'

    # Interface binding
    App\Repository\UserRepositoryInterface:
        class: App\Repository\DoctrineUserRepository

    # Service with specific configuration
    App\Service\PaymentService:
        arguments:
            $apiKey: '%env(PAYMENT_API_KEY)%'
            $timeout: 30

    # Tagged services
    App\EventSubscriber\:
        resource: '../src/EventSubscriber/'
        tags: ['kernel.event_subscriber']
```

## Controllers with Attributes

```php
<?php

declare(strict_types=1);

namespace App\Controller;

use App\DTO\CreateUserRequest;
use App\Entity\User;
use App\Service\UserService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Attribute\MapRequestPayload;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\IsGranted;

#[Route('/api/users', name: 'api_users_')]
final class UserController extends AbstractController
{
    public function __construct(
        private readonly UserService $userService,
    ) {}

    #[Route('', name: 'list', methods: ['GET'])]
    #[IsGranted('ROLE_USER')]
    public function list(): JsonResponse
    {
        $users = $this->userService->getAllUsers();

        return $this->json($users, Response::HTTP_OK, [], [
            'groups' => ['user:read'],
        ]);
    }

    #[Route('', name: 'create', methods: ['POST'])]
    #[IsGranted('ROLE_ADMIN')]
    public function create(
        #[MapRequestPayload] CreateUserRequest $request
    ): JsonResponse {
        $user = $this->userService->createUser(
            $request->email,
            $request->password
        );

        return $this->json($user, Response::HTTP_CREATED, [], [
            'groups' => ['user:read'],
        ]);
    }

    #[Route('/{id}', name: 'show', methods: ['GET'])]
    public function show(User $user): JsonResponse
    {
        $this->denyAccessUnlessGranted('view', $user);

        return $this->json($user, context: ['groups' => ['user:detail']]);
    }
}
```

## DTOs with Validation

```php
<?php

declare(strict_types=1);

namespace App\DTO;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class CreateUserRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Email]
        public string $email,

        #[Assert\NotBlank]
        #[Assert\Length(min: 8, max: 100)]
        #[Assert\PasswordStrength(minScore: Assert\PasswordStrength::STRENGTH_MEDIUM)]
        public string $password,

        #[Assert\NotBlank]
        #[Assert\Length(min: 2, max: 100)]
        public string $name,

        #[Assert\Choice(choices: ['admin', 'user', 'moderator'])]
        public string $role = 'user',
    ) {}
}

final readonly class UpdateUserRequest
{
    public function __construct(
        #[Assert\Email]
        public ?string $email = null,

        #[Assert\Length(min: 2, max: 100)]
        public ?string $name = null,

        #[Assert\Type('bool')]
        public ?bool $isActive = null,
    ) {}
}
```

## Event Subscribers

```php
<?php

declare(strict_types=1);

namespace App\EventSubscriber;

use App\Event\UserRegisteredEvent;
use Psr\Log\LoggerInterface;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\Mailer\MailerInterface;

final readonly class UserSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private MailerInterface $mailer,
        private LoggerInterface $logger,
    ) {}

    public static function getSubscribedEvents(): array
    {
        return [
            UserRegisteredEvent::class => [
                ['sendWelcomeEmail', 10],
                ['logRegistration', 5],
            ],
        ];
    }

    public function sendWelcomeEmail(UserRegisteredEvent $event): void
    {
        $user = $event->getUser();
        // Send email logic
        $this->logger->info('Welcome email sent', ['user_id' => $user->getId()]);
    }

    public function logRegistration(UserRegisteredEvent $event): void
    {
        $this->logger->info('User registered', [
            'user_id' => $event->getUser()->getId(),
            'email' => $event->getUser()->getEmail(),
        ]);
    }
}
```

## Custom Events

```php
<?php

declare(strict_types=1);

namespace App\Event;

use App\Entity\User;
use Symfony\Contracts\EventDispatcher\Event;

final class UserRegisteredEvent extends Event
{
    public function __construct(
        private readonly User $user,
        private readonly \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}

    public function getUser(): User
    {
        return $this->user;
    }

    public function getOccurredAt(): \DateTimeImmutable
    {
        return $this->occurredAt;
    }
}

// Dispatching events
use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

final readonly class UserService
{
    public function __construct(
        private EventDispatcherInterface $eventDispatcher,
    ) {}

    public function registerUser(string $email, string $password): User
    {
        $user = new User($email, $password);
        // ... save user

        $this->eventDispatcher->dispatch(new UserRegisteredEvent($user));

        return $user;
    }
}
```

## Console Commands

```php
<?php

declare(strict_types=1);

namespace App\Command;

use App\Service\UserService;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Style\SymfonyStyle;

#[AsCommand(
    name: 'app:user:create',
    description: 'Create a new user',
)]
final class CreateUserCommand extends Command
{
    public function __construct(
        private readonly UserService $userService,
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this
            ->addArgument('email', InputArgument::REQUIRED, 'User email')
            ->addArgument('password', InputArgument::REQUIRED, 'User password')
            ->addOption('admin', 'a', InputOption::VALUE_NONE, 'Make user admin');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $io = new SymfonyStyle($input, $output);

        $email = $input->getArgument('email');
        $password = $input->getArgument('password');
        $isAdmin = $input->getOption('admin');

        try {
            $user = $this->userService->createUser($email, $password, $isAdmin);

            $io->success(sprintf('User created with ID: %d', $user->getId()));

            return Command::SUCCESS;
        } catch (\Exception $e) {
            $io->error($e->getMessage());
            return Command::FAILURE;
        }
    }
}
```

## Voters (Authorization)

```php
<?php

declare(strict_types=1);

namespace App\Security\Voter;

use App\Entity\Post;
use App\Entity\User;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

final class PostVoter extends Voter
{
    public const VIEW = 'view';
    public const EDIT = 'edit';
    public const DELETE = 'delete';

    protected function supports(string $attribute, mixed $subject): bool
    {
        return in_array($attribute, [self::VIEW, self::EDIT, self::DELETE])
            && $subject instanceof Post;
    }

    protected function voteOnAttribute(
        string $attribute,
        mixed $subject,
        TokenInterface $token
    ): bool {
        $user = $token->getUser();

        if (!$user instanceof User) {
            return false;
        }

        /** @var Post $post */
        $post = $subject;

        return match ($attribute) {
            self::VIEW => $this->canView($post, $user),
            self::EDIT => $this->canEdit($post, $user),
            self::DELETE => $this->canDelete($post, $user),
            default => false,
        };
    }

    private function canView(Post $post, User $user): bool
    {
        return $post->isPublished() || $this->isOwner($post, $user);
    }

    private function canEdit(Post $post, User $user): bool
    {
        return $this->isOwner($post, $user);
    }

    private function canDelete(Post $post, User $user): bool
    {
        return $this->isOwner($post, $user) || $user->hasRole('ROLE_ADMIN');
    }

    private function isOwner(Post $post, User $user): bool
    {
        return $post->getAuthor()->getId() === $user->getId();
    }
}
```

## Message Handler (Messenger)

```php
<?php

declare(strict_types=1);

namespace App\Message;

final readonly class SendWelcomeEmail
{
    public function __construct(
        public int $userId,
    ) {}
}

namespace App\MessageHandler;

use App\Message\SendWelcomeEmail;
use App\Repository\UserRepositoryInterface;
use Symfony\Component\Mailer\MailerInterface;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
final readonly class SendWelcomeEmailHandler
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private MailerInterface $mailer,
    ) {}

    public function __invoke(SendWelcomeEmail $message): void
    {
        $user = $this->userRepository->find($message->userId);

        if (!$user) {
            return;
        }

        // Send email logic
    }
}

// Dispatching messages
use Symfony\Component\Messenger\MessageBusInterface;

$this->messageBus->dispatch(new SendWelcomeEmail($user->getId()));
```

## Quick Reference

| Component | Purpose | File Location |
|-----------|---------|---------------|
| Controller | HTTP handlers | `src/Controller/` |
| Service | Business logic | `src/Service/` |
| Repository | Data access | `src/Repository/` |
| Event | Domain events | `src/Event/` |
| EventSubscriber | Event handlers | `src/EventSubscriber/` |
| Command | CLI commands | `src/Command/` |
| Voter | Authorization | `src/Security/Voter/` |
| Message | Async messages | `src/Message/` |
| MessageHandler | Message handlers | `src/MessageHandler/` |
| DTO | Data transfer | `src/DTO/` |
