# Collections

## Introduction

Laravel's `Illuminate\Support\Collection` provides a fluent, immutable wrapper for working with arrays of data. Every method returns a new `Collection` instance unless otherwise noted, allowing method chaining without mutating the original. The `collect()` helper creates a new collection from any array, iterable, or `null`.

```php
$collection = collect([1, 2, 3]);

// Methods return new instances — original is never mutated
$filtered = $collection->filter(fn (int $v) => $v > 1);
// $collection: [1, 2, 3]  (unchanged)
// $filtered:   [2 => 2, 3 => 3]  (new instance)
```

## Creating Collections

```php
use Illuminate\Support\Collection;

// collect() helper — most common
$c = collect([1, 2, 3]);

// Collection::make()
$c = Collection::make(['a', 'b']);

// Collection::fromJson()
$c = Collection::fromJson('{"name": "John", "age": 30}');
// ['name' => 'John', 'age' => 30]

// Collection::times() — call a closure N times
$c = Collection::times(3, fn (int $i) => $i * 2);
// [2, 4, 6]

// Collection::range() — inclusive numeric range (Laravel 12+)
$c = Collection::range(1, 5);
// [1, 2, 3, 4, 5]

$c = Collection::range(1, 10, 3);  // step of 3
// [1, 4, 7, 10]
```

## Extending Collections

```php
use Illuminate\Support\Collection;

// Register a macro once (typically in AppServiceProvider::boot())
Collection::macro('toUpper', function () {
    return $this->map(fn (string $value) => strtoupper($value));
});

// Usage
collect(['foo', 'bar'])->toUpper();
// ['FOO', 'BAR']

// Macro with arguments
Collection::macro('prefixed', function (string $prefix) {
    return $this->map(fn (string $value) => $prefix.$value);
});

collect(['a', 'b'])->prefixed('item_');
// ['item_a', 'item_b']
```

## Available Methods

### Filtering & Slicing

```php
// filter() — keep items where callback returns truthy (keeps keys)
collect([1, 2, 3, 4])->filter(fn (int $v) => $v > 2);
// [2 => 3, 3 => 4]

// reject() — inverse of filter
collect([1, 2, 3, 4])->reject(fn (int $v) => $v > 2);
// [0 => 1, 1 => 2]

// first() — first passing truth test, or first item
collect([1, 2, 3])->first(fn (int $v) => $v > 1);
// 2

collect([1, 2, 3])->first();
// 1

// firstOrFail() — same as first() but throws ItemNotFoundException
collect([1, 2, 3])->firstOrFail(fn (int $v) => $v > 2);
// 3

collect([1, 2, 3])->firstOrFail(fn (int $v) => $v > 5);
// throws Illuminate\Support\ItemNotFoundException

// firstWhere() — first item matching key/value
$data = collect([['name' => 'John', 'age' => 30], ['name' => 'Jane', 'age' => 25]]);
$data->firstWhere('name', 'Jane');
// ['name' => 'Jane', 'age' => 25]

// last() — last passing truth test, or last item
collect([1, 2, 3])->last(fn (int $v) => $v < 3);
// 2

// only() — items with specified keys
collect(['a' => 1, 'b' => 2, 'c' => 3])->only(['a', 'c']);
// ['a' => 1, 'c' => 3]

// except() — items excluding specified keys
collect(['a' => 1, 'b' => 2, 'c' => 3])->except(['a']);
// ['b' => 2, 'c' => 3]

// slice() — extract a portion with offset and optional length
collect([1, 2, 3, 4, 5])->slice(2, 2);
// [2 => 3, 3 => 4]

// skip() — skip N items from the beginning
collect([1, 2, 3, 4])->skip(2);
// [2 => 3, 3 => 4]

// skipUntil() — skip until callback returns true, then include everything
collect([1, 1, 2, 3])->skipUntil(fn (int $v) => $v >= 2);
// [2 => 2, 3 => 3]

// skipWhile() — skip while callback returns true, then include the rest
collect([1, 1, 2, 3])->skipWhile(fn (int $v) => $v === 1);
// [2 => 2, 3 => 3]

// take() — first N items (negative N takes from the end)
collect([1, 2, 3, 4])->take(2);
// [0 => 1, 1 => 2]

collect([1, 2, 3, 4])->take(-2);
// [2 => 3, 3 => 4]

// takeUntil() — take items until callback returns true, then stop
collect([1, 1, 2, 3])->takeUntil(fn (int $v) => $v >= 2);
// [0 => 1, 1 => 1]

// takeWhile() — take items while callback returns true, then stop
collect([1, 1, 2, 3])->takeWhile(fn (int $v) => $v === 1);
// [0 => 1, 1 => 1]

// where() — simple key/value filter (loose comparison)
$data = collect([['name' => 'John'], ['name' => 'Jane']]);
$data->where('name', 'John');
// [0 => ['name' => 'John']]

// whereStrict() — strict comparison (===)
$data->whereStrict('name', 'John');

// whereBetween() — where column is between two values
collect([['price' => 100], ['price' => 200], ['price' => 300]])
    ->whereBetween('price', [150, 250]);
// [1 => ['price' => 200]]

// whereNotBetween() — inverse of whereBetween
collect([['v' => 1], ['v' => 2], ['v' => 3]])->whereNotBetween('v', [1, 2]);
// [2 => ['v' => 3]]

// whereIn() — where value is in given array (loose)
collect([['v' => 1], ['v' => 2]])->whereIn('v', [1, 3]);
// [0 => ['v' => 1]]

// whereNotIn() — inverse of whereIn
collect([['v' => 1], ['v' => 2]])->whereNotIn('v', [1]);
// [1 => ['v' => 2]]

// whereInstanceOf() — filter by class
collect([new stdClass, new stdClass, new DateTime])
    ->whereInstanceOf(stdClass::class);
// [0 => stdClass, 1 => stdClass]

// whereNull() — items where key is null
collect([['a' => 1], ['a' => null]])->whereNull('a');
// [1 => ['a' => null]]

// whereNotNull() — items where key is not null
collect([['a' => 1], ['a' => null]])->whereNotNull('a');
// [0 => ['a' => 1]]
```

### Mapping & Transforming

```php
// map() — transform every item (returns keys from 0)
collect([1, 2, 3])->map(fn (int $v) => $v * 10);
// [0 => 10, 1 => 20, 2 => 30]

// mapInto() — instantiate class with each item as constructor arg
collect([1, 2])->mapInto(stdClass::class);
// [0 => stdClass {1}, 1 => stdClass {2}]

// mapSpread() — iterate over nested arrays, spread into callback
collect([[1, 2], [3, 4]])
    ->mapSpread(fn (int $a, int $b) => $a + $b);
// [0 => 3, 1 => 7]

// mapToGroups() — group by callback returning key/value pair
$data = collect([
    ['name' => 'John', 'dept' => 'Sales'],
    ['name' => 'Jane', 'dept' => 'Sales'],
    ['name' => 'Jim',  'dept' => 'Marketing'],
]);
$data->mapToGroups(fn (array $item) => [$item['dept'] => $item['name']]);
// ['Sales' => ['John', 'Jane'], 'Marketing' => ['Jim']]

// mapWithKeys() — map to new collection with custom keys
collect([['id' => 1, 'name' => 'John'], ['id' => 2, 'name' => 'Jane']])
    ->mapWithKeys(fn (array $item) => [$item['id'] => $item['name']]);
// [1 => 'John', 2 => 'Jane']

// flatMap() — map and flatten one level
collect([['name' => 'John'], ['name' => 'Jane']])
    ->flatMap(fn (array $item) => [$item['name'] => strtoupper($item['name'])]);
// ['John' => 'JOHN', 'Jane' => 'JANE']

// flatten() — flatten multi-dimensional array to a single level
collect([1, [2, [3, [4]]]])->flatten();
// [1, 2, 3, 4]

collect([1, [2, [3, [4]]]])->flatten(depth: 2);
// [1, 2, 3, [4]]

// collapse() — collapse array of arrays into a flat collection
collect([[1, 2], [3, 4], [5]])->collapse();
// [0 => 1, 1 => 2, 2 => 3, 3 => 4, 4 => 5]

// collapseWithKeys() — collapse while preserving original keys
collect([
    ['first'  => collect([1, 2, 3])],
    ['second' => [4, 5, 6]],
])->collapseWithKeys();
// ['first' => [1, 2, 3], 'second' => [4, 5, 6]]
```

### Testing Conditions

```php
// contains() — does any item pass? (loose comparison for values)
collect([1, 2, 3])->contains(fn (int $v) => $v > 2);
// true

collect(['name' => 'John'])->contains('John');
// true

collect([['name' => 'John']])->contains('name', 'John');
// true

// containsStrict() — same as contains but with strict comparison
collect([1, '1'])->containsStrict('1');
// true

collect([1, '1'])->containsStrict(1);
// true

// doesntContain() — does no item pass?
collect([1, 2, 3])->doesntContain(fn (int $v) => $v > 5);
// true

// doesntContainStrict() — strict version of doesntContain

// every() — does every item pass?
collect([2, 4, 6])->every(fn (int $v) => $v % 2 === 0);
// true

// some() — alias of contains()
collect([1, 2, 3])->some(fn (int $v) => $v === 2);
// true

// isEmpty() — is the collection empty?
collect([])->isEmpty();
// true

// isNotEmpty() — is the collection not empty?
collect([1])->isNotEmpty();
// true

// has() — do all given keys exist?
collect(['a' => 1, 'b' => 2])->has('a');
// true

collect(['a' => 1, 'b' => 2])->has(['a', 'b']);
// true

// hasAny() — does at least one key exist?
collect(['a' => 1])->hasAny(['a', 'b']);
// true

// hasSole() — does the collection contain exactly one item matching criteria?
collect([])->hasSole();
// false

collect([1])->hasSole();
// true

collect([1, 2, 3])->hasSole(fn (int $v) => $v === 2);
// true

// ensure() — assert all items are of a given type
collect([1, 2, 3])->ensure('int');
// [1, 2, 3]  (passes — returns the collection)

collect([1, 'a', 3])->ensure('int');
// throws UnexpectedValueException

collect($users)->ensure(User::class);
// passes if all items are User instances
```

### Searching & Retrieving

```php
// search() — find the first key matching value or callback
collect(['a' => 1, 'b' => 2])->search(2);
// 'b'

collect([1, 2, 3])->search(fn (int $v) => $v > 2);
// 2 (key)

// get() — retrieve value by key with optional default
collect(['a' => 1, 'b' => 2])->get('a');
// 1

collect(['a' => 1])->get('b', 0);
// 0

collect(['a' => 1])->get('b', fn () => 0);
// 0

// pluck() — extract values of a key, optionally keyed by another
$data = collect([
    ['id' => 1, 'name' => 'John'],
    ['id' => 2, 'name' => 'Jane'],
]);
$data->pluck('name');
// [0 => 'John', 1 => 'Jane']

$data->pluck('name', 'id');
// [1 => 'John', 2 => 'Jane']

// keys() — return all keys
collect(['a' => 1, 'b' => 2])->keys();
// ['a', 'b']

// values() — reset keys to sequential 0-based integers
collect(['a' => 1, 'b' => 2])->values();
// [0 => 1, 1 => 2]

// sole() — return exactly one item matching callback, throws if none or many
collect([1, 2, 3])->sole(fn (int $v) => $v === 2);
// 2

collect([1, 1])->sole(fn (int $v) => $v === 1);
// throws ItemNotFoundException (multiple matches)

// find() — return all items matching a truth test
collect([1, 2, 3, 4])->find(fn (int $v) => $v > 2);
// [2 => 3, 3 => 4]

// value() — get a single value from the first item by key
collect([['name' => 'John'], ['name' => 'Jane']])->value('name');
// 'John'

// random() — return one or more random items
collect([1, 2, 3, 4])->random();
// 3 (random)

collect([1, 2, 3, 4])->random(2);
// [2, 4] (random, collection)
```

### Sorting & Ordering

```php
// sort() — sort by value (keeps keys)
collect([3, 1, 2])->sort();
// [1 => 1, 2 => 2, 0 => 3]

// sortBy() — sort by key or callback
$data = collect([['name' => 'John'], ['name' => 'Jane']]);
$data->sortBy('name');
// [1 => ['name' => 'Jane'], 0 => ['name' => 'John']]

$data->sortBy(fn (array $item) => $item['name']);
// [1 => ['name' => 'Jane'], 0 => ['name' => 'John']]

// sortByDesc() — descending sortBy
$data->sortByDesc('name');
// [0 => ['name' => 'John'], 1 => ['name' => 'Jane']]

// sortDesc() — descending sort (same as sort()->reverse())
collect([3, 1, 2])->sortDesc();
// [2 => 3, 0 => 1, 1 => 2]  (values descending, keys preserved)

// sortKeys() — sort by keys
collect(['c' => 3, 'a' => 1, 'b' => 2])->sortKeys();
// ['a' => 1, 'b' => 2, 'c' => 3]

// sortKeysDesc() — descending sort by keys
collect(['a' => 1, 'c' => 3, 'b' => 2])->sortKeysDesc();
// ['c' => 3, 'b' => 2, 'a' => 1]

// sortKeysUsing() — sort by keys using a custom comparison
collect(['a' => 1, 'C' => 3, 'b' => 2])
    ->sortKeysUsing(strcasecmp(...));
// ['a' => 1, 'b' => 2, 'C' => 3]

// reverse() — reverse the order (keeps keys)
collect([1, 2, 3])->reverse();
// [2 => 3, 1 => 2, 0 => 1]
```

### Math

```php
// avg() / average() — average of values
collect([1, 2, 3])->avg();
// 2

collect([['price' => 10], ['price' => 20]])->avg('price');
// 15

// median() — median value
collect([1, 2, 3, 4, 5])->median();
// 3

collect([['price' => 10], ['price' => 20], ['price' => 30]])->median('price');
// 20

// mode() — most frequently occurring value(s)
collect([1, 1, 2, 3])->mode();
// [1]

collect([1, 1, 2, 2])->mode();
// [1, 2]

// min() — minimum value
collect([3, 1, 2])->min();
// 1

collect([['price' => 30], ['price' => 10]])->min('price');
// 10

// max() — maximum value
collect([3, 1, 2])->max();
// 3

// sum() — sum of values
collect([1, 2, 3])->sum();
// 6

collect([['price' => 10], ['price' => 20]])->sum('price');
// 30

// count() — number of items
collect([1, 2, 3])->count();
// 3

// countBy() — count occurrences of each value
collect([1, 1, 2, 2, 2, 3])->countBy();
// [1 => 2, 2 => 3, 3 => 1]

collect(['foo', 'bar', 'foo'])->countBy();
// ['foo' => 2, 'bar' => 1]

// percentage() — percentage of items passing a truth test (Laravel 12+)
collect([1, 1, 2, 2, 2, 3])->percentage(fn (int $v) => $v === 1);
// 33.33
```

### Aggregation & Reduction

```php
// reduce() — reduce to a single value
collect([1, 2, 3])->reduce(fn (int $carry, int $item) => $carry + $item, 0);
// 6

// reduceSpread() — reduce to multiple values using array destructuring
[$creditsRemaining, $batch] = collect($images)
    ->reduceSpread(
        fn (int $credits, Collection $batch, $image) => $image->requiresCredits()
            ? [$credits - 5, $batch->push($image)]
            : [$credits, $batch],
        $availableCredits,
        collect(),
    );

// pipe() — pass the collection to a closure, return the result
collect([1, 2, 3])->pipe(fn (Collection $c) => $c->sum());
// 6

// pipeInto() — create a new instance of a class with collection as constructor arg
collect([1, 2, 3])->pipeInto(ResourceCollection::class);
// ResourceCollection instance with $collection property

// pipeThrough() — pass collection through an array of pipes
collect([1, 2, 3])->pipeThrough([
    fn (Collection $c) => $c->merge([4, 5]),
    fn (Collection $c) => $c->sum(),
]);
// 15

// tap() — pass collection to a closure for side effects, return the collection
collect([1, 2, 3])->tap(function (Collection $c) {
    logger('Collection size: '.$c->count());
});
// [1, 2, 3] (unchanged)
```

### Set Operations

```php
// diff() — items not present in the given collection (value comparison)
collect([1, 2, 3])->diff([2, 4]);
// [0 => 1, 2 => 3]

// diffAssoc() — items whose key/value pairs differ
collect(['a' => 1, 'b' => 2])->diffAssoc(['a' => 1, 'b' => 3]);
// ['b' => 2]

// diffAssocUsing() — diffAssoc with a custom key comparison callback
collect(['a' => 1, 'B' => 2])->diffAssocUsing(
    ['a' => 1, 'b' => 3],
    strcasecmp(...),
);
// ['B' => 2]

// diffKeys() — items whose keys are not in the given collection
collect(['a' => 1, 'b' => 2])->diffKeys(['a' => 1, 'c' => 3]);
// ['b' => 2]

// intersect() — items present in both collections (value comparison)
collect([1, 2, 3])->intersect([2, 4]);
// [1 => 2]

// intersectUsing() — intersect with a custom value comparison callback
collect([1, 2, 3])->intersectUsing([2, 4], fn (int $a, int $b) => $a <=> $b);
// [1 => 2]

// intersectAssoc() — items whose key/value pairs match
collect(['a' => 1, 'b' => 2])->intersectAssoc(['a' => 1, 'b' => 3]);
// ['a' => 1]

// intersectAssocUsing() — intersectAssoc with custom key comparison
collect(['a' => 1, 'B' => 2])->intersectAssocUsing(
    ['a' => 1, 'b' => 3],
    strcasecmp(...),
);
// ['a' => 1]

// intersectByKeys() — items whose keys exist in the given collection
collect(['a' => 1, 'b' => 2])->intersectByKeys(['a' => 1, 'c' => 3]);
// ['a' => 1]

// unique() — unique values (loose comparison, keeps first occurrence)
collect([1, 1, 2, 3])->unique();
// [0 => 1, 2 => 2, 3 => 3]

collect([['name' => 'John'], ['name' => 'Jane'], ['name' => 'John']])
    ->unique('name');
// [0 => ['name' => 'John'], 1 => ['name' => 'Jane']]

// uniqueStrict() — same as unique but with strict (===) comparison

// duplicates() — retrieve duplicate values
collect(['a', 'b', 'a', 'c', 'b'])->duplicates();
// [2 => 'a', 4 => 'b']

// duplicatesStrict() — strict version of duplicates
```

### Arrays & Conversion

```php
// toArray() — convert collection to a plain PHP array
collect([1, 2, 3])->toArray();
// [1, 2, 3]

// toJson() — convert to JSON string
collect(['name' => 'John', 'age' => 30])->toJson();
// '{"name":"John","age":30}'

// toPrettyJson() — pretty-printed JSON (Laravel 12+)
collect(['name' => 'John'])->toPrettyJson();
// '{
//     "name": "John"
// }'

// all() — return the underlying array
collect([1, 2, 3])->all();
// [1, 2, 3]

// implode() — join items into a string
collect([1, 2, 3])->implode('-');
// '1-2-3'

collect([['product' => 'Desk'], ['product' => 'Chair']])
    ->implode('product', ', ');
// 'Desk, Chair'

// Using a closure as first argument (Laravel 12+)
collect([['product' => 'Desk'], ['product' => 'Chair']])
    ->implode(fn (array $item) => strtoupper($item['product']), ', ');
// 'DESK, CHAIR'

// join() — join items with separator, with final separator
collect(['a', 'b', 'c'])->join(', ');
// 'a, b, c'

collect(['a', 'b', 'c'])->join(', ', ' and ');
// 'a, b and c'

// dd() — dump and die
collect([1, 2, 3])->dd();
// dumps the collection and exits

// dump() — dump without dying
collect([1, 2, 3])->dump();
// dumps the collection, returns the collection
```

### Adding & Removing

```php
// push() — append an item
collect([1, 2])->push(3);
// [0 => 1, 1 => 2, 2 => 3]

// pop() — remove and return the last item
$c = collect([1, 2, 3]);
$last = $c->pop();
// $last = 3, $c = [1, 2]

// prepend() — add item to the beginning
collect([1, 2, 3])->prepend(0);
// [0 => 0, 1 => 1, 2 => 2, 3 => 3]

// With key
collect(['a' => 1])->prepend(0, 'z');
// ['z' => 0, 'a' => 1]

// pull() — remove and return a specific key
$c = collect(['a' => 1, 'b' => 2]);
$value = $c->pull('a');
// $value = 1, $c = ['b' => 2]

// put() — set a key/value pair
collect(['a' => 1])->put('b', 2);
// ['a' => 1, 'b' => 2]

// shift() — remove and return the first item
$c = collect([1, 2, 3]);
$first = $c->shift();
// $first = 1, $c = [1 => 2, 2 => 3]

// splice() — remove and return a slice, optionally replacing it
$c = collect([1, 2, 3, 4, 5]);
$removed = $c->splice(2, 2, [10, 11]);
// $removed = [3, 4], $c = [1, 2, 10, 11, 5]

// forget() — remove items by key
collect(['a' => 1, 'b' => 2])->forget('a');
// ['b' => 2]

// add() — add item only if key doesn't exist
collect(['a' => 1])->add('b', 2);
// ['a' => 1, 'b' => 2]

collect(['a' => 1])->add('a', 2);
// ['a' => 1]  (no-op, key already exists)
```

### Chunking & Splitting

```php
// chunk() — split into collections of given size
collect([1, 2, 3, 4, 5])->chunk(2);
// [[1, 2], [3, 4], [5]]  (collection of collections)

// chunkWhile() — chunk based on a callback
collect([1, 2, 3, 4, 5])->chunkWhile(
    fn (int $value, int $key, Collection $chunk) => $value <= 3,
);
// [[1, 2, 3], [4, 5]]

// split() — split into N equal-sized groups
collect([1, 2, 3, 4, 5])->split(3);
// [[1, 2], [3, 4], [5]]

// splitIn() — split into N groups distributing remaining items
collect([1, 2, 3, 4, 5])->splitIn(3);
// [[1, 2], [3, 4], [5]]

// sliding() — sliding window view
collect([1, 2, 3, 4, 5])->sliding(2);
// [[1, 2], [2, 3], [3, 4], [4, 5]]

collect([1, 2, 3, 4])->sliding(2, step: 2);
// [[1, 2], [3, 4]]

// nth() — every Nth item
collect([1, 2, 3, 4, 5])->nth(2);
// [0 => 1, 2 => 3, 4 => 5]

collect([1, 2, 3, 4, 5])->nth(2, offset: 1);
// [1 => 2, 3 => 4]

// forPage() — items for a given page number
collect(range(1, 20))->forPage(2, 5);
// [5 => 6, 6 => 7, 7 => 8, 8 => 9, 9 => 10]
```

### Combining & Merging

```php
// combine() — use one collection as keys, another as values
collect(['name', 'age'])->combine(['John', 30]);
// ['name' => 'John', 'age' => 30]

// concat() — append items from an array or collection
collect([1, 2])->concat([3, 4]);
// [0 => 1, 1 => 2, 2 => 3, 3 => 4]

// crossJoin() — cross join (Cartesian product)
collect([1, 2])->crossJoin(['a', 'b']);
// [[1, 'a'], [1, 'b'], [2, 'a'], [2, 'b']]

// merge() — merge arrays (numeric keys are appended, string keys overwrite)
collect(['a' => 1, 'b' => 2])->merge(['b' => 10]);
// ['a' => 1, 'b' => 10]

collect([1, 2])->merge([3, 4]);
// [0 => 1, 1 => 2, 2 => 3, 3 => 4]

// mergeRecursive() — recursive merge
collect(['a' => ['b' => 1]])->mergeRecursive(['a' => ['c' => 2]]);
// ['a' => ['b' => 1, 'c' => 2]]

// replace() — replace values at matching keys (works like array_replace)
collect(['a' => 1, 'b' => 2])->replace(['a' => 10, 'c' => 3]);
// ['a' => 10, 'b' => 2, 'c' => 3]

// replaceRecursive() — recursive version of replace
collect(['a' => ['b' => 1]])->replaceRecursive(['a' => ['b' => 10]]);
// ['a' => ['b' => 10]]

// union() — add items with keys not already present
collect(['a' => 1, 'b' => 2])->union(['b' => 20, 'c' => 30]);
// ['a' => 1, 'b' => 2, 'c' => 30]

// zip() — merge values from multiple collections element by element
collect([1, 2, 3])->zip([4, 5, 6], ['a', 'b', 'c']);
// [[1, 4, 'a'], [2, 5, 'b'], [3, 6, 'c']]
```

### Key Manipulation

```php
// keyBy() — key the collection by a given key
$data = collect([
    ['id' => 1, 'name' => 'John'],
    ['id' => 2, 'name' => 'Jane'],
]);
$data->keyBy('id');
// [1 => ['id' => 1, 'name' => 'John'], 2 => ['id' => 2, 'name' => 'Jane']]

// Using a callback
$data->keyBy(fn (array $item) => strtolower($item['name']));
// ['john' => ['id' => 1, 'name' => 'John'], 'jane' => ['id' => 2, 'name' => 'Jane']]

// flip() — swap keys and values
collect(['a' => 1, 'b' => 2])->flip();
// [1 => 'a', 2 => 'b']

// dot() — flatten multi-dimensional array into dot notation (aliases: flattenDot, collapse)
// Note: `dot()` is available via the Collection macro pattern; use `Arr::dot()` directly
// for ad-hoc usage outside of chainable methods in some versions.
collect(['user' => ['name' => 'John', 'profile' => ['age' => 30]]])->dot();
// ['user.name' => 'John', 'user.profile.age' => 30]

// undot() — expand dot notation keys back into nested arrays
collect(['user.name' => 'John', 'user.profile.age' => 30])->undot();
// ['user' => ['name' => 'John', 'profile' => ['age' => 30]]]
```

## Higher Order Messages

Collections support higher order messages — dynamic properties that shortcut common method calls. Available for: `average`, `avg`, `contains`, `each`, `every`, `filter`, `first`, `flatMap`, `groupBy`, `keyBy`, `map`, `max`, `min`, `partition`, `reject`, `skipUntil`, `skipWhile`, `some`, `sortBy`, `sortByDesc`, `sum`, `takeUntil`, `takeWhile`, `unique`.

```php
use App\Models\User;

$users = User::where('votes', '>', 500)->get();

// Without higher order message
$users->each(function (User $user) {
    $user->markAsVip();
});

// With higher order message
$users->each->markAsVip();

// Mapping a property
$names = $users->map->name->toArray();

// Sum of a property
$total = $users->sum->votes;
```

## Lazy Collections

`LazyCollection` extends the same `Enumerable` contract but loads items on-demand, making it ideal for processing large datasets without exhausting memory. Use generators or the `lazy()` method on an existing collection.

```php
use Illuminate\Support\LazyCollection;

// Using a generator
$lazy = LazyCollection::make(function () {
    $file = fopen('huge-file.csv', 'r');
    while (($line = fgets($file)) !== false) {
        yield $line;
    }
});

// Process without loading entire file into memory
$lazy->filter(fn (string $line) => str_contains($line, 'error'))
    ->take(100)
    ->each(fn (string $line) => logger($line));

// Convert a regular collection to lazy
$result = collect(range(1, 1_000_000))->lazy()
    ->filter(fn (int $v) => $v % 2 === 0)
    ->take(10)
    ->all();
// Only 10 items are ever materialized

// LazyCollection from a query builder
User::cursor()
    ->filter(fn (User $user) => $user->isActive())
    ->each(fn (User $user) => process($user));
```

## Enumerable Contract

Both `Collection` and `LazyCollection` implement the `Illuminate\Support\Enumerable` contract. This contract defines the shared API (all methods listed above) while allowing each class to determine its own execution strategy — eager for `Collection`, lazy for `LazyCollection`.

```php
use Illuminate\Support\Enumerable;
use Illuminate\Support\Collection;
use Illuminate\Support\LazyCollection;

// Type-hint against the contract when the execution strategy doesn't matter
function processItems(Enumerable $items): Enumerable
{
    return $items->filter(fn ($item) => $item->isValid())
        ->values();
}

// Accepts both Collection and LazyCollection
processItems(collect([1, 2, 3]));
processItems(LazyCollection::make(function () {
    yield 1;
    yield 2;
    yield 3;
}));
```

## Best Practices

1. **Prefer collections over raw arrays** — Fluent API, immutability, and method chaining reduce bugs
2. **Chain methods fluently** — Compose pipelines with `filter()` → `map()` → `values()` rather than nested loops
3. **Use `lazy()` for large datasets** — Avoid memory exhaustion when processing thousands of items
4. **Leverage higher order messages** — `$users->each->activate()` is clearer than `$users->each(fn ($u) => $u->activate())`
5. **Type-hint with `Enumerable`** — Accept `Enumerable` rather than `Collection` when lazy execution is acceptable
6. **Never mutate the original** — Collections are immutable; always assign the result to a new variable
7. **Use `ensure()` for defensive programming** — Validate item types early in pipelines
8. **Register macros sparingly** — Use `Collection::macro()` only for domain-specific operations used across the codebase
9. **Prefer `sole()` when expecting exactly one item** — It throws on zero or multiple matches, preventing silent bugs
10. **Use `percentage()` for readable proportions** — Avoid manual division operations in presentation logic
