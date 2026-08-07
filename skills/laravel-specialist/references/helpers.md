# Helpers

## Arrays & Objects

All methods in this section are available on `Illuminate\Support\Arr`. The global helpers `data_get`, `data_set`, `data_fill`, `head`, and `last` are also listed.

### Arr::accessible

```php
use Illuminate\Support\Arr;

Arr::accessible(['a', 'b']); // true
Arr::accessible('string');   // false
Arr::accessible(new stdClass); // false
```

### Arr::add

```php
$array = Arr::add(['name' => 'John'], 'age', 30);
// ['name' => 'John', 'age' => 30]

// No-op if key already exists
$array = Arr::add(['name' => 'John'], 'name', 'Jane');
// ['name' => 'John']
```

### Arr::collapse

```php
$array = Arr::collapse([[1, 2], [3, 4], [5]]);
// [1, 2, 3, 4, 5]
```

### Arr::crossJoin

```php
$result = Arr::crossJoin([1, 2], ['a', 'b']);
// [[1, 'a'], [1, 'b'], [2, 'a'], [2, 'b']]
```

### Arr::dot

```php
$array = ['user' => ['name' => 'John', 'profile' => ['age' => 30]]];
$dotted = Arr::dot($array);
// ['user.name' => 'John', 'user.profile.age' => 30]
```

### Arr::except

```php
$array = ['name' => 'John', 'age' => 30, 'role' => 'admin'];
$filtered = Arr::except($array, ['role']);
// ['name' => 'John', 'age' => 30]
```

### Arr::first

```php
$array = [100, 200, 300];
$first = Arr::first($array, fn (int $value) => $value >= 200);
// 200

$first = Arr::first($array, fn (int $value) => $value > 500, 0);
// 0 (default)
```

### Arr::flatten

```php
$array = Arr::flatten([1, [2, [3, [4]]]]);
// [1, 2, 3, 4]

$array = Arr::flatten([1, [2, [3, [4]]]], depth: 2);
// [1, 2, 3, [4]]
```

### Arr::forget

```php
$array = ['products' => ['desk' => ['price' => 100]]];
Arr::forget($array, 'products.desk');
// ['products' => []]
```

### Arr::get

```php
$array = ['products' => ['desk' => ['price' => 100]]];
Arr::get($array, 'products.desk.price');  // 100
Arr::get($array, 'products.desk.discount', 0); // 0
Arr::get($array, 'products.desk.discount', fn () => 0); // 0
```

### Arr::has

```php
$array = ['product' => ['name' => 'Desk', 'price' => 100]];
Arr::has($array, 'product.name');      // true
Arr::has($array, ['product.name', 'product.price']); // true
Arr::has($array, 'product.discount');  // false
```

### Arr::isAssoc

```php
Arr::isAssoc(['a', 'b']);          // false (list)
Arr::isAssoc(['a' => 1, 'b' => 2]); // true (associative)
```

### Arr::isList

```php
Arr::isList(['a', 'b']);            // true
Arr::isAssoc(['a' => 1, 'b' => 2]); // false
```

### Arr::join

```php
Arr::join(['a', 'b', 'c'], ', ');        // 'a, b, c'
Arr::join(['a', 'b', 'c'], ', ', ' and '); // 'a, b and c'
```

### Arr::keyBy

```php
$array = [
    ['id' => 1, 'name' => 'John'],
    ['id' => 2, 'name' => 'Jane'],
];
$keyed = Arr::keyBy($array, 'id');
// [1 => ['id' => 1, 'name' => 'John'], 2 => ['id' => 2, 'name' => 'Jane']]
```

### Arr::last

```php
$array = [100, 200, 300];
$last = Arr::last($array, fn (int $value) => $value < 300);
// 200

$last = Arr::last($array, fn (int $value) => $value > 500, 0);
// 0 (default)
```

### Arr::map

```php
$array = Arr::map([1, 2, 3], fn (int $value) => $value * 2);
// [2, 4, 6]
```

### Arr::mapSpread

```php
$array = [[1, 2], [3, 4]];
$result = Arr::mapSpread($array, fn (int $a, int $b) => $a + $b);
// [3, 7]
```

### Arr::mapWithKeys

```php
$array = [
    ['id' => 1, 'name' => 'John'],
    ['id' => 2, 'name' => 'Jane'],
];
$mapped = Arr::mapWithKeys($array, fn (array $item) => [$item['id'] => $item['name']]);
// [1 => 'John', 2 => 'Jane']
```

### Arr::only

```php
$array = ['name' => 'John', 'age' => 30, 'role' => 'admin'];
$filtered = Arr::only($array, ['name', 'role']);
// ['name' => 'John', 'role' => 'admin']
```

### Arr::pluck

```php
$array = [
    ['id' => 1, 'name' => 'John'],
    ['id' => 2, 'name' => 'Jane'],
];
Arr::pluck($array, 'name'); // ['John', 'Jane']

// With keys
Arr::pluck($array, 'name', 'id'); // [1 => 'John', 2 => 'Jane']

// Dot notation
$array = [['user' => ['name' => 'John']]];
Arr::pluck($array, 'user.name'); // ['John']
```

### Arr::prepend

```php
$array = Arr::prepend([1, 2, 3], 0);
// [0, 1, 2, 3]

$array = Arr::prepend(['name' => 'John'], 'admin', 'role');
// ['role' => 'admin', 'name' => 'John']
```

### Arr::pull

```php
$array = ['name' => 'John', 'age' => 30];
$name = Arr::pull($array, 'name');
// $name = 'John', $array = ['age' => 30]
```

### Arr::query

```php
$array = Arr::query(['name' => 'John', 'role' => 'admin']);
// 'name=John&role=admin'
```

### Arr::random

```php
$array = Arr::random([1, 2, 3, 4]);  // Random single value
$items = Arr::random([1, 2, 3, 4], 2); // Random 2 values
```

### Arr::set

```php
$array = ['products' => ['desk' => ['price' => 100]]];
Arr::set($array, 'products.desk.price', 200);
// ['products' => ['desk' => ['price' => 200]]]
```

### Arr::shuffle

```php
$shuffled = Arr::shuffle([1, 2, 3, 4]);
// Random order
```

### Arr::sort

```php
$sorted = Arr::sort(['Desk', 'Table', 'Chair']);
// ['Chair', 'Desk', 'Table']

$sorted = Arr::sort([
    ['name' => 'Desk'],
    ['name' => 'Table'],
], fn (array $value) => $value['name']);
// [['name' => 'Desk'], ['name' => 'Table']]
```

### Arr::sortDesc

```php
$sorted = Arr::sortDesc(['Desk', 'Table', 'Chair']);
// ['Table', 'Desk', 'Chair']
```

### Arr::take

```php
$taken = Arr::take([1, 2, 3, 4], 2);
// [1, 2]

$taken = Arr::take([1, 2, 3, 4], -2);
// [3, 4]
```

### Arr::toCssClasses

```php
$isActive = false;
$hasError = true;

Arr::toCssClasses(['p-4', 'font-bold' => $isActive, 'bg-red' => $hasError]);
// 'p-4 bg-red'
```

### Arr::toCssStyles

```php
$hasColor = true;

Arr::toCssStyles(['background-color: blue', 'color: blue' => $hasColor]);
// 'background-color: blue; color: blue;'
```

### Arr::where

```php
$filtered = Arr::where([1, 2, 3, 4], fn (int $value) => $value > 2);
// [2 => 3, 3 => 4] (keeps keys)
```

### Arr::wrap

```php
Arr::wrap('John');         // ['John']
Arr::wrap(['John']);       // ['John']
Arr::wrap(null);           // []
```

### data_get

```php
$data = ['user' => ['profile' => ['age' => 30]]];
data_get($data, 'user.profile.age');  // 30
data_get($data, 'user.profile.age', 0); // 30

// Supports wildcards
$data = [['name' => 'John'], ['name' => 'Jane']];
data_get($data, '*.name'); // ['John', 'Jane']
```

### data_set

```php
$data = ['products' => ['desk' => ['price' => 100]]];
data_set($data, 'products.desk.price', 200);
// ['products' => ['desk' => ['price' => 200]]]

// Wildcard
$data = [['name' => 'Desk'], ['name' => 'Table']];
data_set($data, '*.price', 50);

// With overwrite: false — does not overwrite existing values
data_set($data, 'products.desk.price', 200, overwrite: false);
```

### data_fill

```php
$data = ['products' => ['desk' => ['price' => 100]]];
data_fill($data, 'products.desk.discount', 0);
// ['products' => ['desk' => ['price' => 100, 'discount' => 0]]]

// No-op if key already exists
data_fill($data, 'products.desk.price', 200);
// ['products' => ['desk' => ['price' => 100]]]
```

### head

```php
head([1, 2, 3]); // 1
```

### last

```php
last([1, 2, 3]); // 3
```

## Numbers

All number helpers are available on `Illuminate\Support\Number`.

### Number::format

```php
use Illuminate\Support\Number;

Number::format(1000);          // '1,000'
Number::format(1000.5, precision: 2); // '1,000.50'
Number::format(1000, locale: 'de');   // '1.000'
```

### Number::currency

```php
Number::currency(1000);                      // '$1,000.00'
Number::currency(1000, in: 'EUR');           // '€1,000.00'
Number::currency(1000, in: 'EUR', locale: 'de'); // '1.000,00 €'
Number::currency(1000, precision: 0);        // '$1,000'
```

### Number::abbreviate

```php
Number::abbreviate(1000);            // '1K'
Number::abbreviate(489939);          // '490K'
Number::abbreviate(1230000, precision: 2); // '1.23M'
```

### Number::fileSize

```php
Number::fileSize(1024);            // '1 KB'
Number::fileSize(1024 * 1024);     // '1 MB'
Number::fileSize(1500);            // '1 KB'
Number::fileSize(1500, precision: 2); // '1.46 KB'
```

### Number::forHumans

```php
Number::forHumans(1000);     // '1 thousand'
Number::forHumans(1000000);  // '1 million'
Number::forHumans(1234567);  // '1 million'
```

### Number::ordinal

```php
Number::ordinal(1);   // '1st'
Number::ordinal(2);   // '2nd'
Number::ordinal(3);   // '3rd'
Number::ordinal(21);  // '21st'
Number::ordinal(12);  // '12th'
```

### Number::percentage

```php
Number::percentage(10);           // '10%'
Number::percentage(10.123, precision: 2); // '10.12%'
Number::percentage(10, locale: 'de');     // '10 %'
```

### Number::spell

```php
Number::spell(102);                     // 'one hundred and two'
Number::spell(88, locale: 'fr');        // 'quatre-vingt-huit'
Number::spell(10, after: 10);           // '10' (not spelled if <= after)
Number::spell(11, after: 10);           // 'eleven'
Number::spell(5, until: 10);            // 'five' (spelled if <= until)
Number::spell(10, until: 10);           // '10' (not spelled)
```

### Number::clamp

```php
Number::clamp(105, min: 10, max: 100); // 100
Number::clamp(5, min: 10, max: 100);   // 10
Number::clamp(50, min: 10, max: 100);  // 50
```

## Paths

```php
app_path('Models/User.php');       // /app/Models/User.php
base_path('vendor/autoload.php');  // /vendor/autoload.php
config_path('app.php');            // /config/app.php
database_path('migrations');       // /database/migrations
lang_path('en/messages.php');      // /lang/en/messages.php
public_path('css/app.css');        // /public/css/app.css
resource_path('views/welcome.blade.php'); // /resources/views/welcome.blade.php
storage_path('app/public');        // /storage/app/public
```

## URLs

```php
// Generate URL for a named route
$url = route('users.show', ['user' => 1]);
$url = route('users.show', ['user' => 1], absolute: false);

// Generate URL to a controller action
$url = action([UserController::class, 'show'], ['user' => 1]);

// Redirect to a named route
return to_route('users.show', ['user' => 1]);

// Redirect to a controller action
return to_action([UserController::class, 'show'], ['user' => 1]);

// Asset URLs
asset('css/app.css');           // http://example.com/css/app.css
secure_asset('css/app.css');    // https://example.com/css/app.css

// Current URL with or without scheme
url('/users');                  // http://example.com/users
secure_url('/users');           // https://example.com/users

// Force HTTPS scheme in generated URLs
URL::forceScheme('https');
```

## Miscellaneous

### abort / abort_if

```php
abort(404);
abort_if(! $user, 403, 'Unauthorized');
abort_unless($user, 401, 'Please login');
```

### app

```php
$container = app();
$service = app('HelpSpot\API');
$service = app()->make('HelpSpot\API');
$version = app()->version();
$inProduction = app()->environment('production');
```

### auth

```php
$user = auth()->user();
$id = auth()->id();
auth()->login($user);
auth()->logout();
```

### back

```php
return back(); // Redirect to previous page
return back()->with('status', 'Saved!');
```

### bcrypt

```php
$hash = bcrypt('plain-text-password');
```

### blank / filled

```php
blank('');       // true
blank('test');   // false
blank([]);       // true

filled('test');  // true
filled('');      // false
```

### broadcast

```php
broadcast(new OrderShipped($order));
broadcast(new OrderShipped($order))->toOthers();
```

### cache

```php
cache(['key' => 'value'], 300);   // Store for 5 minutes
$value = cache('key');            // Retrieve
cache()->put('key', 'value', 300); // Store via facade
```

### collect

```php
$collection = collect([1, 2, 3]);
$collection = collect(['name' => 'John']);
```

### config

```php
$timezone = config('app.timezone');
$timezone = config('app.timezone', 'UTC');
config(['app.timezone' => 'America/New_York']);
```

### cookie

```php
$value = cookie('name');
$response = new Response('Hello World');
$response->withCookie(cookie('name', 'value', 120));
```

### csrf_field / csrf_token

```php
csrf_field();  // '<input type="hidden" name="_token" value="abc123">'
csrf_token();  // 'abc123'
```

### dd / dump

```php
dd($variable);           // Dump and die
dd($var1, $var2, $var3); // Multiple values

dump($variable);         // Dump without dying
```

### decrypt / encrypt

```php
$encrypted = encrypt('sensitive-data');
$decrypted = decrypt($encrypted);
```

### dispatch / dispatch_sync

```php
dispatch(new ProcessPodcast($podcast)); // Queue job
dispatch_sync(new ProcessPodcast($podcast)); // Run synchronously
ProcessPodcast::dispatch($podcast);    // Via trait
```

### env

```php
$key = env('APP_KEY');
$debug = env('APP_DEBUG', false);
```
> **Note:** Use `config()` in production. Only use `env()` in config files.

### event

```php
event(new OrderShipped($order));
```

### info / logger

```php
info('User logged in', ['id' => $userId]);
logger('Something happened');
logger()->error('Failed to process', ['order' => $orderId]);
```

### method_field

```php
method_field('PUT');
// '<input type="hidden" name="_method" value="PUT">'
```

### now / today

```php
now();           // Carbon\Carbon instance
today();         // Carbon\Carbon instance at 00:00:00
now()->addDay();
today()->subMonth();
```

### old

```php
$name = old('name');
$email = old('email', 'default@example.com');
```

### once

```php
// Cache the result for the duration of the request
$exp = once(fn () => expensiveComputation());
// Subsequent calls return the cached result
```

### optional

```php
optional($user?->profile)->bio;
// Returns null if $user->profile is null, no error
```

### policy

```php
if (policy($post, 'update', $user)) {
    // User can update
}
```

### redirect

```php
return redirect('/home');
return redirect()->route('users.show', ['user' => 1]);
return redirect()->action([UserController::class, 'index']);
return redirect()->away('https://example.com');
return redirect()->back()->withInput();
```

### report

```php
report($exception); // Log exception via the exception handler
```

### request

```php
$name = request('name');
$all = request()->all();
$user = request()->user();
$isApi = request()->expectsJson();
```

### rescue

```php
$result = rescue(fn () => riskyOperation(), 'fallback');
$result = rescue(fn () => riskyOperation(), fn () => 'fallback');
```

### resolve

```php
$service = resolve(Service::class);
$service = resolve('HelpSpot\API', ['key' => 'abc']);
```

### response

```php
return response('Hello', 200);
return response()->json(['user' => $user]);
return response()->json(['error' => 'Not found'], 404);
return response()->download($pathToFile);
return response()->streamDownload(function () {
    echo file_get_contents($pathToFile);
}, 'export.csv');
```

### retry

```php
$result = retry(3, function () {
    return unstableApiCall();
}, 100); // 100ms between attempts

$result = retry(3, function (int $attempt) {
    return unstableApiCall();
}, function (int $attempt) {
    return $attempt * 100; // Dynamic backoff
});
```

### session

```php
session(['key' => 'value']);
$value = session('key');
$value = session('key', 'default');
session()->flash('status', 'Task successful');
```

### tap

```php
$user = tap(User::find(1), function (User $user) {
    $user->update(['name' => 'Updated']);
    $user->save();
});
// Returns the User instance regardless of what the closure returns
```

### throw_if / throw_unless

```php
throw_if(! $user, \App\Exceptions\UserNotFoundException::class);
throw_unless($user, \App\Exceptions\UserNotFoundException::class);
```

### transform

```php
transform($value, fn (string $value) => ucfirst($value));
// Returns transformed value if not blank, else null

$value = transform($value, fn (string $v) => ucfirst($v), 'default');
```

### validator

```php
$validator = validator($request->all(), [
    'email' => 'required|email',
    'name' => 'required|string|max:255',
]);

if ($validator->fails()) {
    // Handle
}
```

### value

```php
$greeting = value(fn () => 'Hello World'); // Evaluates the closure
value('Hello'); // Returns 'Hello' (pass-through for non-closures)
```

### view

```php
return view('profile.show', ['user' => $user]);
$html = view('emails.welcome', ['user' => $user])->render();
```

### when

```php
$value = when(true, fn () => 'first', fn () => 'second');
// 'first'

$value = when(false, fn () => 'first', fn () => 'second');
// 'second'
```

### with

```php
$user = with(User::find(1), function (User $user) {
    $user->load('posts');
    return $user;
});

// Single expression version
$user = with(User::find(1)); // Just returns the value
```

## Other Utilities

### Benchmark

```php
use Illuminate\Support\Benchmark;

// Single callback
Benchmark::dd(fn () => User::find(1)); // 0.1 ms

// Compare scenarios
Benchmark::dd([
    'Scenario 1' => fn () => User::count(),
    'Scenario 2' => fn () => User::all()->count(),
]);

// Return without dumping
$time = Benchmark::measure(fn () => User::find(1));
// 0.1

$times = Benchmark::measure([
    'with_redis' => fn () => cache('key'),
    'without' => fn () => DB::table('cache')->first(),
]);
// ['with_redis' => 0.5, 'without' => 3.2]

// Warm up specific return type
$result = Benchmark::value(fn () => User::count());
// Returns the actual value, not the time
```

### Lottery

```php
use Illuminate\Support\Lottery;

Lottery::odds(1, 100)->winner(fn () => $user->win())
    ->loser(fn () => $user->lose())
    ->choose();

// As a class
class ReportCpuJob implements ShouldQueue
{
    use Dispatchable;

    public function __construct()
    {
        // Runs in 1 out of 100 jobs
    }

    public static function shouldDispatch(): Lottery
    {
        return Lottery::odds(1, 100);
    }
}
```

### Pipeline

```php
use Illuminate\Pipeline\Pipeline;

$result = app(Pipeline::class)
    ->send($request)
    ->through([
        EnsureTokenIsValid::class,
        EnsureUserIsSubscribed::class,
        SetLocale::class,
    ])
    ->then(fn ($request) => (new HomeController)->index($request));

// Each pipe is a class with handle($request, $next) method
```

### Sleep

```php
use Illuminate\Support\Sleep;

Sleep::for(1.5)->minutes();
Sleep::for(2)->seconds();
Sleep::for(500)->milliseconds();
Sleep::for(5000)->microseconds();
Sleep::until(now()->addMinute());
Sleep::sleep(2);           // PHP sleep alias
Sleep::usleep(5000);       // PHP usleep alias

// Return value after sleeping
$result = Sleep::for(1)->second()->then(fn () => 1 + 1);

// Sleep while condition is true
Sleep::for(1)->second()->while(fn () => shouldKeepSleeping());
```

### Timebox

```php
use Illuminate\Support\Timebox;

$result = (new Timebox)->call(function () {
    // Run at most 5 seconds
    return $this->process();
}, 5);

// With early return
$result = (new Timebox)->call(function ($timebox) {
    if ($this->shouldReturnEarly()) {
        $timebox->returnEarly();
    }
    return $this->process();
}, 5);
```

### URI

```php
use Illuminate\Support\Uri;

$uri = Uri::of('https://laravel.com/docs')
    ->withQuery(['page' => 2, 'search' => 'eloquent']);

// 'https://laravel.com/docs?page=2&search=eloquent'

$uri = Uri::of('https://laravel.com')
    ->withPath('/docs')
    ->withFragment('installation');

// 'https://laravel.com/docs#installation'

$uri = Uri::of('https://laravel.com/docs/11.x')
    ->replacePath('/docs/12.x');

// 'https://laravel.com/docs/12.x'

// Retrieve parsed components
Uri::of('https://user@laravel.com:8080/docs?q=eloquent#first')
    ->scheme();   // 'https'
    ->user();     // 'user'
    ->host();     // 'laravel.com'
    ->port();     // 8080
    ->path();     // '/docs'
    ->query();    // 'q=eloquent'
    ->fragment(); // 'first'
```
