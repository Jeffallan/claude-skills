# Async PHP Patterns

> Reference for: PHP Pro
> Load when: Swoole, ReactPHP, async, fibers, concurrency, streams

## Swoole HTTP Server

```php
<?php

declare(strict_types=1);

use Swoole\HTTP\Server;
use Swoole\HTTP\Request;
use Swoole\HTTP\Response;

$server = new Server('0.0.0.0', 9501);

$server->set([
    'worker_num' => 4,
    'max_request' => 10000,
    'task_worker_num' => 2,
    'enable_coroutine' => true,
]);

$server->on('start', function (Server $server) {
    echo "Swoole HTTP server started at http://0.0.0.0:9501\n";
});

$server->on('request', function (Request $request, Response $response) {
    $response->header('Content-Type', 'application/json');

    match ($request->server['request_uri']) {
        '/api/users' => handleUsers($request, $response),
        '/api/health' => $response->end(json_encode(['status' => 'healthy'])),
        default => $response->status(404)->end(json_encode(['error' => 'Not found'])),
    };
});

function handleUsers(Request $request, Response $response): void
{
    // Coroutine for concurrent DB queries
    go(function () use ($response) {
        $users = queryDatabase('SELECT * FROM users LIMIT 10');
        $response->end(json_encode(['data' => $users]));
    });
}

$server->start();
```

## Swoole Coroutines

```php
<?php

declare(strict_types=1);

use Swoole\Coroutine;
use Swoole\Coroutine\Http\Client;

// Concurrent HTTP requests
Coroutine\run(function () {
    $results = [];

    // Create multiple coroutines
    $wg = new Coroutine\WaitGroup();

    $urls = [
        'https://api.example.com/users',
        'https://api.example.com/posts',
        'https://api.example.com/comments',
    ];

    foreach ($urls as $url) {
        $wg->add();
        go(function () use ($url, &$results, $wg) {
            $client = new Client(parse_url($url, PHP_URL_HOST), 443, true);
            $client->set(['timeout' => 5]);
            $client->get(parse_url($url, PHP_URL_PATH));

            $results[$url] = [
                'status' => $client->statusCode,
                'body' => $client->body,
            ];

            $client->close();
            $wg->done();
        });
    }

    $wg->wait();

    print_r($results);
});
```

## Swoole Async MySQL

```php
<?php

declare(strict_types=1);

use Swoole\Coroutine;
use Swoole\Coroutine\MySQL;

Coroutine\run(function () {
    $mysql = new MySQL();

    $connected = $mysql->connect([
        'host' => '127.0.0.1',
        'port' => 3306,
        'user' => 'root',
        'password' => 'password',
        'database' => 'test',
    ]);

    if (!$connected) {
        throw new \RuntimeException($mysql->connect_error);
    }

    // Async query
    $result = $mysql->query('SELECT * FROM users WHERE active = 1');

    foreach ($result as $row) {
        echo "User: {$row['name']}\n";
    }

    // Prepared statements
    $stmt = $mysql->prepare('SELECT * FROM users WHERE id = ?');
    $stmt->execute([42]);
    $user = $stmt->fetchAll();

    $mysql->close();
});
```

## Swoole Channel (Communication)

```php
<?php

declare(strict_types=1);

use Swoole\Coroutine;
use Swoole\Coroutine\Channel;

Coroutine\run(function () {
    $channel = new Channel(10); // Buffer size: 10

    // Producer
    go(function () use ($channel) {
        for ($i = 1; $i <= 5; $i++) {
            $channel->push("Task {$i}");
            echo "Produced: Task {$i}\n";
            Coroutine::sleep(0.5);
        }
        $channel->close();
    });

    // Consumer
    go(function () use ($channel) {
        while (true) {
            $task = $channel->pop();
            if ($task === false && $channel->errCode === SWOOLE_CHANNEL_CLOSED) {
                break;
            }
            echo "Consumed: {$task}\n";
            Coroutine::sleep(1);
        }
    });
});
```

## ReactPHP Event Loop

```php
<?php

declare(strict_types=1);

require 'vendor/autoload.php';

use React\EventLoop\Loop;
use React\Http\Message\Response;
use Psr\Http\Message\ServerRequestInterface;

// HTTP Server
$server = new React\Http\HttpServer(function (ServerRequestInterface $request) {
    return new Response(
        200,
        ['Content-Type' => 'application/json'],
        json_encode([
            'method' => $request->getMethod(),
            'uri' => (string) $request->getUri(),
            'timestamp' => time(),
        ])
    );
});

$socket = new React\Socket\SocketServer('0.0.0.0:8080');
$server->listen($socket);

echo "Server running at http://0.0.0.0:8080\n";

// Periodic timer
Loop::addPeriodicTimer(5.0, function () {
    echo "Heartbeat: " . date('H:i:s') . "\n";
});

// One-time timer
Loop::addTimer(10.0, function () {
    echo "This runs once after 10 seconds\n";
});
```

## ReactPHP Async MySQL

```php
<?php

declare(strict_types=1);

require 'vendor/autoload.php';

use React\MySQL\Factory;
use React\MySQL\QueryResult;

$factory = new Factory();

$connection = $factory->createLazyConnection('root:password@localhost/database');

$connection->query('SELECT * FROM users WHERE active = 1')
    ->then(
        function (QueryResult $result) {
            echo "Found " . count($result->resultRows) . " users\n";
            foreach ($result->resultRows as $row) {
                echo "User: {$row['name']}\n";
            }
        },
        function (\Exception $error) {
            echo "Error: " . $error->getMessage() . "\n";
        }
    );

// Prepared statements
$connection->query('SELECT * FROM users WHERE id = ?', [42])
    ->then(function (QueryResult $result) {
        $user = $result->resultRows[0] ?? null;
        var_dump($user);
    });
```

## ReactPHP Promises

```php
<?php

declare(strict_types=1);

use React\Promise\Promise;
use React\Promise\Deferred;
use function React\Promise\all;

// Creating promises
function fetchUser(int $id): Promise
{
    $deferred = new Deferred();

    // Simulate async operation
    Loop::addTimer(1.0, function () use ($deferred, $id) {
        $deferred->resolve([
            'id' => $id,
            'name' => "User {$id}",
        ]);
    });

    return $deferred->promise();
}

// Using promises
fetchUser(42)
    ->then(function ($user) {
        echo "Got user: {$user['name']}\n";
        return fetchUserPosts($user['id']);
    })
    ->then(function ($posts) {
        echo "Got " . count($posts) . " posts\n";
    })
    ->catch(function (\Exception $error) {
        echo "Error: " . $error->getMessage() . "\n";
    });

// Parallel promises
all([
    fetchUser(1),
    fetchUser(2),
    fetchUser(3),
])->then(function ($users) {
    echo "Fetched " . count($users) . " users\n";
});
```

## PHP Fibers (Native PHP 8.1+)

```php
<?php

declare(strict_types=1);

// Simple async function using fibers
function async(callable $callback): Fiber
{
    return new Fiber($callback);
}

function await(Fiber $fiber): mixed
{
    if (!$fiber->isStarted()) {
        return $fiber->start();
    }
    if ($fiber->isTerminated()) {
        return $fiber->getReturn();
    }
    return $fiber->resume();
}

// Simulate async I/O
function fetchData(string $url): Fiber
{
    return async(function () use ($url) {
        echo "Fetching: {$url}\n";
        Fiber::suspend('pending');

        // Simulate network delay
        sleep(1);

        return "Data from {$url}";
    });
}

// Usage
$fiber1 = fetchData('https://api.example.com/users');
$fiber2 = fetchData('https://api.example.com/posts');

await($fiber1);
await($fiber2);

$result1 = await($fiber1);
$result2 = await($fiber2);

echo "{$result1}\n";
echo "{$result2}\n";
```

## Amphp Framework

```php
<?php

declare(strict_types=1);

require 'vendor/autoload.php';

use Amp\Http\Server\HttpServer;
use Amp\Http\Server\Request;
use Amp\Http\Server\Response;
use Amp\Http\Server\Router;
use Amp\Socket\Server as SocketServer;
use function Amp\async;
use function Amp\Future\await;

// HTTP Server with Amphp
$router = new Router();

$router->addRoute('GET', '/api/users', function (Request $request): Response {
    // Concurrent database queries
    $users = await([
        async(fn() => queryUsers()),
        async(fn() => queryUserStats()),
    ]);

    return new Response(
        status: 200,
        headers: ['content-type' => 'application/json'],
        body: json_encode(['users' => $users[0], 'stats' => $users[1]]),
    );
});

$server = new HttpServer(
    servers: [SocketServer::listen('0.0.0.0:8080')],
    requestHandler: $router,
);

$server->start();
```

## Quick Reference

| Technology | Use Case | Performance |
|------------|----------|-------------|
| Swoole | High-performance servers, WebSockets | Very High |
| ReactPHP | Event-driven apps, real-time | High |
| Amphp | Modern async framework | High |
| Fibers | Native async (PHP 8.1+) | Medium |
| Generators | Simple async patterns | Medium |

| Feature | Swoole | ReactPHP | Amphp |
|---------|--------|----------|-------|
| Coroutines | Yes | No (Promises) | Yes (Fibers) |
| HTTP Server | Built-in | Via package | Via package |
| WebSockets | Built-in | Via package | Via package |
| Extension | Required | Not required | Not required |
| Learning Curve | Medium | Low | Medium |
