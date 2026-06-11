# Laravel Socialite

## Overview

OAuth 1.0 & 2.0 authentication provider. Supports Facebook, X, LinkedIn, Google, GitHub, GitLab, Bitbucket, and Slack. Community adapters at [socialiteproviders.com](https://socialiteproviders.com/).

## Installation

```bash
composer require laravel/socialite
```

## Configuration

Add credentials to `config/services.php`:

```php
<?php

'github' => [
    'client_id' => env('GITHUB_CLIENT_ID'),
    'client_secret' => env('GITHUB_CLIENT_SECRET'),
    'redirect' => 'http://example.com/callback-url',
],
```

Provider keys: `facebook`, `x`, `linkedin-openid`, `google`, `github`, `gitlab`, `bitbucket`, `slack`, `slack-openid`.

Relative `redirect` paths are resolved to full URLs automatically.

## Authentication

### Routing

Two routes: one to redirect, one to handle the callback:

```php
<?php

use Laravel\Socialite\Socialite;

Route::get('/auth/redirect', function () {
    return Socialite::driver('github')->redirect();
});

Route::get('/auth/callback', function () {
    $user = Socialite::driver('github')->user();

    // $user->token
});
```

### Authentication and Storage

```php
<?php

use App\Models\User;
use Illuminate\Support\Facades\Auth;
use Laravel\Socialite\Socialite;

Route::get('/auth/callback', function () {
    $githubUser = Socialite::driver('github')->user();

    $user = User::updateOrCreate([
        'github_id' => $githubUser->id,
    ], [
        'name' => $githubUser->name,
        'email' => $githubUser->email,
        'github_token' => $githubUser->token,
        'github_refresh_token' => $githubUser->refreshToken,
    ]);

    Auth::login($user);

    return redirect('/dashboard');
});
```

### Access Scopes

```php
<?php

// Merge scopes with existing
return Socialite::driver('github')
    ->scopes(['read:user', 'public_repo'])
    ->redirect();

// Overwrite all scopes
return Socialite::driver('github')
    ->setScopes(['read:user', 'public_repo'])
    ->redirect();
```

### Slack Bot Scopes

Slack has two token types: Bot (`xoxb-`) and User (`xoxp-`). Use `asBotUser()` for bot tokens (e.g. sending notifications to workspaces):

```php
<?php

// Redirect for bot token
return Socialite::driver('slack')
    ->asBotUser()
    ->setScopes(['chat:write', 'chat:write.public', 'chat:write.customize'])
    ->redirect();

// In callback, fetch user as bot
$user = Socialite::driver('slack')->asBotUser()->user();
```

When using bot tokens, only `$user->token` is hydrated.

### Optional Parameters

```php
<?php

return Socialite::driver('google')
    ->with(['hd' => 'example.com'])
    ->redirect();
```

Avoid reserved keywords: `state`, `response_type`.

## Retrieving User Details

```php
<?php

$user = Socialite::driver('github')->user();

// OAuth 2.0
$token = $user->token;
$refreshToken = $user->refreshToken;
$expiresIn = $user->expiresIn;

// OAuth 1.0
$token = $user->token;
$tokenSecret = $user->tokenSecret;

// All providers
$user->getId();
$user->getNickname();
$user->getName();
$user->getEmail();
$user->getAvatar();
```

### userFromToken (OAuth2)

If you already have a valid access token:

```php
<?php

$user = Socialite::driver('github')->userFromToken($token);
```

Supports Facebook Limited Login OIDC tokens as well.

### Stateless Authentication

Disable session state verification for APIs:

```php
<?php

return Socialite::driver('google')->stateless()->user();
```

## Testing

### Faking Redirect

```php
<?php

use Laravel\Socialite\Socialite;

test('user is redirected to github', function () {
    Socialite::fake('github');

    $response = $this->get('/auth/github/redirect');

    $response->assertRedirect();
});
```

### Faking Callback

```php
<?php

use Laravel\Socialite\Socialite;
use Laravel\Socialite\Two\User;

test('user can login with github', function () {
    Socialite::fake('github', (new User)->map([
        'id' => 'github-123',
        'name' => 'Jason Beggs',
        'email' => 'jason@example.com',
    ]));

    $response = $this->get('/auth/github/callback');

    $response->assertRedirect('/dashboard');

    $this->assertDatabaseHas('users', [
        'name' => 'Jason Beggs',
        'email' => 'jason@example.com',
        'github_id' => 'github-123',
    ]);
});
```

### Customizing the Fake User

```php
<?php

$fakeUser = (new User)->map([
    'id' => 'github-123',
    'name' => 'Jason Beggs',
    'email' => 'jason@example.com',
])->setToken('fake-token')
  ->setRefreshToken('fake-refresh-token')
  ->setExpiresIn(3600)
  ->setApprovedScopes(['read', 'write']);
```

## Best Practices

- Store `{provider}_id`, `{provider}_token`, and `{provider}_refresh_token` on the users table
- Use `updateOrCreate` to handle both first-time login and re-authentication
- Use `stateless()` for API-only apps or when you don't need session state
- Validate the user's email exists before creating an account (some providers may not return it)
- Register community providers via `SocialiteProviders` if not natively supported
- Always handle the case where the OAuth callback fails (e.g. user denies access)
