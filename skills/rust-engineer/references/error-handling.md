# Error Handling in Rust

## Result and Option Basics

```rust
// Result: operation that can fail
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// Option: value that might be absent
fn find_user(id: u64) -> Option<User> {
    if id == 1 {
        Some(User { id, name: "Alice".to_string() })
    } else {
        None
    }
}

// Using ? operator for propagation
fn calculate(a: f64, b: f64, c: f64) -> Result<f64, String> {
    let x = divide(a, b)?;  // Returns Err early if division fails
    let y = divide(x, c)?;
    Ok(y)
}
```

## Custom Error Types

```rust
use std::fmt;

// Manual error type
#[derive(Debug)]
enum AppError {
    NotFound(String),
    InvalidInput(String),
    DatabaseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
            AppError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            AppError::DatabaseError(msg) => write!(f, "Database error: {}", msg),
        }
    }
}

impl std::error::Error for AppError {}

// Usage
fn get_user(id: u64) -> Result<User, AppError> {
    if id == 0 {
        return Err(AppError::InvalidInput("ID cannot be zero".to_string()));
    }
    // ... fetch user
    Err(AppError::NotFound(format!("User {} not found", id)))
}
```

## Using thiserror

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum DataError {
    #[error("Data not found: {0}")]
    NotFound(String),

    #[error("Invalid ID: {id}, reason: {reason}")]
    InvalidId { id: u64, reason: String },

    #[error("IO error")]
    Io(#[from] std::io::Error),

    #[error("Parse error")]
    Parse(#[from] std::num::ParseIntError),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

// Usage with automatic conversions
fn read_config(path: &str) -> Result<Config, DataError> {
    let content = std::fs::read_to_string(path)?;  // Auto-converts io::Error
    let port: u16 = content.parse()?;  // Auto-converts ParseIntError
    Ok(Config { port })
}
```

## Using anyhow for Applications

```rust
use anyhow::{Result, Context, bail, ensure};

// Simple error handling for applications
fn process_file(path: &str) -> Result<()> {
    let content = std::fs::read_to_string(path)
        .context(format!("Failed to read file: {}", path))?;

    ensure!(!content.is_empty(), "File is empty");

    if content.len() > 1000 {
        bail!("File too large");
    }

    // Process content...
    Ok(())
}

// Adding context to errors
fn main() -> Result<()> {
    process_file("config.txt")
        .context("Failed to process configuration")?;
    Ok(())
}
```

## Option Combinators

```rust
// map: transform Option<T> to Option<U>
let num: Option<i32> = Some(5);
let doubled = num.map(|n| n * 2);  // Some(10)

// and_then: chain operations
let result = Some(5)
    .and_then(|n| if n > 0 { Some(n * 2) } else { None })
    .and_then(|n| Some(n + 1));  // Some(11)

// or: provide alternative
let value = None.or(Some(42));  // Some(42)

// unwrap_or: provide default
let value = None.unwrap_or(42);  // 42

// unwrap_or_else: compute default lazily
let value = None.unwrap_or_else(|| expensive_computation());

// filter: conditional None
let num = Some(5).filter(|&n| n > 10);  // None

// Pattern matching
match find_user(1) {
    Some(user) => println!("Found: {}", user.name),
    None => println!("User not found"),
}

// if let for simple cases
if let Some(user) = find_user(1) {
    println!("Found: {}", user.name);
}
```

## Result Combinators

```rust
// map: transform Ok value
let result: Result<i32, String> = Ok(5);
let doubled = result.map(|n| n * 2);  // Ok(10)

// map_err: transform error
let result: Result<i32, &str> = Err("error");
let mapped = result.map_err(|e| e.to_uppercase());  // Err("ERROR")

// and_then: chain fallible operations
fn parse_then_double(s: &str) -> Result<i32, std::num::ParseIntError> {
    s.parse::<i32>()
        .and_then(|n| Ok(n * 2))
}

// or_else: provide alternative computation
let result = Err("error").or_else(|_| Ok(42));  // Ok(42)

// unwrap_or: provide default
let value = Err("error").unwrap_or(42);  // 42

// expect: unwrap with custom panic message
let value = result.expect("Failed to parse number");

// Pattern matching
match divide(10.0, 2.0) {
    Ok(result) => println!("Result: {}", result),
    Err(e) => eprintln!("Error: {}", e),
}
```

## Error Conversion and From Trait

```rust
use std::io;
use std::num::ParseIntError;

#[derive(Debug)]
enum MyError {
    Io(io::Error),
    Parse(ParseIntError),
}

impl From<io::Error> for MyError {
    fn from(err: io::Error) -> Self {
        MyError::Io(err)
    }
}

impl From<ParseIntError> for MyError {
    fn from(err: ParseIntError) -> Self {
        MyError::Parse(err)
    }
}

// Now ? operator works with automatic conversion
fn read_and_parse(path: &str) -> Result<i32, MyError> {
    let content = std::fs::read_to_string(path)?;  // io::Error -> MyError
    let number = content.trim().parse()?;  // ParseIntError -> MyError
    Ok(number)
}
```

## Advanced Error Patterns

```rust
// Multiple error sources with Box<dyn Error>
use std::error::Error;

fn complex_operation() -> Result<String, Box<dyn Error>> {
    let file = std::fs::read_to_string("data.txt")?;
    let number: i32 = file.trim().parse()?;
    Ok(format!("Number: {}", number))
}

// Error with backtrace (nightly)
#[derive(Debug)]
struct DetailedError {
    message: String,
    backtrace: std::backtrace::Backtrace,
}

impl DetailedError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            backtrace: std::backtrace::Backtrace::capture(),
        }
    }
}

// Recoverable vs unrecoverable errors
fn might_fail(value: i32) -> Result<i32, String> {
    if value < 0 {
        Err("Negative value".to_string())  // Recoverable
    } else if value > 1000 {
        panic!("Value too large!");  // Unrecoverable
    } else {
        Ok(value * 2)
    }
}
```

## Try Blocks (Nightly)

```rust
#![feature(try_blocks)]

// Try block for localized error handling
let result: Result<i32, Box<dyn Error>> = try {
    let file = std::fs::read_to_string("config.txt")?;
    let num: i32 = file.trim().parse()?;
    num * 2
};
```

## Error Context Pattern

```rust
use thiserror::Error;

#[derive(Error, Debug)]
#[error("{message}")]
struct ContextError {
    message: String,
    #[source]
    source: Option<Box<dyn Error + Send + Sync>>,
}

impl ContextError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            source: None,
        }
    }

    fn with_source(mut self, source: impl Error + Send + Sync + 'static) -> Self {
        self.source = Some(Box::new(source));
        self
    }
}

// Extension trait for adding context
trait Context<T> {
    fn context(self, message: impl Into<String>) -> Result<T, ContextError>;
}

impl<T, E: Error + Send + Sync + 'static> Context<T> for Result<T, E> {
    fn context(self, message: impl Into<String>) -> Result<T, ContextError> {
        self.map_err(|e| ContextError::new(message).with_source(e))
    }
}
```

## Best Practices

- Use Result for recoverable errors, panic! for unrecoverable bugs
- Prefer ? operator over unwrap() in production code
- Use expect() with descriptive messages instead of unwrap()
- Use thiserror for libraries (structured errors)
- Use anyhow for applications (simple error handling)
- Implement std::error::Error trait for custom error types
- Add context to errors as they propagate up the stack
- Use #[from] in thiserror for automatic conversions
- Document error conditions in function documentation
- Use Option::ok_or() to convert Option to Result
- Use Result::ok() to convert Result to Option (discarding error)
- Avoid String as error type (use custom types instead)
- Use ensure! and bail! from anyhow for cleaner checks
- Log errors at boundaries, return them in library code
