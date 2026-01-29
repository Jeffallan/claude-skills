# Testing Patterns

## XCTest Basics

```swift
import XCTest
@testable import MyApp

final class UserTests: XCTestCase {
    var sut: UserManager!

    override func setUp() {
        super.setUp()
        sut = UserManager()
    }

    override func tearDown() {
        sut = nil
        super.tearDown()
    }

    func testUserCreation() {
        // Given
        let name = "John Doe"
        let email = "john@example.com"

        // When
        let user = sut.createUser(name: name, email: email)

        // Then
        XCTAssertEqual(user.name, name)
        XCTAssertEqual(user.email, email)
        XCTAssertNotNil(user.id)
    }

    func testValidation() throws {
        // Unwrapping optionals in tests
        let user = try XCTUnwrap(sut.findUser(id: 123))
        XCTAssertEqual(user.name, "Test User")
    }
}
```

## Async Testing

```swift
final class AsyncTests: XCTestCase {
    func testAsyncFunction() async throws {
        // Test async/await code directly
        let result = try await fetchData()
        XCTAssertEqual(result.count, 10)
    }

    func testAsyncSequence() async throws {
        var results: [Int] = []

        for try await value in numberStream() {
            results.append(value)
            if results.count >= 5 {
                break
            }
        }

        XCTAssertEqual(results.count, 5)
    }

    func testWithTimeout() async throws {
        // Test with timeout
        try await withTimeout(seconds: 5) {
            try await longRunningOperation()
        }
    }

    func testConcurrentOperations() async throws {
        async let result1 = fetchData(id: 1)
        async let result2 = fetchData(id: 2)

        let (data1, data2) = try await (result1, result2)

        XCTAssertNotNil(data1)
        XCTAssertNotNil(data2)
    }
}

// Helper for timeout
func withTimeout<T>(
    seconds: TimeInterval,
    operation: @escaping () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask {
            try await operation()
        }

        group.addTask {
            try await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}
```

## Mocking

```swift
// Protocol for dependency injection
protocol DataService {
    func fetch(id: Int) async throws -> Data
    func save(_ data: Data) async throws
}

// Production implementation
class APIDataService: DataService {
    func fetch(id: Int) async throws -> Data {
        // Real API call
    }

    func save(_ data: Data) async throws {
        // Real save operation
    }
}

// Mock for testing
class MockDataService: DataService {
    var fetchCalled = false
    var fetchID: Int?
    var fetchResult: Data?
    var fetchError: Error?

    var saveCalled = false
    var savedData: Data?
    var saveError: Error?

    func fetch(id: Int) async throws -> Data {
        fetchCalled = true
        fetchID = id

        if let error = fetchError {
            throw error
        }

        return fetchResult ?? Data()
    }

    func save(_ data: Data) async throws {
        saveCalled = true
        savedData = data

        if let error = saveError {
            throw error
        }
    }
}

// Using mock in tests
final class DataManagerTests: XCTestCase {
    func testDataFetch() async throws {
        // Given
        let mockService = MockDataService()
        mockService.fetchResult = "test data".data(using: .utf8)
        let manager = DataManager(service: mockService)

        // When
        let result = try await manager.loadData(id: 123)

        // Then
        XCTAssertTrue(mockService.fetchCalled)
        XCTAssertEqual(mockService.fetchID, 123)
        XCTAssertNotNil(result)
    }
}
```

## Test Doubles

```swift
// Spy - records interactions
class SpyDelegate: UserManagerDelegate {
    private(set) var didUpdateUserCalled = false
    private(set) var updatedUser: User?
    private(set) var callCount = 0

    func didUpdateUser(_ user: User) {
        didUpdateUserCalled = true
        updatedUser = user
        callCount += 1
    }
}

// Stub - provides predetermined responses
class StubNetworkService: NetworkService {
    var stubbedResponse: Result<Data, Error> = .success(Data())

    func fetch(url: URL) async throws -> Data {
        try stubbedResponse.get()
    }
}

// Fake - working implementation with shortcuts
class FakeDatabase: Database {
    private var storage: [String: Data] = [:]

    func save(key: String, value: Data) {
        storage[key] = value
    }

    func load(key: String) -> Data? {
        storage[key]
    }

    func clear() {
        storage.removeAll()
    }
}
```

## Performance Testing

```swift
final class PerformanceTests: XCTestCase {
    func testSortingPerformance() {
        let numbers = (0..<10000).shuffled()

        measure {
            _ = numbers.sorted()
        }
    }

    func testCustomMetrics() {
        let metrics: [XCTMetric] = [
            XCTClockMetric(),
            XCTCPUMetric(),
            XCTMemoryMetric(),
            XCTStorageMetric()
        ]

        let options = XCTMeasureOptions()
        options.iterationCount = 10

        measure(metrics: metrics, options: options) {
            performExpensiveOperation()
        }
    }
}
```

## UI Testing

```swift
final class AppUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    func testLoginFlow() {
        // Test UI interactions
        let emailField = app.textFields["Email"]
        emailField.tap()
        emailField.typeText("test@example.com")

        let passwordField = app.secureTextFields["Password"]
        passwordField.tap()
        passwordField.typeText("password123")

        app.buttons["Login"].tap()

        // Verify navigation
        XCTAssertTrue(app.navigationBars["Dashboard"].exists)
    }

    func testButtonEnabled() {
        let button = app.buttons["Submit"]
        XCTAssertFalse(button.isEnabled)

        app.textFields["Username"].tap()
        app.textFields["Username"].typeText("testuser")

        XCTAssertTrue(button.isEnabled)
    }
}
```

## Testing Actors

```swift
final class ActorTests: XCTestCase {
    func testActorIsolation() async throws {
        actor Counter {
            private var value = 0

            func increment() -> Int {
                value += 1
                return value
            }

            func reset() {
                value = 0
            }
        }

        let counter = Counter()

        // Test concurrent access
        await withTaskGroup(of: Int.self) { group in
            for _ in 0..<100 {
                group.addTask {
                    await counter.increment()
                }
            }
        }

        let finalValue = await counter.increment()
        XCTAssertEqual(finalValue, 101)
    }
}
```

## Snapshot Testing

```swift
import SnapshotTesting

final class ViewSnapshotTests: XCTestCase {
    func testButtonAppearance() {
        let button = UIButton()
        button.setTitle("Tap Me", for: .normal)
        button.backgroundColor = .blue
        button.frame = CGRect(x: 0, y: 0, width: 200, height: 50)

        assertSnapshot(matching: button, as: .image)
    }

    func testViewControllerLayout() {
        let vc = MyViewController()
        assertSnapshot(matching: vc, as: .image(on: .iPhone13))
    }

    func testDarkMode() {
        let view = MyView()
        assertSnapshot(matching: view, as: .image(traits: .init(userInterfaceStyle: .dark)))
    }
}
```

## Test Organization

```swift
// MARK: - Test Cases
extension UserManagerTests {
    // MARK: Creation Tests
    func testUserCreation() { }
    func testUserCreationWithInvalidData() { }

    // MARK: Validation Tests
    func testEmailValidation() { }
    func testPasswordValidation() { }

    // MARK: Persistence Tests
    func testUserSave() { }
    func testUserLoad() { }
}

// MARK: - Test Helpers
extension UserManagerTests {
    func makeTestUser() -> User {
        User(name: "Test", email: "test@example.com")
    }

    func setupMockData() {
        // Common test setup
    }
}
```

## Best Practices

- Use `@testable import` to test internal types
- One assertion concept per test (can have multiple XCTAssert calls)
- Use Given-When-Then pattern for clarity
- Name tests descriptively: `test_methodName_condition_expectedResult`
- Use setUp/tearDown for common test setup
- Prefer dependency injection for testability
- Use protocols to enable mocking
- Test edge cases and error conditions
- Use async/await for testing async code
- Measure performance with XCTest metrics
- Use UI testing for critical user flows
- Mock external dependencies
- Keep tests fast and independent
- Use test doubles appropriately (mock, stub, spy, fake)
