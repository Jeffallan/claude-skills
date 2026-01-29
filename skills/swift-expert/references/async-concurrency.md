# Async/Await Concurrency

## Async/Await Basics

```swift
// Async function
func fetchUser(id: Int) async throws -> User {
    let url = URL(string: "https://api.example.com/users/\(id)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Calling async functions
func loadUserData() async {
    do {
        let user = try await fetchUser(id: 123)
        print("Loaded: \(user.name)")
    } catch {
        print("Error: \(error)")
    }
}

// Multiple concurrent operations
func fetchMultipleUsers(ids: [Int]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask {
                try await fetchUser(id: id)
            }
        }

        var users: [User] = []
        for try await user in group {
            users.append(user)
        }
        return users
    }
}
```

## Actors

```swift
// Actor for thread-safe state management
actor UserCache {
    private var cache: [Int: User] = [:]
    private var inProgress: [Int: Task<User, Error>] = [:]

    func user(id: Int) async throws -> User {
        // Check cache first
        if let cached = cache[id] {
            return cached
        }

        // Check if already loading
        if let task = inProgress[id] {
            return try await task.value
        }

        // Start new load
        let task = Task {
            try await fetchUser(id: id)
        }
        inProgress[id] = task

        do {
            let user = try await task.value
            cache[id] = user
            inProgress.removeValue(forKey: id)
            return user
        } catch {
            inProgress.removeValue(forKey: id)
            throw error
        }
    }

    func clearCache() {
        cache.removeAll()
    }
}

// Usage
let cache = UserCache()
let user = try await cache.user(id: 123)
```

## MainActor

```swift
// UI updates must happen on main thread
@MainActor
class ViewModel: ObservableObject {
    @Published var users: [User] = []
    @Published var isLoading = false

    func loadUsers() async {
        isLoading = true
        defer { isLoading = false }

        do {
            // This async work happens off main thread
            let loadedUsers = try await fetchMultipleUsers(ids: [1, 2, 3])

            // Property updates happen on main thread automatically
            users = loadedUsers
        } catch {
            print("Error: \(error)")
        }
    }
}

// Isolated functions
@MainActor
func updateUI() {
    // This always runs on main thread
}

// Non-isolated functions in MainActor type
@MainActor
class DataManager {
    var data: [String] = []

    // Runs on main thread
    func updateData(_ newData: [String]) {
        data = newData
    }

    // Can run on any thread
    nonisolated func processData(_ input: String) -> String {
        return input.uppercased()
    }
}
```

## Structured Concurrency

```swift
// Task groups for dynamic concurrency
func downloadImages(urls: [URL]) async throws -> [UIImage] {
    try await withThrowingTaskGroup(of: (Int, UIImage).self) { group in
        for (index, url) in urls.enumerated() {
            group.addTask {
                let (data, _) = try await URLSession.shared.data(from: url)
                guard let image = UIImage(data: data) else {
                    throw ImageError.invalidData
                }
                return (index, image)
            }
        }

        var images = [UIImage?](repeating: nil, count: urls.count)
        for try await (index, image) in group {
            images[index] = image
        }

        return images.compactMap { $0 }
    }
}

// Parallel async-let
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser(id: currentUserID)
    async let posts = fetchPosts()
    async let notifications = fetchNotifications()

    return try await Dashboard(
        user: user,
        posts: posts,
        notifications: notifications
    )
}
```

## Task Management

```swift
// Detached tasks
func backgroundWork() {
    Task.detached(priority: .background) {
        // Runs independently, doesn't inherit context
        await performHeavyComputation()
    }
}

// Cancellation
class DataLoader {
    private var loadTask: Task<Void, Never>?

    func startLoading() {
        loadTask?.cancel()

        loadTask = Task {
            do {
                for try await item in itemStream() {
                    // Check for cancellation
                    try Task.checkCancellation()

                    await process(item)

                    // Alternative cancellation check
                    if Task.isCancelled {
                        break
                    }
                }
            } catch is CancellationError {
                print("Task cancelled")
            } catch {
                print("Error: \(error)")
            }
        }
    }

    func stopLoading() {
        loadTask?.cancel()
        loadTask = nil
    }
}

// Task priorities
Task(priority: .high) {
    await criticalWork()
}

Task(priority: .low) {
    await backgroundWork()
}
```

## AsyncSequence

```swift
// Custom AsyncSequence
struct NumberSequence: AsyncSequence {
    typealias Element = Int
    let range: Range<Int>

    struct AsyncIterator: AsyncIteratorProtocol {
        var current: Int
        let end: Int

        mutating func next() async -> Int? {
            guard current < end else { return nil }

            // Simulate async work
            try? await Task.sleep(for: .milliseconds(100))

            defer { current += 1 }
            return current
        }
    }

    func makeAsyncIterator() -> AsyncIterator {
        AsyncIterator(current: range.lowerBound, end: range.upperBound)
    }
}

// Usage
for await number in NumberSequence(range: 0..<10) {
    print(number)
}

// Async stream
func eventStream() -> AsyncStream<Event> {
    AsyncStream { continuation in
        let observer = NotificationCenter.default.addObserver(
            forName: .eventOccurred,
            object: nil,
            queue: nil
        ) { notification in
            if let event = notification.object as? Event {
                continuation.yield(event)
            }
        }

        continuation.onTermination = { _ in
            NotificationCenter.default.removeObserver(observer)
        }
    }
}
```

## Sendable Protocol

```swift
// Sendable types can be safely passed across concurrency domains
struct User: Sendable {
    let id: Int
    let name: String
}

// Non-Sendable by default (has mutable state)
class ViewModel {
    var data: [String] = []
}

// Make it Sendable with @unchecked (use carefully!)
class SafeViewModel: @unchecked Sendable {
    private let lock = NSLock()
    private var _data: [String] = []

    var data: [String] {
        lock.lock()
        defer { lock.unlock() }
        return _data
    }

    func setData(_ newData: [String]) {
        lock.lock()
        defer { lock.unlock() }
        _data = newData
    }
}

// Generic with Sendable constraint
func processData<T: Sendable>(_ data: T) async -> T {
    // Can safely pass data across concurrency boundaries
    await Task.detached {
        return data
    }.value
}
```

## Continuations

```swift
// Bridging callback-based APIs to async/await
func fetchDataAsync() async throws -> Data {
    try await withCheckedThrowingContinuation { continuation in
        fetchDataWithCallback { result in
            switch result {
            case .success(let data):
                continuation.resume(returning: data)
            case .failure(let error):
                continuation.resume(throwing: error)
            }
        }
    }
}

// Unsafe continuations for performance-critical code
func unsafeFetchDataAsync() async -> Data {
    await withUnsafeContinuation { continuation in
        fetchDataWithCallback { data in
            continuation.resume(returning: data)
        }
    }
}
```

## Best Practices

- Use actors for mutable shared state
- Prefer async/await over completion handlers
- Use MainActor for UI-related code
- Leverage structured concurrency (task groups, async-let)
- Check for cancellation in long-running tasks
- Mark types as Sendable when safe
- Use continuations to bridge legacy async code
- Avoid blocking in async contexts
- Use Task.detached sparingly (breaks structured concurrency)
