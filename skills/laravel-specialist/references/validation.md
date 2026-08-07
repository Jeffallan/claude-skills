# Validation

## Quickstart

```php
<?php

namespace App\Http\Controllers;

use App\Models\Post;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class PostController
{
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'content' => ['required', 'string'],
            'category_id' => ['required', 'exists:categories,id'],
            'tags' => ['nullable', 'array'],
            'tags.*' => ['exists:tags,id'],
            'published_at' => ['nullable', 'date', 'after:now'],
        ]);

        $post = Post::create($validated);

        return redirect()->route('posts.show', $post);
    }
}
```

## Form Request Validation

```bash
php artisan make:request StorePostRequest
```

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StorePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return auth()->check();
    }

    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'min:3', 'max:255'],
            'slug' => ['required', 'string', Rule::unique('posts', 'slug')],
            'content' => ['required', 'string', 'min:10'],
            'category_id' => ['required', 'exists:categories,id'],
            'tags' => ['array'],
            'tags.*' => ['exists:tags,id'],
            'published_at' => ['nullable', 'date', 'after_or_equal:today'],
        ];
    }

    public function messages(): array
    {
        return [
            'title.required' => 'A post title is required.',
            'title.min' => 'The title must be at least :min characters.',
            'slug.unique' => 'This slug is already in use.',
        ];
    }

    protected function prepareForValidation(): void
    {
        $this->merge([
            'slug' => str($this->title)->slug(),
        ]);
    }

    protected function passedValidation(): void
    {
        $this->merge([
            'excerpt' => str($this->content)->limit(150),
        ]);
    }

    public function after(): array
    {
        return [
            function ($validator) {
                if ($this->spamDetected($this->content)) {
                    $validator->errors()->add('content', 'Content appears to be spam.');
                }
            },
        ];
    }

    private function spamDetected(string $content): bool
    {
        return false;
    }
}
```

Using the form request in a controller:

```php
use App\Http\Requests\StorePostRequest;
use App\Models\Post;

public function store(StorePostRequest $request): Post
{
    return Post::create($request->validated());
}
```

## Form Request Attributes

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Attributes\StopOnFirstFailure;

#[StopOnFirstFailure]
class StorePostRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'content' => ['required', 'string'],
        ];
    }
}
```

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Attributes\FailOnUnknownFields;

#[FailOnUnknownFields]
class UpdatePostRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'title' => ['sometimes', 'string', 'max:255'],
        ];
    }
}
```

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Attributes\RedirectTo;

#[RedirectTo('/dashboard')]
class StorePostRequest extends FormRequest
{
    // On validation failure, redirect to /dashboard
}
```

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Attributes\ErrorBag;

#[ErrorBag('postCreation')]
class StorePostRequest extends FormRequest
{
    // Errors go to the 'postCreation' error bag
}
```

## Manually Creating Validators

```php
<?php

use Illuminate\Support\Facades\Validator;

$validator = Validator::make($request->all(), [
    'email' => ['required', 'email'],
    'password' => ['required', 'min:8'],
]);

if ($validator->fails()) {
    return redirect()->back()
        ->withErrors($validator)
        ->withInput();
}

$validated = $validator->validated();

// Retrieve only specific safe fields
$safe = $validator->safe()->only(['email', 'name']);
$exceptPassword = $validator->safe()->except(['password']);
```

## Named Error Bags

```php
<?php

use Illuminate\Support\Facades\Validator;

$validator = Validator::make($request->all(), [
    'title' => ['required', 'string'],
    'content' => ['required', 'string'],
]);

if ($validator->fails()) {
    return redirect()->back()
        ->withErrors($validator, 'postCreation');
}
```

```blade
@if ($errors->postCreation->any())
    <div class="alert alert-danger">
        <ul>
            @foreach ($errors->postCreation->all() as $error)
                <li>{{ $error }}</li>
            @endforeach
        </ul>
    </div>
@endif
```

## Available Validation Rules

| Rule | Description |
|------|-------------|
| `required` | Field must be present and non-empty |
| `string` | Must be a string |
| `integer` | Must be an integer |
| `numeric` | Must be numeric |
| `boolean` | Must be boolean-ish |
| `array` | Must be an array |
| `email` | Must be a valid email |
| `url` | Must be a valid URL |
| `date` | Must be a valid date |
| `date_format:Y-m-d` | Must match the given format |
| `after:today` | Must be after the given date |
| `before:2025-01-01` | Must be before the given date |
| `min:3` | Minimum length or value |
| `max:255` | Maximum length or value |
| `between:1,10` | Must be between the given range |
| `size:16` | Must be exactly the given size |
| `in:active,inactive` | Must be one of the given values |
| `not_in:draft` | Must not be one of the given values |
| `exists:users,id` | Must exist in the database |
| `unique:posts,slug` | Must be unique in the database |
| `confirmed` | Must match `field_confirmation` |
| `current_password` | Must match the user's current password |
| `image` | Must be an image file |
| `mimes:pdf,docx` | Must be one of the given MIME types |
| `mimetypes:image/jpeg` | Must match the given MIME type |
| `file` | Must be a file upload |
| `size:2048` | File size in KB |
| `prohibited` | Field must be empty or absent |
| `prohibited_if:status,draft` | Field must be empty when another field matches |
| `prohibits:field1,field2` | If present, the other fields must be empty |
| `required_if:status,draft` | Required when another field matches |
| `required_with:title` | Required when another field is present |
| `required_unless:status,published` | Required unless another field matches |
| `gt:field` | Must be greater than another field |
| `lt:field` | Must be less than another field |
| `regex:/^[a-z]+$/` | Must match the pattern |

## Conditionally Adding Rules

```php
<?php

use Illuminate\Support\Facades\Validator;

$validator = Validator::make($data, [
    'email' => ['required', 'email'],
    'role' => ['required', 'string'],
    'notify_all' => ['boolean'],
]);

$validator->sometimes('notification_email', 'email', function ($input) {
    return $input->notify_all === true;
});

$validator->sometimes('expires_at', 'date|after:today', function ($input) {
    return $input->role === 'temporary';
});
```

```php
// In a Form Request
public function rules(): array
{
    $rules = [
        'email' => ['required', 'email'],
        'role' => ['required', 'string'],
    ];

    if ($this->role === 'admin') {
        $rules['permissions'] = ['required', 'array'];
        $rules['permissions.*'] = ['exists:permissions,id'];
    }

    return $rules;
}
```

## Validating Arrays (Nested)

```php
<?php

use Illuminate\Support\Facades\Validator;

$validator = Validator::make($request->all(), [
    'users' => ['required', 'array'],
    'users.*.email' => ['required', 'email', 'distinct'],
    'users.*.name' => ['required', 'string', 'max:255'],
    'users.*.roles' => ['array'],
    'users.*.roles.*' => ['exists:roles,id'],
]);

// Access validated nested data
$validated = $validator->validated();
```

```php
// In a Form Request
public function rules(): array
{
    return [
        'items' => ['required', 'array', 'min:1'],
        'items.*.product_id' => ['required', 'exists:products,id'],
        'items.*.quantity' => ['required', 'integer', 'min:1', 'max:100'],
        'items.*.price' => ['required', 'numeric', 'min:0'],
    ];
}
```

## Custom Validation Rules

### Closure Rules

```php
<?php

use Illuminate\Support\Facades\Validator;

$validator = Validator::make($request->all(), [
    'coupon' => [
        'required',
        'string',
        function (string $attribute, mixed $value, \Closure $fail) {
            if (!Coupon::isValid($value)) {
                $fail('The :attribute is invalid or expired.');
            }
        },
    ],
]);
```

Stopping on first failure:

```php
function (string $attribute, mixed $value, \Closure $fail) {
    if (!Coupon::isValid($value)) {
        $fail('The :attribute is invalid or expired.')->translate();
    }
},
```

### Rule Objects

```bash
php artisan make:rule Uppercase
```

```php
<?php

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Uppercase implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (strtoupper($value) !== $value) {
            $fail('The :attribute must be uppercase.');
        }
    }
}
```

Using the rule:

```php
use App\Rules\Uppercase;

'name' => ['required', 'string', new Uppercase],
```

## Working with Validated Input

```php
// From Form Request
$validated = $request->validated();

// Only specific fields
$data = $request->safe()->only(['title', 'content']);
$data = $request->safe()->except(['tags']);

// From manual validator
$validated = $validator->validated();
$safe = $validator->safe()->only(['email']);
$safe = $validator->safe()->except(['password']);
```

## Error Messages in Views

```blade
@if ($errors->any())
    <div class="alert alert-danger">
        <ul>
            @foreach ($errors->all() as $error)
                <li>{{ $error }}</li>
            @endforeach
        </ul>
    </div>
@endif

@error('title')
    <span class="text-danger">{{ $message }}</span>
@enderror
```

## After Validation Hooks

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StorePostRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'content' => ['required', 'string'],
        ];
    }

    protected function passedValidation(): void
    {
        $this->merge([
            'slug' => str($this->title)->slug(),
            'user_id' => auth()->id(),
        ]);
    }

    public function after(): array
    {
        return [
            function ($validator) {
                if ($this->duplicateDetected()) {
                    $validator->errors()->add('title', 'A post with this title already exists.');
                }
            },
        ];
    }

    private function duplicateDetected(): bool
    {
        return false;
    }
}
```

## Best Practices

1. **Use Form Requests** - Keep validation logic out of controllers for reuse
2. **Validate at the boundary** - Validate all input before any business logic
3. **Use specific validation rules** - Prefer `exists:table,column` over manual DB checks
4. **Leverage `safe()->only()`** - Avoid mass-assignment vulnerabilities by whitelisting fields
5. **Use custom Rule objects** - Encapsulate complex validation logic
6. **Return meaningful error messages** - Use `:attribute` and `:value` placeholders
7. **Use `after()` hooks** - For cross-field or database validation after individual field checks
8. **Validate arrays with `*` notation** - Use `items.*.product_id` for nested validation
9. **Use `sometimes` for updates** - Only validate present fields during updates
10. **Stop on first failure when appropriate** - Use `#[StopOnFirstFailure]` for performance
11. **Use `#[FailOnUnknownFields]`** - Prevent unexpected extra fields in API requests
