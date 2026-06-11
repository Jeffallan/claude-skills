# Laravel Fortify

## What is Fortify?

Frontend-agnostic authentication backend. Registers routes and controllers for login, registration, password reset, email verification, two-factor auth, and passkeys. No UI included — pair it with your own frontend.

## When to Use It

- You need auth backend but want a custom frontend (Blade, Vue, React, etc.)
- Do **not** use if you're already using a starter kit (Laravel Breeze, Jetstream) — those ship with Fortify built-in
- Not competing with Sanctum: Fortify handles registration/reset/etc., Sanctum handles token management and session auth

## Installation

```bash
composer require laravel/fortify
php artisan fortify:install
php artisan migrate
```

`fortify:install` publishes:
- `app/Actions/Fortify/*` — `CreateNewUser`, `ResetUserPassword`, `UpdateUserPassword`, `UpdateUserProfileInformation`
- `app/Providers/FortifyServiceProvider.php`
- `config/fortify.php`
- Database migrations

## Bootstrap / App Config

Laravel 13.x uses `bootstrap/app.php` for service registration. Enable Fortify routing:

```php
<?php

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__ . '/../routes/web.php',
        api: __DIR__ . '/../routes/api.php',
        commands: __DIR__ . '/../routes/console.php',
        health: '/up',
        fortify: true, // enables Fortify routes
    )
    ->withFortify() // registers FortifyServiceProvider
    ->create();
```

## Features Configuration

```php
<?php

// config/fortify.php
use Laravel\Fortify\Features;

'features' => [
    Features::registration(),
    Features::resetPasswords(),
    Features::emailVerification(),
    Features::updateProfileInformation(),
    Features::updatePasswords(),
    Features::twoFactorAuthentication([
        'confirm' => true,
        'confirmPassword' => true,
    ]),
    Features::passkeys([
        'confirmPassword' => true,
    ]),
],
```

## Disabling Views

For SPAs or custom API frontends, set `views` to `false`:

```php
<?php

// config/fortify.php
'views' => false,
```

If using password reset with views disabled, still define a named route `password.reset` (used by the `ResetPassword` notification to generate reset URLs).

## View Customization

All view rendering is configured in `FortifyServiceProvider::boot()`:

```php
<?php

use Laravel\Fortify\Fortify;

public function boot(): void
{
    Fortify::loginView(fn () => view('auth.login'));
    Fortify::registerView(fn () => view('auth.register'));
    Fortify::requestPasswordResetLinkView(fn () => view('auth.forgot-password'));
    Fortify::resetPasswordView(fn (Request $request) => view('auth.reset-password', ['request' => $request]));
    Fortify::verifyEmailView(fn () => view('auth.verify-email'));
    Fortify::twoFactorChallengeView(fn () => view('auth.two-factor-challenge'));
    Fortify::confirmPasswordView(fn () => view('auth.confirm-password'));
}
```

## Authentication

### Login Endpoint

`POST /login` — expects `email` (or username field matching `fortify.username` config) and `password`. Optional boolean `remember`.

- Success: redirect to `fortify.home` URI (or 200 for XHR)
- Failure: redirect back with validation errors (or 422 for XHR)

### Customizing User Authentication

```php
<?php

use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Laravel\Fortify\Fortify;

Fortify::authenticateUsing(function (Request $request) {
    $user = User::where('email', $request->email)->first();

    if ($user && Hash::check($request->password, $user->password)) {
        return $user;
    }
});
```

### Customizing the Authentication Pipeline

```php
<?php

use Laravel\Fortify\Actions\AttemptToAuthenticate;
use Laravel\Fortify\Actions\CanonicalizeUsername;
use Laravel\Fortify\Actions\EnsureLoginIsNotThrottled;
use Laravel\Fortify\Actions\PrepareAuthenticatedSession;
use Laravel\Fortify\Actions\RedirectIfTwoFactorAuthenticatable;
use Laravel\Fortify\Features;
use Laravel\Fortify\Fortify;
use Illuminate\Http\Request;

Fortify::authenticateThrough(function (Request $request) {
    return array_filter([
        config('fortify.limiters.login') ? null : EnsureLoginIsNotThrottled::class,
        config('fortify.lowercase_usernames') ? CanonicalizeUsername::class : null,
        Features::enabled(Features::twoFactorAuthentication()) ? RedirectIfTwoFactorAuthenticatable::class : null,
        AttemptToAuthenticate::class,
        PrepareAuthenticatedSession::class,
    ]);
});
```

### Authentication Guard

Customize via `config/fortify.php` `guard` key. Defaults to `web`. For SPA auth, use `web` guard with Laravel Sanctum.

### Customizing Redirects

Override response contracts via service container binding in `FortifyServiceProvider::register()`:

```php
<?php

use Laravel\Fortify\Contracts\LogoutResponse;

$this->app->instance(LogoutResponse::class, new class implements LogoutResponse {
    public function toResponse($request)
    {
        return redirect('/');
    }
});
```

Available contracts:
- `LoginResponse`
- `LogoutResponse`
- `RegisterResponse`
- `PasswordResetResponse`
- `TwoFactorLoginResponse`
- `LockoutResponse`

## Two-Factor Authentication

### User Model Setup

```php
<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Fortify\TwoFactorAuthenticatable;

class User extends Authenticatable
{
    use Notifiable, TwoFactorAuthenticatable;
}
```

### Enabling

`POST /user/two-factor-authentication` — triggers password confirmation. Sets session `status = two-factor-authentication-enabled`.

### Confirming

Display QR code:

```php
$request->user()->twoFactorQrCodeSvg();
```

Display recovery codes:

```php
(array) $request->user()->recoveryCodes();
```

`POST /user/confirmed-two-factor-authentication` — expects `code`. Sets `status = two-factor-authentication-confirmed`.

### Authenticating

`GET /two-factor-challenge` — returns view. `POST /two-factor-challenge` — expects `code` (TOTP) or `recovery_code`.

- Success: redirect to `fortify.home` (204 for XHR)
- Failure: redirect back with errors (422 for XHR)

XHR login response includes `two_factor` boolean — redirect to challenge screen when `true`.

### Disabling

`DELETE /user/two-factor-authentication`

### Regenerating Recovery Codes

`POST /user/two-factor-recovery-codes`

## Passkeys (WebAuthn)

### User Model Setup

```php
<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Fortify\Contracts\PasskeyUser;
use Laravel\Fortify\PasskeyAuthenticatable;

class User extends Authenticatable implements PasskeyUser
{
    use Notifiable, PasskeyAuthenticatable;
}
```

### Passkeys Configuration

```php
<?php

// config/fortify.php
'passkeys' => [
    'relying_party_id' => parse_url(config('app.url'), PHP_URL_HOST),
    'allowed_origins' => [config('app.url')],
    'user_handle_secret' => config('app.key'),
    'timeout' => 60000,
],
```

### JavaScript Client

```bash
npm install @laravel/passkeys
```

```js
import { Passkeys } from "@laravel/passkeys";

await Passkeys.register({ name: "MacBook Pro" });
await Passkeys.verify();
```

Also available for React (`@laravel/passkeys/react`), Vue (`@laravel/passkeys/vue`), and Svelte (`@laravel/passkeys/svelte`).

### Authentication Flow

1. `GET /passkeys/login/options` — returns WebAuthn challenge
2. Pass to `navigator.credentials.get(...)` on the frontend
3. `POST /passkeys/login` — send credential + optional `remember`

### Confirming Password With Passkeys

1. `GET /passkeys/confirm/options`
2. `POST /passkeys/confirm` — sends credential

### Registering Passkeys

1. `GET /user/passkeys/options`
2. `POST /user/passkeys` — sends `name` + `credential`

### Deleting Passkeys

`DELETE /user/passkeys/{passkey}`

## Registration

`POST /register` — expects `name`, email/username, `password`, `password_confirmation`.

- Success: redirect to `fortify.home` (201 for XHR)
- Failure: redirect back with errors (422 for XHR)

### Customizing Registration

Modify `app/Actions/Fortify/CreateNewUser.php` — contains validation rules and user creation logic.

```php
<?php

namespace App\Actions\Fortify;

use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Validator;
use Laravel\Fortify\Contracts\CreatesNewUsers;

class CreateNewUser implements CreatesNewUsers
{
    use PasswordValidationRules;

    public function create(array $input): User
    {
        Validator::make($input, [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'email', 'max:255', 'unique:users'],
            'password' => $this->passwordRules(),
        ])->validate();

        return User::create([
            'name' => $input['name'],
            'email' => $input['email'],
            'password' => Hash::make($input['password']),
        ]);
    }
}
```

Override the action class:

```php
<?php

use App\Actions\Fortify\CreateNewUser;

Fortify::createUsersUsing(CreateNewUser::class);
```

## Password Reset

### Request Reset Link

`POST /forgot-password` — expects `email`.

- Success: redirect back with `status` session variable
- Failure: redirect back with errors (422 for XHR)

### Reset Password

`POST /reset-password` — expects `email`, `password`, `password_confirmation`, `token` (from route param).

- Success: redirect to `/login` with `status`
- Failure: redirect back with errors (422 for XHR)

### Customizing Password Resets

Modify `app/Actions/Fortify/ResetUserPassword.php`:

```php
<?php

use Laravel\Fortify\Contracts\ResetsUserPasswords;

Fortify::resetUserPasswordsUsing(ResetUserPassword::class);
```

## Email Verification

Requires `MustVerifyEmail` interface on User model + `emailVerification` feature enabled.

- `POST /email/verification-notification` — resends verification link. Sets `status = verification-link-sent`.
- Protect routes with `verified` middleware:

```php
<?php

Route::get('/dashboard', function () {
    // ...
})->middleware(['verified']);
```

## Profile / Password Update

```php
<?php

// Update profile info
Fortify::updateUserProfileInformationUsing(UpdateUserProfileInformation::class);

// Update password
Fortify::updateUserPasswordsUsing(UpdateUserPassword::class);
```

Modify the corresponding action classes in `app/Actions/Fortify/`.

## Rate Limiting

Configure limiters in `config/fortify.php`:

```php
<?php

'limiters' => [
    'login' => 'login',
    'two-factor' => 'two-factor',
    'passkeys' => 'passkeys',
],
```

Define the actual limiter in `AppServiceProvider` or a `RouteServiceProvider`:

```php
<?php

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;

RateLimiter::for('login', function (Request $request) {
    $email = (string) $request->email;

    return Limit::perMinute(5)->by($email . $request->ip());
});
```

## Testing

```php
<?php

use App\Models\User;
use Laravel\Fortify\Fortify;
use Illuminate\Support\Facades\Hash;

// Custom auth logic in tests
Fortify::authenticateUsing(function (Request $request) {
    $user = User::where('email', $request->email)->first();

    return $user && Hash::check($request->password, $user->password) ? $user : null;
});

// Test registration
$response = $this->post('/register', [
    'name' => 'Test User',
    'email' => 'test@example.com',
    'password' => 'password',
    'password_confirmation' => 'password',
]);

$response->assertRedirect('/home');
$this->assertAuthenticated();
```

## Best Practices

- Set `'views' => false` for SPAs or API-driven frontends
- Disable features you don't use in `config/fortify.php` to reduce route surface
- Customize via `FortifyServiceProvider` — keep logic centralized
- Use `Fortify::authenticateUsing()` for non-standard auth (LDAP, OTP, etc.)
- Override response contracts instead of modifying vendor code
- Rate-limit login, 2FA, and passkey endpoints
- Use `Features::passkeys()` with `confirmPassword: true` for security
- Pair with Sanctum for SPA+API setups where Fortify handles auth initiation and Sanctum handles session/token persistence
