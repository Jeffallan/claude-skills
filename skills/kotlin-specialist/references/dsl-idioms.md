# DSL & Kotlin Idioms

## Type-Safe Builders

```kotlin
// HTML DSL example
class Tag(val name: String) {
    val children = mutableListOf<Tag>()
    val attributes = mutableMapOf<String, String>()

    fun <T : Tag> initTag(tag: T, init: T.() -> Unit): T {
        tag.init()
        children.add(tag)
        return tag
    }

    override fun toString(): String {
        val attrs = attributes.entries.joinToString(" ") { "${it.key}=\"${it.value}\"" }
        val content = children.joinToString("")
        return "<$name${if (attrs.isNotEmpty()) " $attrs" else ""}>$content</$name>"
    }
}

class HTML : Tag("html") {
    fun head(init: Head.() -> Unit) = initTag(Head(), init)
    fun body(init: Body.() -> Unit) = initTag(Body(), init)
}

class Head : Tag("head") {
    fun title(init: Title.() -> Unit) = initTag(Title(), init)
}

class Title : Tag("title") {
    operator fun String.unaryPlus() {
        children.add(TextNode(this))
    }
}

class Body : Tag("body") {
    fun div(classes: String? = null, init: Div.() -> Unit) =
        initTag(Div(), init).apply {
            classes?.let { attributes["class"] = it }
        }
}

class Div : Tag("div") {
    fun p(init: P.() -> Unit) = initTag(P(), init)
}

class P : Tag("p") {
    operator fun String.unaryPlus() {
        children.add(TextNode(this))
    }
}

class TextNode(private val text: String) : Tag("") {
    override fun toString() = text
}

// Usage
fun html(init: HTML.() -> Unit): HTML {
    val html = HTML()
    html.init()
    return html
}

val page = html {
    head {
        title { +"My Page" }
    }
    body {
        div("container") {
            p { +"Hello, World!" }
        }
    }
}
```

## Lambda with Receiver

```kotlin
// Configuration DSL
class DatabaseConfig {
    var host: String = "localhost"
    var port: Int = 5432
    var username: String = ""
    var password: String = ""
    var database: String = ""
}

fun database(config: DatabaseConfig.() -> Unit): DatabaseConfig {
    return DatabaseConfig().apply(config)
}

// Usage
val dbConfig = database {
    host = "db.example.com"
    port = 3306
    username = "admin"
    password = "secret"
    database = "myapp"
}

// Builder pattern with type-safe DSL
class User private constructor(
    val id: String,
    val name: String,
    val email: String,
    val age: Int?
) {
    class Builder {
        var id: String = ""
        var name: String = ""
        var email: String = ""
        var age: Int? = null

        fun build(): User {
            require(id.isNotBlank()) { "ID is required" }
            require(name.isNotBlank()) { "Name is required" }
            require(email.isNotBlank()) { "Email is required" }
            return User(id, name, email, age)
        }
    }
}

fun user(init: User.Builder.() -> Unit): User =
    User.Builder().apply(init).build()

// Usage
val user = user {
    id = "123"
    name = "John Doe"
    email = "john@example.com"
    age = 30
}
```

## Scope Functions

```kotlin
// let - transform and null check
val result = user?.let { u ->
    "${u.name} (${u.email})"
}

// run - execute block and return result
val greeting = run {
    val name = getName()
    val title = getTitle()
    "$title $name"
}

// with - operate on object
val message = with(user) {
    "User: $name, Email: $email, Active: $isActive"
}

// apply - configure object
val user = User().apply {
    name = "John"
    email = "john@example.com"
    isActive = true
}

// also - side effects
val saved = user
    .also { logger.info("Saving user: ${it.name}") }
    .also { validate(it) }
    .also { repository.save(it) }

// takeIf/takeUnless - conditional returns
val adult = user.takeIf { it.age >= 18 }
val minor = user.takeUnless { it.age >= 18 }
```

## Extension Functions

```kotlin
// String extensions
fun String.isValidEmail(): Boolean =
    matches(Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\$"))

fun String.truncate(length: Int, ellipsis: String = "..."): String =
    if (this.length <= length) this
    else "${take(length - ellipsis.length)}$ellipsis"

// Collection extensions
fun <T> List<T>.second(): T = this[1]

fun <T> List<T>.secondOrNull(): T? = if (size >= 2) this[1] else null

inline fun <T> Iterable<T>.sumOf(selector: (T) -> Double): Double {
    var sum = 0.0
    for (element in this) {
        sum += selector(element)
    }
    return sum
}

// Generic extensions
inline fun <T> T.applyIf(condition: Boolean, block: T.() -> Unit): T =
    if (condition) apply(block) else this

// Usage
val email = "user@example.com"
    .applyIf(email.isValidEmail()) {
        toLowerCase()
    }
```

## Delegated Properties

```kotlin
import kotlin.properties.Delegates

// Lazy initialization
class Repository {
    val database: Database by lazy {
        Database.connect("jdbc:postgresql://localhost/db")
    }
}

// Observable property
class User {
    var name: String by Delegates.observable("<not set>") { prop, old, new ->
        println("${prop.name} changed from $old to $new")
    }
}

// Vetoable property (can reject changes)
class Account {
    var balance: Double by Delegates.vetoable(0.0) { _, old, new ->
        new >= 0 // Only allow non-negative balance
    }
}

// Custom delegate
class Preference<T>(private val key: String, private val default: T) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): T =
        preferences.get(key) as? T ?: default

    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: T) {
        preferences.set(key, value)
    }
}

class Settings {
    var theme: String by Preference("theme", "light")
    var fontSize: Int by Preference("fontSize", 14)
}

// Map delegation
class UserData(map: Map<String, Any?>) {
    val name: String by map
    val age: Int by map
    val email: String by map
}

val userData = UserData(
    mapOf(
        "name" to "John",
        "age" to 30,
        "email" to "john@example.com"
    )
)
```

## Infix Functions

```kotlin
// Custom infix operators
infix fun <T> T.shouldBe(expected: T) {
    if (this != expected) {
        throw AssertionError("Expected $expected but got $this")
    }
}

infix fun String.matches(regex: Regex): Boolean =
    this.matches(regex)

// Usage
val result = 2 + 2
result shouldBe 4

"test@example.com" matches Regex(".*@.*\\..*")

// DSL with infix
class Route(val path: String) {
    infix fun to(handler: () -> Unit): RouteDefinition =
        RouteDefinition(path, handler)
}

data class RouteDefinition(val path: String, val handler: () -> Unit)

infix fun String.GET(handler: () -> Unit): RouteDefinition =
    Route(this) to handler

// Usage
val route = "/users" GET { println("Get users") }
```

## Operator Overloading

```kotlin
data class Vector(val x: Double, val y: Double) {
    operator fun plus(other: Vector) =
        Vector(x + other.x, y + other.y)

    operator fun minus(other: Vector) =
        Vector(x - other.x, y - other.y)

    operator fun times(scalar: Double) =
        Vector(x * scalar, y * scalar)

    operator fun unaryMinus() =
        Vector(-x, -y)

    operator fun get(index: Int): Double = when (index) {
        0 -> x
        1 -> y
        else -> throw IndexOutOfBoundsException()
    }
}

// Usage
val v1 = Vector(1.0, 2.0)
val v2 = Vector(3.0, 4.0)
val v3 = v1 + v2
val v4 = v1 * 2.0
val x = v1[0]

// Invoke operator
class Greeter(private val greeting: String) {
    operator fun invoke(name: String) = "$greeting, $name!"
}

val greet = Greeter("Hello")
println(greet("World")) // Hello, World!
```

## Sealed Classes & When

```kotlin
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

// Exhaustive when
fun <T> handleResult(result: Result<T>): String = when (result) {
    is Result.Success -> "Data: ${result.data}"
    is Result.Error -> "Error: ${result.exception.message}"
    Result.Loading -> "Loading..."
}

// Sealed interface for more flexibility
sealed interface UiState {
    object Loading : UiState
    data class Success(val data: List<String>) : UiState
    data class Error(val message: String) : UiState
}
```

## Inline & Reified

```kotlin
// Inline function
inline fun <T> measureTime(block: () -> T): Pair<T, Long> {
    val start = System.currentTimeMillis()
    val result = block()
    val duration = System.currentTimeMillis() - start
    return result to duration
}

// Reified type parameters
inline fun <reified T> parseJson(json: String): T =
    Json.decodeFromString<T>(json)

inline fun <reified T : Any> Intent.getParcelableExtraCompat(key: String): T? =
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        getParcelableExtra(key, T::class.java)
    } else {
        @Suppress("DEPRECATION")
        getParcelableExtra(key) as? T
    }

// Value class (inline class)
@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String) {
    init {
        require(value.contains("@")) { "Invalid email" }
    }
}

// Usage - zero runtime overhead
val userId = UserId("123")
val email = Email("test@example.com")
```

## Quick Reference

| Idiom | Purpose |
|-------|---------|
| `let` | Transform & null check |
| `run` | Execute block, return result |
| `with` | Operate on object |
| `apply` | Configure object |
| `also` | Side effects |
| `takeIf/takeUnless` | Conditional return |
| `by lazy` | Lazy initialization |
| `by Delegates.observable` | Observe changes |
| `inline fun` | Eliminate lambda overhead |
| `reified` | Access type at runtime |
| `@JvmInline` | Zero-cost wrapper |
| `infix` | Custom operators |
| `operator` | Operator overloading |
| `sealed class` | Restricted hierarchies |
