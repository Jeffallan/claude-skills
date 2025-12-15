# Testing in Rust

> Reference for: Rust Engineer
> Load when: Unit tests, integration tests, property testing, benchmarks

## Unit Tests

```rust
// Tests in same file
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_addition() {
        assert_eq!(2 + 2, 4);
    }

    #[test]
    fn test_subtraction() {
        assert!(10 - 5 == 5);
    }

    #[test]
    #[should_panic(expected = "division by zero")]
    fn test_panic() {
        divide(10, 0);
    }

    #[test]
    fn test_result() -> Result<(), String> {
        let result = divide(10, 2)?;
        assert_eq!(result, 5);
        Ok(())
    }

    #[test]
    #[ignore]
    fn expensive_test() {
        // Run with: cargo test -- --ignored
    }
}

// Assertions
fn assert_examples() {
    assert!(true);
    assert_eq!(2 + 2, 4);
    assert_ne!(2 + 2, 5);

    // Custom messages
    assert!(value > 0, "Value must be positive, got {}", value);
    assert_eq!(result, expected, "Calculation failed");
}
```

## Doctests

```rust
/// Adds two numbers together.
///
/// # Examples
///
/// ```
/// use mylib::add;
///
/// let result = add(2, 3);
/// assert_eq!(result, 5);
/// ```
///
/// ```should_panic
/// use mylib::divide;
///
/// divide(10, 0);  // This will panic
/// ```
///
/// ```ignore
/// // This code won't compile but won't fail the test
/// let x = undefined_function();
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

## Integration Tests

```rust
// tests/integration_test.rs
use mylib;

#[test]
fn test_full_workflow() {
    let config = mylib::Config::new("test.conf");
    let result = mylib::process(&config);
    assert!(result.is_ok());
}

// tests/common/mod.rs - shared test utilities
pub fn setup() -> TestContext {
    TestContext {
        db: create_test_db(),
    }
}

// tests/another_test.rs
mod common;

#[test]
fn test_with_common() {
    let ctx = common::setup();
    // Use ctx...
}
```

## Test Organization

```rust
// Nested test modules
#[cfg(test)]
mod tests {
    use super::*;

    mod addition {
        use super::*;

        #[test]
        fn positive_numbers() {
            assert_eq!(add(2, 3), 5);
        }

        #[test]
        fn negative_numbers() {
            assert_eq!(add(-2, -3), -5);
        }
    }

    mod subtraction {
        use super::*;

        #[test]
        fn test_subtract() {
            assert_eq!(subtract(10, 5), 5);
        }
    }
}
```

## Test Fixtures and Setup

```rust
struct TestContext {
    temp_dir: std::path::PathBuf,
    db: Database,
}

impl TestContext {
    fn setup() -> Self {
        let temp_dir = std::env::temp_dir().join("test");
        std::fs::create_dir_all(&temp_dir).unwrap();

        Self {
            temp_dir,
            db: Database::connect_test(),
        }
    }
}

impl Drop for TestContext {
    fn drop(&mut self) {
        // Cleanup
        std::fs::remove_dir_all(&self.temp_dir).ok();
        self.db.disconnect();
    }
}

#[test]
fn test_with_fixture() {
    let ctx = TestContext::setup();
    // Test uses ctx...
    // Automatic cleanup via Drop
}
```

## Async Tests

```rust
use tokio;

#[tokio::test]
async fn test_async_function() {
    let result = async_operation().await;
    assert_eq!(result, 42);
}

#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn test_with_custom_runtime() {
    let result = concurrent_operation().await;
    assert!(result.is_ok());
}

// Testing async with timeout
#[tokio::test]
async fn test_with_timeout() {
    let timeout = std::time::Duration::from_secs(5);
    let result = tokio::time::timeout(timeout, slow_operation()).await;
    assert!(result.is_ok());
}
```

## Property-Based Testing (proptest)

```rust
use proptest::prelude::*;

// Simple property test
proptest! {
    #[test]
    fn test_reversing_twice_is_identity(ref s in ".*") {
        let reversed: String = s.chars().rev().collect();
        let double_reversed: String = reversed.chars().rev().collect();
        assert_eq!(s, &double_reversed);
    }
}

// Custom strategies
proptest! {
    #[test]
    fn test_addition_commutative(a in 0..1000i32, b in 0..1000i32) {
        assert_eq!(a + b, b + a);
    }

    #[test]
    fn test_vector_push_pop(
        ref v in prop::collection::vec(0..100i32, 0..100),
        item in 0..100i32
    ) {
        let mut v = v.clone();
        v.push(item);
        assert_eq!(v.pop(), Some(item));
    }
}

// Complex custom strategies
fn user_strategy() -> impl Strategy<Value = User> {
    (1..1000u64, "[a-z]{3,10}", "[a-z0-9.]+@[a-z]+\\.[a-z]+")
        .prop_map(|(id, name, email)| User { id, name, email })
}

proptest! {
    #[test]
    fn test_user_serialization(user in user_strategy()) {
        let json = serde_json::to_string(&user).unwrap();
        let deserialized: User = serde_json::from_str(&json).unwrap();
        assert_eq!(user, deserialized);
    }
}
```

## Mocking

```rust
// Using mockall
use mockall::*;
use mockall::predicate::*;

#[automock]
trait Database {
    fn get_user(&self, id: u64) -> Option<User>;
    fn save_user(&mut self, user: User) -> Result<(), Error>;
}

#[test]
fn test_with_mock() {
    let mut mock = MockDatabase::new();

    mock.expect_get_user()
        .with(eq(1))
        .times(1)
        .returning(|_| Some(User { id: 1, name: "Alice".to_string() }));

    mock.expect_save_user()
        .times(1)
        .returning(|_| Ok(()));

    // Use mock in test
    let user = mock.get_user(1);
    assert!(user.is_some());
}
```

## Benchmarks (Criterion)

```rust
// benches/my_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 1,
        1 => 1,
        n => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

fn criterion_benchmark(c: &mut Criterion) {
    c.bench_function("fib 20", |b| b.iter(|| fibonacci(black_box(20))));
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);

// Cargo.toml:
// [dev-dependencies]
// criterion = "0.5"
//
// [[bench]]
// name = "my_benchmark"
// harness = false
```

## Advanced Benchmarking

```rust
use criterion::{BenchmarkId, Criterion, criterion_group, criterion_main};

fn bench_multiple_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("sorting");

    for size in [10, 100, 1000, 10000].iter() {
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, &size| {
            b.iter_batched(
                || generate_random_vec(size),
                |mut v| v.sort(),
                criterion::BatchSize::SmallInput,
            );
        });
    }

    group.finish();
}

// Comparing implementations
fn bench_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("string_search");

    group.bench_function("naive", |b| {
        b.iter(|| naive_search(black_box("haystack"), black_box("needle")))
    });

    group.bench_function("optimized", |b| {
        b.iter(|| optimized_search(black_box("haystack"), black_box("needle")))
    });

    group.finish();
}

criterion_group!(benches, bench_multiple_sizes, bench_comparison);
criterion_main!(benches);
```

## Testing with External Resources

```rust
// Testing file I/O
#[test]
fn test_file_operations() {
    use std::io::Write;

    let temp_dir = std::env::temp_dir();
    let file_path = temp_dir.join("test_file.txt");

    // Write
    let mut file = std::fs::File::create(&file_path).unwrap();
    file.write_all(b"test content").unwrap();

    // Read
    let content = std::fs::read_to_string(&file_path).unwrap();
    assert_eq!(content, "test content");

    // Cleanup
    std::fs::remove_file(&file_path).unwrap();
}

// Testing with databases (using sqlx)
#[sqlx::test]
async fn test_database_operations(pool: sqlx::PgPool) -> sqlx::Result<()> {
    sqlx::query("INSERT INTO users (name) VALUES ($1)")
        .bind("Alice")
        .execute(&pool)
        .await?;

    let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
        .fetch_one(&pool)
        .await?;

    assert_eq!(count.0, 1);
    Ok(())
}
```

## Snapshot Testing

```rust
// Using insta crate
use insta::assert_snapshot;

#[test]
fn test_output_format() {
    let data = generate_complex_output();
    assert_snapshot!(data);
}

#[test]
fn test_json_output() {
    let json = serde_json::to_string_pretty(&get_data()).unwrap();
    assert_snapshot!(json);
}

// Run with: cargo insta test
// Review snapshots: cargo insta review
```

## Code Coverage

```rust
// Using tarpaulin
// cargo install cargo-tarpaulin
// cargo tarpaulin --out Html --output-dir coverage

// Using llvm-cov
// cargo install cargo-llvm-cov
// cargo llvm-cov --html
```

## Fuzzing

```rust
// Using cargo-fuzz
// cargo install cargo-fuzz
// cargo fuzz init

// fuzz/fuzz_targets/fuzz_target_1.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Ok(s) = std::str::from_utf8(data) {
        let _ = mylib::parse_input(s);
    }
});

// Run with: cargo fuzz run fuzz_target_1
```

## Best Practices

- Write tests alongside production code in #[cfg(test)] modules
- Use integration tests in tests/ directory for end-to-end testing
- Include doctests in documentation for examples that must work
- Use descriptive test names that explain what is being tested
- Test edge cases (empty inputs, max values, etc.)
- Use property-based testing for algorithmic code
- Benchmark performance-critical code with criterion
- Run tests in CI with cargo test --all-features
- Use cargo test -- --nocapture to see println! output
- Test error conditions with #[should_panic] or Result
- Mock external dependencies for unit tests
- Use test fixtures for complex setup/teardown
- Run clippy on test code too
- Measure code coverage and aim for high coverage
- Use fuzzing for security-critical parsers
- Test async code with tokio::test
- Use snapshot testing for complex output validation
