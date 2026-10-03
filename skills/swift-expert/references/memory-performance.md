# Memory & Performance

## Automatic Reference Counting (ARC)

```swift
// Strong references (default)
class Person {
    let name: String
    var apartment: Apartment?

    init(name: String) {
        self.name = name
    }

    deinit {
        print("\(name) is being deinitialized")
    }
}

class Apartment {
    let unit: String
    weak var tenant: Person?  // Weak to break retain cycle

    init(unit: String) {
        self.unit = unit
    }

    deinit {
        print("Apartment \(unit) is being deinitialized")
    }
}

var john: Person? = Person(name: "John")
var unit4A: Apartment? = Apartment(unit: "4A")

john?.apartment = unit4A
unit4A?.tenant = john

// Setting to nil will properly deallocate both
john = nil
unit4A = nil
```

## Weak and Unowned References

```swift
// Weak - optional reference that doesn't keep object alive
class ViewController: UIViewController {
    weak var delegate: ViewControllerDelegate?

    func performAction() {
        delegate?.didPerformAction()
    }
}

// Unowned - non-optional reference, assumes target outlives owner
class Customer {
    let name: String
    var card: CreditCard?

    init(name: String) {
        self.name = name
    }
}

class CreditCard {
    let number: String
    unowned let customer: Customer  // Customer always outlives card

    init(number: String, customer: Customer) {
        self.number = number
        self.customer = customer
    }
}

// Unowned optional (Swift 5+)
class Department {
    var courses: [Course] = []
}

class Course {
    unowned var department: Department
    unowned var nextCourse: Course?

    init(department: Department) {
        self.department = department
    }
}
```

## Capture Lists in Closures

```swift
class DataManager {
    var data: [String] = []

    func loadData() {
        // Strong reference cycle - DataManager won't be deallocated
        NetworkManager.fetch { response in
            self.data = response  // self is captured strongly
        }

        // Weak self - breaks cycle
        NetworkManager.fetch { [weak self] response in
            guard let self = self else { return }
            self.data = response
        }

        // Unowned self - when self definitely outlives closure
        NetworkManager.fetch { [unowned self] response in
            self.data = response  // Crashes if self is deallocated
        }

        // Capturing specific values
        let identifier = UUID()
        NetworkManager.fetch { [identifier] response in
            print("Request \(identifier) completed")
        }
    }
}
```

## Value Semantics

```swift
// Structs provide automatic copy-on-write for collections
struct User {
    var name: String
    var friends: [String]  // Copy-on-write
}

var user1 = User(name: "Alice", friends: ["Bob"])
var user2 = user1  // Shallow copy
user2.friends.append("Charlie")  // Now triggers deep copy

print(user1.friends)  // ["Bob"]
print(user2.friends)  // ["Bob", "Charlie"]

// Custom copy-on-write
final class Storage<T> {
    var value: T
    init(_ value: T) { self.value = value }
}

struct MyArray<Element> {
    private var storage: Storage<[Element]>

    init(_ elements: [Element] = []) {
        storage = Storage(elements)
    }

    var value: [Element] {
        get { storage.value }
        set {
            if !isKnownUniquelyReferenced(&storage) {
                storage = Storage(newValue)
            } else {
                storage.value = newValue
            }
        }
    }

    mutating func append(_ element: Element) {
        if !isKnownUniquelyReferenced(&storage) {
            storage = Storage(storage.value)
        }
        storage.value.append(element)
    }
}
```

## Performance Optimization

```swift
// Use lazy properties for expensive computations
class Report {
    let data: [DataPoint]

    lazy var summary: String = {
        // Expensive computation only when accessed
        data.map { $0.description }.joined(separator: "\n")
    }()

    init(data: [DataPoint]) {
        self.data = data
    }
}

// Avoid repeated type casting
// Bad
for item in items {
    if let user = item as? User {
        processUser(user)
    }
}

// Good
let users = items.compactMap { $0 as? User }
for user in users {
    processUser(user)
}

// Use contiguous storage
// Slower - pointer indirection for each element
let arrayOfClasses: [MyClass] = [MyClass(), MyClass()]

// Faster - contiguous memory
let arrayOfStructs: [MyStruct] = [MyStruct(), MyStruct()]

// Avoid string concatenation in loops
// Bad
var result = ""
for item in items {
    result += item.description  // Allocates new string each time
}

// Good
let result = items.map { $0.description }.joined()

// Or
var result = ""
result.reserveCapacity(estimatedSize)
for item in items {
    result.append(item.description)
}
```

## Collection Performance

```swift
// Choose the right collection type
// Array - ordered, random access O(1), append O(1) amortized
let ordered: [Int] = [1, 2, 3]

// Set - unique elements, contains O(1), no order
let unique: Set<Int> = [1, 2, 3]

// Dictionary - key-value pairs, lookup O(1)
let mapping: [String: Int] = ["a": 1, "b": 2]

// Use ContiguousArray for performance-critical code
let contiguous = ContiguousArray<MyStruct>(repeating: MyStruct(), count: 1000)

// Reserve capacity for known sizes
var numbers: [Int] = []
numbers.reserveCapacity(1000)
for i in 0..<1000 {
    numbers.append(i)
}

// Use enumerated() instead of indices
// Bad
for i in 0..<array.count {
    process(index: i, value: array[i])
}

// Good
for (index, value) in array.enumerated() {
    process(index: index, value: value)
}
```

## Memory Profiling with Instruments

```swift
// Add markers for profiling
import os.signpost

let log = OSLog(subsystem: "com.example.app", category: "Performance")

func processData() {
    os_signpost(.begin, log: log, name: "Data Processing")
    defer { os_signpost(.end, log: log, name: "Data Processing") }

    // Processing code
}

// Autoreleasepool for memory-intensive loops
func processLargeDataset() {
    for batch in dataBatches {
        autoreleasepool {
            // Process batch
            // Memory released at end of each iteration
        }
    }
}

// Check for memory leaks
#if DEBUG
extension NSObject {
    static func trackAllocations() {
        let count = performSelector(
            Selector(("instancesRespond:"))
        )
        print("\(self): \(count) instances")
    }
}
#endif
```

## Optimization Levels

```swift
// Whole Module Optimization in Package.swift
let package = Package(
    name: "MyApp",
    products: [
        .executable(name: "MyApp", targets: ["MyApp"])
    ],
    targets: [
        .target(
            name: "MyApp",
            swiftSettings: [
                .unsafeFlags(["-O"], .when(configuration: .release))
            ]
        )
    ]
)

// Inline optimization
@inline(__always)
func criticalPath() {
    // Always inlined
}

@inline(never)
func debugHelper() {
    // Never inlined, good for debugging
}

// Optimization attributes
@_specialize(where T == Int)
@_specialize(where T == String)
func process<T>(_ value: T) {
    // Specialized versions generated
}
```

## Memory Warnings

```swift
class ImageCache {
    private var cache: [String: UIImage] = [:]

    init() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(clearCache),
            name: UIApplication.didReceiveMemoryWarningNotification,
            object: nil
        )
    }

    @objc private func clearCache() {
        cache.removeAll()
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
```

## Best Practices

- Use value types (structs) by default
- Use weak references for delegates
- Use unowned when lifetime is guaranteed
- Always use capture lists in closures that reference self
- Profile before optimizing (use Instruments)
- Reserve collection capacity when size is known
- Use lazy properties for expensive computations
- Implement copy-on-write for custom types with reference storage
- Handle memory warnings in iOS apps
- Use autoreleasepool for memory-intensive loops
- Choose appropriate collection types
- Avoid premature optimization - measure first
