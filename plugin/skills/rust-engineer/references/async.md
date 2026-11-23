# Async Programming in Rust

## Basic Async/Await

```rust
use tokio;

// Async function returns a Future
async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    let body = response.text().await?;
    Ok(body)
}

// Tokio runtime
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let data = fetch_data("https://api.example.com").await?;
    println!("Data: {}", data);
    Ok(())
}

// Manual runtime creation
fn main() {
    let runtime = tokio::runtime::Runtime::new().unwrap();
    runtime.block_on(async {
        println!("Hello from async context");
    });
}
```

## Concurrent Execution

```rust
use tokio;

// Sequential execution
async fn sequential() {
    let result1 = async_operation1().await;
    let result2 = async_operation2().await;  // Waits for operation1
}

// Concurrent execution with join!
async fn concurrent() {
    let (result1, result2) = tokio::join!(
        async_operation1(),
        async_operation2()
    );
}

// Concurrent with try_join! (stops on first error)
async fn concurrent_with_errors() -> Result<(), Box<dyn std::error::Error>> {
    let (result1, result2) = tokio::try_join!(
        fallible_operation1(),
        fallible_operation2()
    )?;
    Ok(())
}

// Spawning tasks
async fn spawn_tasks() {
    let handle1 = tokio::spawn(async {
        // This runs on a separate task
        expensive_computation().await
    });

    let handle2 = tokio::spawn(async {
        another_computation().await
    });

    // Wait for both to complete
    let result1 = handle1.await.unwrap();
    let result2 = handle2.await.unwrap();
}
```

## Select and Race Conditions

```rust
use tokio::time::{sleep, Duration};

// select! - wait for first to complete
async fn first_to_complete() {
    tokio::select! {
        result = async_operation1() => {
            println!("Operation 1 completed first: {:?}", result);
        }
        result = async_operation2() => {
            println!("Operation 2 completed first: {:?}", result);
        }
    }
}

// Timeout pattern
async fn with_timeout() -> Result<String, &'static str> {
    tokio::select! {
        result = fetch_data("https://api.example.com") => {
            result.map_err(|_| "Fetch failed")
        }
        _ = sleep(Duration::from_secs(5)) => {
            Err("Timeout")
        }
    }
}

// Cancellation with select!
async fn cancellable_operation(mut cancel_rx: tokio::sync::watch::Receiver<bool>) {
    tokio::select! {
        result = long_running_task() => {
            println!("Task completed: {:?}", result);
        }
        _ = cancel_rx.changed() => {
            println!("Task cancelled");
        }
    }
}
```

## Streams

```rust
use tokio_stream::{self as stream, StreamExt};

// Creating streams
async fn stream_example() {
    let mut stream = stream::iter(vec![1, 2, 3, 4, 5]);

    while let Some(value) = stream.next().await {
        println!("Value: {}", value);
    }
}

// Stream combinators
async fn stream_combinators() {
    let stream = stream::iter(vec![1, 2, 3, 4, 5])
        .filter(|x| *x % 2 == 0)
        .map(|x| x * 2);

    let results: Vec<_> = stream.collect().await;
    println!("Results: {:?}", results);
}

// Async stream processing
use futures::stream::{self, StreamExt};

async fn process_stream() {
    let stream = stream::iter(vec![1, 2, 3, 4, 5])
        .then(|x| async move {
            tokio::time::sleep(Duration::from_millis(100)).await;
            x * 2
        });

    stream.for_each(|x| async move {
        println!("Processed: {}", x);
    }).await;
}
```

## Channels for Communication

```rust
use tokio::sync::{mpsc, oneshot, broadcast, watch};

// mpsc: multiple producer, single consumer
async fn mpsc_example() {
    let (tx, mut rx) = mpsc::channel(32);

    tokio::spawn(async move {
        tx.send("Hello").await.unwrap();
        tx.send("World").await.unwrap();
    });

    while let Some(msg) = rx.recv().await {
        println!("Received: {}", msg);
    }
}

// oneshot: single value, one-time use
async fn oneshot_example() {
    let (tx, rx) = oneshot::channel();

    tokio::spawn(async move {
        tx.send("Result").unwrap();
    });

    let result = rx.await.unwrap();
    println!("Got: {}", result);
}

// broadcast: multiple producers, multiple consumers
async fn broadcast_example() {
    let (tx, mut rx1) = broadcast::channel(16);
    let mut rx2 = tx.subscribe();

    tokio::spawn(async move {
        tx.send("Message").unwrap();
    });

    println!("rx1: {}", rx1.recv().await.unwrap());
    println!("rx2: {}", rx2.recv().await.unwrap());
}

// watch: single producer, multiple consumers (last value)
async fn watch_example() {
    let (tx, mut rx) = watch::channel("initial");

    tokio::spawn(async move {
        loop {
            rx.changed().await.unwrap();
            println!("Value changed to: {}", *rx.borrow());
        }
    });

    tx.send("updated").unwrap();
}
```

## Shared State

```rust
use std::sync::Arc;
use tokio::sync::{Mutex, RwLock};

// Mutex for exclusive access
async fn mutex_example() {
    let data = Arc::new(Mutex::new(0));

    let mut handles = vec![];

    for _ in 0..10 {
        let data = Arc::clone(&data);
        let handle = tokio::spawn(async move {
            let mut lock = data.lock().await;
            *lock += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.await.unwrap();
    }

    println!("Final value: {}", *data.lock().await);
}

// RwLock for read-write patterns
async fn rwlock_example() {
    let data = Arc::new(RwLock::new(vec![1, 2, 3]));

    // Multiple readers
    let data1 = Arc::clone(&data);
    tokio::spawn(async move {
        let read = data1.read().await;
        println!("Read: {:?}", *read);
    });

    let data2 = Arc::clone(&data);
    tokio::spawn(async move {
        let read = data2.read().await;
        println!("Read: {:?}", *read);
    });

    // Single writer
    tokio::time::sleep(Duration::from_millis(100)).await;
    let mut write = data.write().await;
    write.push(4);
}
```

## Async Traits (with async-trait)

```rust
use async_trait::async_trait;

#[async_trait]
trait AsyncRepository {
    async fn find_by_id(&self, id: u64) -> Result<User, Error>;
    async fn save(&self, user: User) -> Result<(), Error>;
}

struct DatabaseRepository {
    pool: sqlx::PgPool,
}

#[async_trait]
impl AsyncRepository for DatabaseRepository {
    async fn find_by_id(&self, id: u64) -> Result<User, Error> {
        sqlx::query_as("SELECT * FROM users WHERE id = $1")
            .bind(id)
            .fetch_one(&self.pool)
            .await
            .map_err(Into::into)
    }

    async fn save(&self, user: User) -> Result<(), Error> {
        sqlx::query("INSERT INTO users (name, email) VALUES ($1, $2)")
            .bind(&user.name)
            .bind(&user.email)
            .execute(&self.pool)
            .await?;
        Ok(())
    }
}
```

## Pin and Futures

```rust
use std::pin::Pin;
use std::future::Future;
use std::task::{Context, Poll};

// Manual Future implementation
struct DelayedValue {
    value: i32,
    delay: tokio::time::Sleep,
}

impl Future for DelayedValue {
    type Output = i32;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        match Pin::new(&mut self.delay).poll(cx) {
            Poll::Ready(_) => Poll::Ready(self.value),
            Poll::Pending => Poll::Pending,
        }
    }
}

// Using pinned futures
async fn use_pinned() {
    let future = DelayedValue {
        value: 42,
        delay: tokio::time::sleep(Duration::from_secs(1)),
    };

    let result = future.await;
    println!("Result: {}", result);
}
```

## Background Tasks and Graceful Shutdown

```rust
use tokio::signal;

async fn background_task(mut shutdown: tokio::sync::watch::Receiver<bool>) {
    loop {
        tokio::select! {
            _ = tokio::time::sleep(Duration::from_secs(1)) => {
                println!("Background task running...");
            }
            _ = shutdown.changed() => {
                println!("Shutting down background task");
                break;
            }
        }
    }
}

#[tokio::main]
async fn main() {
    let (shutdown_tx, shutdown_rx) = tokio::sync::watch::channel(false);

    let task = tokio::spawn(background_task(shutdown_rx));

    // Wait for ctrl-c
    signal::ctrl_c().await.unwrap();
    println!("Received shutdown signal");

    // Signal shutdown
    shutdown_tx.send(true).unwrap();

    // Wait for task to complete
    task.await.unwrap();
}
```

## Error Handling in Async

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum AsyncError {
    #[error("Network error: {0}")]
    Network(#[from] reqwest::Error),

    #[error("Timeout")]
    Timeout,

    #[error("Task failed")]
    TaskFailed(#[from] tokio::task::JoinError),
}

async fn robust_operation() -> Result<String, AsyncError> {
    let timeout = Duration::from_secs(5);

    let result = tokio::time::timeout(timeout, async {
        reqwest::get("https://api.example.com")
            .await?
            .text()
            .await
    })
    .await
    .map_err(|_| AsyncError::Timeout)??;

    Ok(result)
}
```

## Runtime Configuration

```rust
// Custom runtime configuration
fn main() {
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(4)
        .thread_name("my-worker")
        .thread_stack_size(3 * 1024 * 1024)
        .enable_all()
        .build()
        .unwrap();

    runtime.block_on(async {
        println!("Running on custom runtime");
    });
}

// Current-thread runtime (single-threaded)
fn single_threaded() {
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();

    runtime.block_on(async {
        println!("Single-threaded async");
    });
}
```

## Best Practices

- Use tokio::spawn for CPU-bound tasks on multi-threaded runtime
- Use spawn_blocking for blocking operations (file I/O, sync code)
- Prefer tokio::sync primitives over std::sync in async code
- Use channels for task communication instead of shared state when possible
- Always handle JoinHandle results (tasks can panic)
- Use select! for cancellation patterns
- Avoid holding locks across .await points
- Use timeout for all external I/O operations
- Implement graceful shutdown with channels
- Use async-trait for trait-based async code
- Prefer try_join! over manual error handling
- Use Arc<Mutex<T>> sparingly (channels often better)
- Test async code with tokio::test macro
- Monitor task spawning to prevent unbounded growth
