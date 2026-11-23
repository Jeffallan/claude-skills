# Traits, Generics, and Type System

## Basic Trait Definition

```rust
// Simple trait
trait Drawable {
    fn draw(&self);
}

// Trait with default implementation
trait Describable {
    fn describe(&self) -> String {
        String::from("No description available")
    }
}

// Implementing traits
struct Circle {
    radius: f64,
}

impl Drawable for Circle {
    fn draw(&self) {
        println!("Drawing circle with radius {}", self.radius);
    }
}

impl Describable for Circle {
    fn describe(&self) -> String {
        format!("A circle with radius {}", self.radius)
    }
}
```

## Associated Types

```rust
// Associated types vs generic parameters
trait Container {
    type Item;

    fn add(&mut self, item: Self::Item);
    fn get(&self, index: usize) -> Option<&Self::Item>;
}

impl Container for Vec<i32> {
    type Item = i32;

    fn add(&mut self, item: i32) {
        self.push(item);
    }

    fn get(&self, index: usize) -> Option<&i32> {
        self.get(index)
    }
}

// Iterator trait (standard library example)
trait MyIterator {
    type Item;

    fn next(&mut self) -> Option<Self::Item>;
}
```

## Generic Traits and Bounds

```rust
// Generic trait with multiple bounds
fn print_info<T>(item: &T)
where
    T: std::fmt::Display + std::fmt::Debug,
{
    println!("Display: {}", item);
    println!("Debug: {:?}", item);
}

// Generic struct with trait bounds
struct Pair<T: PartialOrd> {
    first: T,
    second: T,
}

impl<T: PartialOrd> Pair<T> {
    fn new(first: T, second: T) -> Self {
        Self { first, second }
    }

    fn larger(&self) -> &T {
        if self.first > self.second {
            &self.first
        } else {
            &self.second
        }
    }
}

// Blanket implementation
trait MyTrait {
    fn do_something(&self);
}

impl<T: std::fmt::Display> MyTrait for T {
    fn do_something(&self) {
        println!("Value: {}", self);
    }
}
```

## Trait Objects (Dynamic Dispatch)

```rust
// Static dispatch (monomorphization)
fn static_dispatch<T: Drawable>(item: &T) {
    item.draw();
}

// Dynamic dispatch (trait objects)
fn dynamic_dispatch(item: &dyn Drawable) {
    item.draw();
}

// Storing trait objects
struct Canvas {
    shapes: Vec<Box<dyn Drawable>>,
}

impl Canvas {
    fn new() -> Self {
        Self { shapes: Vec::new() }
    }

    fn add_shape(&mut self, shape: Box<dyn Drawable>) {
        self.shapes.push(shape);
    }

    fn draw_all(&self) {
        for shape in &self.shapes {
            shape.draw();
        }
    }
}

// Object safety: traits must meet criteria
trait ObjectSafe {
    fn method(&self);  // OK: takes &self
}

trait NotObjectSafe {
    fn generic<T>(&self);  // NOT OK: generic method
    fn by_value(self);     // NOT OK: takes self by value
}
```

## Derive Macros

```rust
// Standard derive macros
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct User {
    id: u64,
    name: String,
}

// Deriving more traits
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct Point {
    x: i32,
    y: i32,
}

// Custom derive with serde
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    host: String,
    port: u16,
}
```

## Advanced Trait Patterns

```rust
// Extension trait pattern
trait StringExt {
    fn truncate_to(&self, max_len: usize) -> String;
}

impl StringExt for str {
    fn truncate_to(&self, max_len: usize) -> String {
        if self.len() <= max_len {
            self.to_string()
        } else {
            format!("{}...", &self[..max_len])
        }
    }
}

// Sealed trait pattern (prevent external implementation)
mod sealed {
    pub trait Sealed {}
}

pub trait MySealed: sealed::Sealed {
    fn method(&self);
}

struct MyType;
impl sealed::Sealed for MyType {}
impl MySealed for MyType {
    fn method(&self) {
        println!("Implemented");
    }
}

// Supertraits
trait Printable {
    fn print(&self);
}

trait Loggable: Printable {  // Supertrait: must also impl Printable
    fn log(&self) {
        self.print();  // Can call supertrait methods
    }
}
```

## Associated Constants

```rust
trait Config {
    const MAX_SIZE: usize;
    const DEFAULT_TIMEOUT: u64;
}

struct ServerConfig;

impl Config for ServerConfig {
    const MAX_SIZE: usize = 1024;
    const DEFAULT_TIMEOUT: u64 = 30;
}

fn use_config<T: Config>() {
    println!("Max size: {}", T::MAX_SIZE);
}
```

## Generic Associated Types (GATs)

```rust
// GATs allow generics in associated types
trait LendingIterator {
    type Item<'a> where Self: 'a;

    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
}

struct WindowsMut<'data, T> {
    data: &'data mut [T],
    index: usize,
}

impl<'data, T> LendingIterator for WindowsMut<'data, T> {
    type Item<'a> = &'a mut [T] where Self: 'a;

    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>> {
        if self.index >= self.data.len() {
            return None;
        }

        let start = self.index;
        self.index += 2;

        Some(&mut self.data[start..start.min(self.data.len())])
    }
}
```

## Marker Traits

```rust
use std::marker::{PhantomData, Send, Sync};

// Send: type can be transferred across thread boundaries
// Sync: type can be shared between threads (&T is Send)

// Custom marker trait
trait Trusted {}

struct TrustedData<T> {
    data: T,
    _marker: PhantomData<T>,
}

impl<T: Trusted> TrustedData<T> {
    fn new(data: T) -> Self {
        Self {
            data,
            _marker: PhantomData,
        }
    }
}
```

## Operator Overloading

```rust
use std::ops::{Add, Mul};

#[derive(Debug, Clone, Copy)]
struct Vector2D {
    x: f64,
    y: f64,
}

impl Add for Vector2D {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

impl Mul<f64> for Vector2D {
    type Output = Self;

    fn mul(self, scalar: f64) -> Self {
        Self {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

// Usage
let v1 = Vector2D { x: 1.0, y: 2.0 };
let v2 = Vector2D { x: 3.0, y: 4.0 };
let v3 = v1 + v2;
let v4 = v1 * 2.5;
```

## From/Into Conversion Traits

```rust
struct UserId(u64);

impl From<u64> for UserId {
    fn from(id: u64) -> Self {
        UserId(id)
    }
}

// Into is automatically implemented
fn accept_user_id(id: impl Into<UserId>) {
    let user_id = id.into();
    println!("User ID: {}", user_id.0);
}

// TryFrom for fallible conversions
use std::convert::TryFrom;

impl TryFrom<i64> for UserId {
    type Error = &'static str;

    fn try_from(value: i64) -> Result<Self, Self::Error> {
        if value < 0 {
            Err("User ID cannot be negative")
        } else {
            Ok(UserId(value as u64))
        }
    }
}
```

## Const Traits (Nightly)

```rust
// Const trait implementations (requires nightly)
#![feature(const_trait_impl)]

#[const_trait]
trait ConstAdd {
    fn add(self, other: Self) -> Self;
}

impl const ConstAdd for i32 {
    fn add(self, other: Self) -> Self {
        self + other
    }
}

const fn compute() -> i32 {
    5.add(10)  // Can use in const context
}
```

## Best Practices

- Prefer associated types when there's one clear type per implementation
- Use generic parameters when multiple types might be used simultaneously
- Keep traits small and focused (single responsibility)
- Use extension traits to add functionality to existing types
- Document trait requirements and invariants
- Use marker traits for compile-time guarantees
- Prefer static dispatch for performance, dynamic dispatch for flexibility
- Use #[derive] when possible instead of manual implementations
- Implement standard traits (Debug, Clone, etc.) for better ecosystem integration
- Use sealed traits to prevent external implementations when needed
