# Artisan Console

## Tinker (REPL)

```shell
# Start an interactive PHP REPL with the application booted
php artisan tinker

> User::count()
=> 42
> User::where('email', 'john@example.com')->first()
=> App\Models\User {#...}
> $user = User::factory()->create()
=> App\Models\User {#...}
> $user->posts()->create(['title' => 'Hello'])
=> App\Models\Post {#...}
```

Configure the allow list for classes that can be instantiated in `config/tinker.php`:

```php
'alias' => [
    'User' => App\Models\User::class,
],

'dont_alias' => [
    App\Models\Payment::class,
],
```

## Writing Commands

```shell
php artisan make:command SendEmails
```

### Command Structure (PHP 8 Attributes)

```php
<?php

namespace App\Console\Commands;

use App\Models\User;
use App\Support\DripEmailer;
use Illuminate\Console\Attributes\Description;
use Illuminate\Console\Attributes\Signature;
use Illuminate\Console\Command;

#[Signature('mail:send {user}')]
#[Description('Send a marketing email to a user')]
class SendEmails extends Command
{
    public function handle(DripEmailer $drip): void
    {
        $drip->send(User::findOrFail($this->argument('user')));
    }
}
```

### Exit Codes

```php
use Illuminate\Console\Command;

class SendEmails extends Command
{
    #[Signature('mail:send {user}')]
    #[Description('Send a marketing email to a user')]
    public function handle(): int
    {
        $user = User::find($this->argument('user'));

        if (! $user) {
            $this->error('User not found');

            return Command::FAILURE;
        }

        // ...

        return Command::SUCCESS;
    }

    // Also available: Command::INVALID
}
```

### Failing Commands

```php
public function handle(): void
{
    $this->fail('Something went wrong');
    // Automatically exits with FAILURE
}
```

## Closure Commands

Define lightweight commands in `routes/console.php`:

```php
use Illuminate\Support\Facades\Artisan;

Artisan::command('mail:send {user}', function (string $user) {
    $this->info("Sending email to: {$user}!");
})->purpose('Send a marketing email to a user');
```

The closure is bound to the command instance, giving access to `$this->info()`, `$this->argument()`, etc.

### Scheduling Closure Commands

```php
Artisan::command('delete:recent-users', function () {
    DB::table('recent_users')->delete();
})->purpose('Delete recent users')->daily();
```

## Isolatable Commands

Prevent overlapping execution:

```php
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Contracts\Console\Isolatable;

class SendEmails extends Command implements Isolatable
{
    #[Signature('mail:send {user}')]
    #[Description('Send a marketing email to a user')]
    public function handle(): void
    {
        // Only one instance runs at a time
    }
}
```

No changes needed in `handle()`. The framework automatically acquires a lock.

### Custom Isolation Key

```php
public function isolatableId(): string
{
    return $this->argument('user');
}
```

### Custom Lock Expiration

```php
use Carbon\CarbonInterval;

public function isolationLockExpiresAt(): CarbonInterval
{
    return CarbonInterval::minutes(5);
}
```

### Manual Lock Bypass

```shell
php artisan mail:send 1 --isolated
php artisan mail:send 1 --no-isolated
```

## Defining Input

### Arguments

```php
// Required argument
#[Signature('mail:send {user}')]

// Optional argument
#[Signature('mail:send {user?}')]

// Default value
#[Signature('mail:send {user=foo}')]

// Array argument
#[Signature('mail:send {users*}')]
```

### Options

```php
// Switch (boolean)
#[Signature('mail:send {--queue}')]

// With value (required)
#[Signature('mail:send {--queue=}')]

// With default
#[Signature('mail:send {--queue=default}')]

// Array option
#[Signature('mail:send {--id=*}')]

// Shortcut
#[Signature('mail:send {-Q}')]
```

### Input Descriptions

```php
#[Signature('
    mail:send
    {user : The ID of the user to send to}
    {--queue : Whether the job should be queued}
')]
```

## Prompting for Missing Input

Implement `PromptsForMissingInput` to automatically prompt users for missing required arguments:

```php
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Contracts\Console\PromptsForMissingInput;

class SendEmails extends Command implements PromptsForMissingInput
{
    #[Signature('mail:send {user}')]
    #[Description('Send a marketing email to a user')]

    public function handle(): void
    {
        $user = User::findOrFail($this->argument('user'));

        // If called without user argument, prompts will ask for it
    }
}
```

## Command I/O

### Retrieving Input

```php
public function handle(): void
{
    // Arguments
    $userId = $this->argument('user');
    $allArguments = $this->arguments();

    // Options
    $shouldQueue = $this->option('queue');
    $allOptions = $this->options();

    // Check presence
    if ($this->hasArgument('user')) { /* ... */ }
    if ($this->option('queue')) { /* ... */ }

    // All arguments and options
    $input = $this->input->getArguments();
    $options = $this->input->getOptions();
}
```

### Prompting

```php
// Text input
$name = $this->ask('What is your name?');

// Secret input (hidden)
$password = $this->secret('What is the password?');

// Confirmation
if ($this->confirm('Do you wish to continue?', true)) {
    // User said yes
}

// Autocomplete / Anticipate
$name = $this->anticipate('What is your name?', ['John', 'Jane', 'Joe']);

// Choice with options
$role = $this->choice(
    'What role should the user have?',
    ['Admin', 'Editor', 'Subscriber'],
    default: 0,
    maxAttempts: 3,
    multiple: false,
);

// Choice with multiple selections
$permissions = $this->choice(
    'Select permissions',
    ['read', 'write', 'delete'],
    multiple: true,
);

// Table with search
$user = $this->choice(
    'Select a user',
    User::pluck('name', 'id')->toArray(),
    searchable: true,
);
```

### Writing Output

```php
// Status levels
$this->info('Operation successful');
$this->error('Something went wrong');
$this->warn('Be careful');
$this->line('Plain message');
$this->newLine(2); // Multiple blank lines

// Raw output (no formatting)
$this->output->write('Inline text');

// Tables
$headers = ['Name', 'Email'];
$rows = User::all(['name', 'email'])->toArray();
$this->table($headers, $rows);

// Progress bars
$users = User::where('subscribed', true)->get();
$bar = $this->output->createProgressBar($users->count());

foreach ($users as $user) {
    // Process user
    $bar->advance();
}

$bar->finish();
$this->newLine(2);

// Progress bar with custom message
$bar = $this->output->createProgressBar($users->count());
$bar->setFormat(' %current%/%max% [%bar%] %percent:3s%% %message%');
$bar->setMessage('Processing...');
$bar->start();

// Task indicator
$this->task('Processing users', function () {
    return User::where('subscribed', true)->update(['processed' => true]);
});
// Output: "Processing users: ✔" or "Processing users: ✖"

// Alert box
$this->alert('Important operation starting');

// Bullet list
$this->bulletList([
    'Item 1: description',
    'Item 2: description',
]);
```

### Components (More Structured Output)

```php
$this->components->info('Building application...');
$this->components->task('Compiling assets', fn () => true);
$this->components->warn('This is a warning');
$this->components->twoColumnDetail('Key', 'Value');
$this->components->bulletList(['First', 'Second']);
```

## Registering Commands

In Laravel 11+, commands in `app/Console/Commands/` are auto-discovered. For manual registration in `bootstrap/app.php`:

```php
use Illuminate\Foundation\Application;
use Illuminate\Console\Scheduling\Schedule;

->withCommands([
    __DIR__ . '/../app/Console/Commands',
    App\Console\Commands\SendEmails::class,
])
```

## Programmatically Executing Commands

```php
use Illuminate\Support\Facades\Artisan;

// Execute and get exit code
$exitCode = Artisan::call('mail:send', [
    'user' => 1,
    '--queue' => true,
]);

// Queue command for background execution
Artisan::queue('mail:send', ['user' => 1])
    ->onConnection('redis')
    ->onQueue('commands')
    ->delay(now()->addMinutes(10));

// Pass options
Artisan::call('mail:send', [
    'user' => 1,
    '--queue' => 'high',
]);
```

### Calling Commands From Other Commands

```php
public function handle(): void
{
    $this->call('mail:send', [
        'user' => 1,
    ]);

    // Silently (suppresses output)
    $this->callSilently('mail:send', ['user' => 1]);

    // Capture output
    $output = $this->output->capture(function () {
        $this->call('mail:send', ['user' => 1]);
    });
}
```

## Signal Handling

Trap OS signals within a command:

```php
public function handle(): void
{
    $this->trap(SIGTERM, function () {
        $this->info('Shutting down gracefully...');
        // Cleanup resources
        exit(0);
    });

    $this->trap(SIGINT, function () {
        $this->warn('Interrupted by user');
        exit(1);
    });

    // Long-running process
    while (true) {
        // Process
    }
}
```

## Stub Customization

Publish stubs to `stubs/` directory for customization:

```shell
php artisan stub:publish
```

Customize generated files by modifying stubs:

```
stubs/
├── console.stub          # php artisan make:command
├── controller.api.stub   # php artisan make:controller --api
├── controller.model.stub # php artisan make:controller --model
├── controller.stub       # php artisan make:controller
├── event.stub
├── job.stub
├── model.stub
├── notification.stub
├── etc.
```

## Testing Commands

```php
<?php

use Illuminate\Support\Facades\Artisan;

test('command sends email', function () {
    $user = User::factory()->create();

    $this->artisan('mail:send', ['user' => $user->id])
        ->expectsQuestion('What is your name?', 'Taylor Otwell')
        ->expectsChoice('Which language?', 'PHP', ['PHP', 'Ruby'])
        ->expectsOutput('Email sent successfully')
        ->doesntExpectOutput('Error')
        ->assertExitCode(0);
});
```

## Best Practices

1. **Keep commands thin** — delegate business logic to services and actions
2. **Use `#[Signature]` and `#[Description]` attributes** — cleaner than `$signature` and `$description` properties
3. **Use `PromptsForMissingInput`** — improves UX by automatically prompting for required arguments
4. **Implement `Isolatable` for scheduled commands** — prevents overlaps
5. **Use `$this->components->task()` for reporting progress** — cleaner than manual progress bar management
6. **Return `Command::SUCCESS` or `Command::FAILURE`** — enables composability in pipelines
7. **Use `Artisan::queue()` for heavy commands** — avoid blocking the HTTP request
8. **Handle signals in long-running commands** — `$this->trap()` for graceful shutdown
9. **Use `$this->call()` to compose complex workflows** — chain multiple commands together
10. **Test command I/O** — use `expectsQuestion()`, `expectsOutput()`, and `assertExitCode()` in tests
