# Kotlin Multiplatform (KMP)

## Project Structure

```
project/
├── commonMain/
│   ├── kotlin/
│   │   ├── data/
│   │   │   └── User.kt
│   │   ├── repository/
│   │   │   └── UserRepository.kt
│   │   └── Platform.kt (expect)
│   └── resources/
├── androidMain/
│   └── kotlin/
│       └── Platform.android.kt (actual)
├── iosMain/
│   └── kotlin/
│       └── Platform.ios.kt (actual)
└── jvmMain/
    └── kotlin/
        └── Platform.jvm.kt (actual)
```

## Gradle Configuration

```kotlin
// build.gradle.kts
plugins {
    kotlin("multiplatform") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
}

kotlin {
    // JVM target
    jvm {
        compilations.all {
            kotlinOptions.jvmTarget = "17"
        }
    }

    // Android target
    androidTarget {
        compilations.all {
            kotlinOptions.jvmTarget = "17"
        }
    }

    // iOS targets
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "shared"
            isStatic = true
        }
    }

    // JS target
    js(IR) {
        browser()
        nodejs()
    }

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
                implementation("io.ktor:ktor-client-core:2.3.7")
            }
        }

        val commonTest by getting {
            dependencies {
                implementation(kotlin("test"))
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
            }
        }

        val androidMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-okhttp:2.3.7")
            }
        }

        val iosMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-darwin:2.3.7")
            }
        }

        val jvmMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-cio:2.3.7")
            }
        }
    }
}
```

## Expect/Actual Pattern

```kotlin
// commonMain/kotlin/Platform.kt
expect class Platform() {
    val name: String
    fun currentTimeMillis(): Long
}

expect fun getPlatform(): Platform

// androidMain/kotlin/Platform.android.kt
import android.os.Build

actual class Platform {
    actual val name: String = "Android ${Build.VERSION.SDK_INT}"

    actual fun currentTimeMillis(): Long =
        System.currentTimeMillis()
}

actual fun getPlatform(): Platform = Platform()

// iosMain/kotlin/Platform.ios.kt
import platform.UIKit.UIDevice
import platform.Foundation.NSDate

actual class Platform {
    actual val name: String =
        UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion

    actual fun currentTimeMillis(): Long =
        (NSDate().timeIntervalSince1970 * 1000).toLong()
}

actual fun getPlatform(): Platform = Platform()
```

## Common Code Patterns

```kotlin
// commonMain - Shared business logic
class UserRepository(private val api: ApiService) {
    private val _users = MutableStateFlow<List<User>>(emptyList())
    val users: StateFlow<List<User>> = _users.asStateFlow()

    suspend fun loadUsers() {
        try {
            val result = api.getUsers()
            _users.value = result
        } catch (e: Exception) {
            // Handle error
        }
    }
}

// Shared models
@Serializable
data class User(
    val id: String,
    val name: String,
    val email: String,
    val createdAt: Long
)

// Sealed class for platform-agnostic results
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
    object Loading : Result<Nothing>()
}
```

## Platform-Specific Implementations

```kotlin
// commonMain
expect class DatabaseDriver()

expect suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>>

// androidMain
import android.content.Context
import androidx.sqlite.db.SupportSQLiteDatabase

actual class DatabaseDriver(private val context: Context) {
    private val db: SupportSQLiteDatabase = // Initialize Android SQLite
}

actual suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>> =
    withContext(Dispatchers.IO) {
        // Android-specific query execution
    }

// iosMain
import platform.Foundation.NSFileManager

actual class DatabaseDriver() {
    private val db = // Initialize iOS SQLite
}

actual suspend fun DatabaseDriver.query(sql: String): List<Map<String, Any>> =
    withContext(Dispatchers.Default) {
        // iOS-specific query execution
    }
```

## Ktor Client Multiplatform

```kotlin
// commonMain
class ApiClient {
    private val client = HttpClient {
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }
        install(Logging) {
            level = LogLevel.INFO
        }
    }

    suspend fun getUsers(): List<User> =
        client.get("https://api.example.com/users").body()

    suspend fun createUser(user: User): User =
        client.post("https://api.example.com/users") {
            contentType(ContentType.Application.Json)
            setBody(user)
        }.body()
}
```

## Source Set Hierarchy

```kotlin
// Intermediate source sets for iOS
kotlin {
    sourceSets {
        val commonMain by getting
        val commonTest by getting

        val iosMain by creating {
            dependsOn(commonMain)
        }

        val iosX64Main by getting {
            dependsOn(iosMain)
        }

        val iosArm64Main by getting {
            dependsOn(iosMain)
        }

        val iosSimulatorArm64Main by getting {
            dependsOn(iosMain)
        }
    }
}
```

## Native Interop (iOS)

```kotlin
// iosMain - Calling Objective-C/Swift
import platform.Foundation.NSBundle
import platform.UIKit.UIApplication

fun getAppVersion(): String =
    NSBundle.mainBundle.objectForInfoDictionaryKey("CFBundleShortVersionString") as? String
        ?: "Unknown"

fun openURL(url: String) {
    val nsUrl = NSURL.URLWithString(url)
    UIApplication.sharedApplication.openURL(nsUrl ?: return)
}

// Freezing for thread safety (Kotlin/Native memory model)
class IosViewModel {
    private val scope = MainScope()

    fun loadData() {
        scope.launch {
            val data = api.getData().freeze() // Freeze for iOS
            updateUI(data)
        }
    }
}
```

## Testing Multiplatform Code

```kotlin
// commonTest
class UserRepositoryTest {
    private lateinit var repository: UserRepository

    @BeforeTest
    fun setup() {
        repository = UserRepository(FakeApiService())
    }

    @Test
    fun testLoadUsers() = runTest {
        repository.loadUsers()

        val users = repository.users.value
        assertEquals(2, users.size)
    }
}

// Platform-specific tests
// androidTest
class AndroidUserRepositoryTest {
    @Test
    fun testAndroidSpecific() {
        // Android-only test
    }
}

// iosTest
class IosUserRepositoryTest {
    @Test
    fun testIosSpecific() {
        // iOS-only test
    }
}
```

## Publishing KMP Library

```kotlin
// build.gradle.kts
plugins {
    `maven-publish`
}

publishing {
    publications {
        create<MavenPublication>("kotlinMultiplatform") {
            groupId = "com.example"
            artifactId = "shared"
            version = "1.0.0"
        }
    }

    repositories {
        maven {
            url = uri("https://maven.pkg.github.com/user/repo")
            credentials {
                username = System.getenv("GITHUB_ACTOR")
                password = System.getenv("GITHUB_TOKEN")
            }
        }
    }
}
```

## Quick Reference

| Pattern | Purpose |
|---------|---------|
| `expect class` | Declare platform-specific type in common |
| `actual class` | Implement platform-specific type |
| `commonMain` | Shared code across all platforms |
| `androidMain` | Android-specific implementations |
| `iosMain` | iOS-specific implementations (all targets) |
| `jvmMain` | JVM/Desktop-specific code |
| `jsMain` | JavaScript-specific code |
| `*Test` | Platform-specific tests |
| `dependsOn` | Source set hierarchy |
| `.freeze()` | iOS memory model (legacy) |
| `kotlin("multiplatform")` | KMP Gradle plugin |
