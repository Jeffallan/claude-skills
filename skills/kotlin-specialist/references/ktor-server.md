# Ktor Server

## Application Setup

```kotlin
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json

fun main() {
    embeddedServer(Netty, port = 8080, host = "0.0.0.0") {
        configureRouting()
        configureSerialization()
        configureAuth()
        configureMonitoring()
    }.start(wait = true)
}

fun Application.configureSerialization() {
    install(ContentNegotiation) {
        json(Json {
            prettyPrint = true
            isLenient = true
            ignoreUnknownKeys = true
        })
    }
}
```

## Routing

```kotlin
import io.ktor.server.routing.*
import io.ktor.server.response.*
import io.ktor.server.request.*
import io.ktor.http.*

fun Application.configureRouting() {
    routing {
        route("/api/v1") {
            userRoutes()
            postRoutes()
        }
    }
}

fun Route.userRoutes() {
    route("/users") {
        get {
            val users = userService.getAllUsers()
            call.respond(HttpStatusCode.OK, users)
        }

        get("/{id}") {
            val id = call.parameters["id"]
                ?: return@get call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val user = userService.getUser(id)
                ?: return@get call.respond(HttpStatusCode.NotFound, "User not found")

            call.respond(HttpStatusCode.OK, user)
        }

        post {
            val userRequest = call.receive<CreateUserRequest>()
            val user = userService.createUser(userRequest)
            call.respond(HttpStatusCode.Created, user)
        }

        put("/{id}") {
            val id = call.parameters["id"]
                ?: return@put call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val updateRequest = call.receive<UpdateUserRequest>()
            val user = userService.updateUser(id, updateRequest)
                ?: return@put call.respond(HttpStatusCode.NotFound, "User not found")

            call.respond(HttpStatusCode.OK, user)
        }

        delete("/{id}") {
            val id = call.parameters["id"]
                ?: return@delete call.respond(HttpStatusCode.BadRequest, "Missing ID")

            val deleted = userService.deleteUser(id)
            if (deleted) {
                call.respond(HttpStatusCode.NoContent)
            } else {
                call.respond(HttpStatusCode.NotFound, "User not found")
            }
        }
    }
}
```

## Models & Serialization

```kotlin
import kotlinx.serialization.Serializable

@Serializable
data class User(
    val id: String,
    val email: String,
    val name: String,
    val createdAt: Long
)

@Serializable
data class CreateUserRequest(
    val email: String,
    val name: String,
    val password: String
)

@Serializable
data class UpdateUserRequest(
    val email: String? = null,
    val name: String? = null
)

@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: String? = null
)
```

## Authentication (JWT)

```kotlin
import io.ktor.server.auth.*
import io.ktor.server.auth.jwt.*
import com.auth0.jwt.JWT
import com.auth0.jwt.algorithms.Algorithm

fun Application.configureAuth() {
    val secret = environment.config.property("jwt.secret").getString()
    val issuer = environment.config.property("jwt.issuer").getString()
    val audience = environment.config.property("jwt.audience").getString()

    install(Authentication) {
        jwt("auth-jwt") {
            realm = "Ktor Server"
            verifier(
                JWT
                    .require(Algorithm.HMAC256(secret))
                    .withIssuer(issuer)
                    .withAudience(audience)
                    .build()
            )
            validate { credential ->
                if (credential.payload.audience.contains(audience)) {
                    JWTPrincipal(credential.payload)
                } else {
                    null
                }
            }
            challenge { _, _ ->
                call.respond(HttpStatusCode.Unauthorized, "Token is not valid or has expired")
            }
        }
    }
}

// Protected routes
fun Route.protectedRoutes() {
    authenticate("auth-jwt") {
        get("/profile") {
            val principal = call.principal<JWTPrincipal>()
            val userId = principal?.payload?.getClaim("userId")?.asString()
            val user = userService.getUser(userId ?: "")
            call.respond(user ?: HttpStatusCode.NotFound)
        }
    }
}

// Token generation
fun generateToken(userId: String): String {
    return JWT.create()
        .withAudience(audience)
        .withIssuer(issuer)
        .withClaim("userId", userId)
        .withExpiresAt(Date(System.currentTimeMillis() + 60000 * 60 * 24)) // 24h
        .sign(Algorithm.HMAC256(secret))
}
```

## Database Integration (Exposed)

```kotlin
import org.jetbrains.exposed.sql.*
import org.jetbrains.exposed.sql.transactions.experimental.newSuspendedTransaction
import org.jetbrains.exposed.sql.transactions.transaction

object Users : Table() {
    val id = varchar("id", 36)
    val email = varchar("email", 255).uniqueIndex()
    val name = varchar("name", 255)
    val passwordHash = varchar("password_hash", 255)
    val createdAt = long("created_at")

    override val primaryKey = PrimaryKey(id)
}

class UserService(private val database: Database) {
    suspend fun <T> dbQuery(block: suspend () -> T): T =
        newSuspendedTransaction(Dispatchers.IO) { block() }

    suspend fun getAllUsers(): List<User> = dbQuery {
        Users.selectAll().map { toUser(it) }
    }

    suspend fun getUser(id: String): User? = dbQuery {
        Users.select { Users.id eq id }
            .mapNotNull { toUser(it) }
            .singleOrNull()
    }

    suspend fun createUser(request: CreateUserRequest): User = dbQuery {
        val id = UUID.randomUUID().toString()
        val passwordHash = hashPassword(request.password)

        Users.insert {
            it[Users.id] = id
            it[email] = request.email
            it[name] = request.name
            it[Users.passwordHash] = passwordHash
            it[createdAt] = System.currentTimeMillis()
        }

        User(id, request.email, request.name, System.currentTimeMillis())
    }

    private fun toUser(row: ResultRow): User =
        User(
            id = row[Users.id],
            email = row[Users.email],
            name = row[Users.name],
            createdAt = row[Users.createdAt]
        )
}
```

## Error Handling

```kotlin
import io.ktor.server.plugins.statuspages.*

fun Application.configureErrorHandling() {
    install(StatusPages) {
        exception<Throwable> { call, cause ->
            when (cause) {
                is IllegalArgumentException -> {
                    call.respond(
                        HttpStatusCode.BadRequest,
                        ApiResponse<Nothing>(success = false, error = cause.message)
                    )
                }
                is NotFoundException -> {
                    call.respond(
                        HttpStatusCode.NotFound,
                        ApiResponse<Nothing>(success = false, error = cause.message)
                    )
                }
                else -> {
                    call.respond(
                        HttpStatusCode.InternalServerError,
                        ApiResponse<Nothing>(success = false, error = "Internal server error")
                    )
                }
            }
        }

        status(HttpStatusCode.NotFound) { call, status ->
            call.respond(
                status,
                ApiResponse<Nothing>(success = false, error = "Resource not found")
            )
        }
    }
}

class NotFoundException(message: String) : Exception(message)
```

## CORS Configuration

```kotlin
import io.ktor.server.plugins.cors.routing.*

fun Application.configureCORS() {
    install(CORS) {
        allowMethod(HttpMethod.Options)
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowMethod(HttpMethod.Patch)
        allowHeader(HttpHeaders.Authorization)
        allowHeader(HttpHeaders.ContentType)
        allowCredentials = true
        allowNonSimpleContentTypes = true

        anyHost() // Development only
        // allowHost("client-host", schemes = listOf("http", "https"))
    }
}
```

## WebSockets

```kotlin
import io.ktor.websocket.*
import io.ktor.server.websocket.WebSockets
import io.ktor.server.websocket.webSocket
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.receiveAsFlow

fun Application.configureWebSockets() {
    install(WebSockets) {
        pingPeriod = Duration.ofSeconds(15)
        timeout = Duration.ofSeconds(15)
        maxFrameSize = Long.MAX_VALUE
        masking = false
    }

    routing {
        webSocket("/chat") {
            val session = ChatSession(this)
            chatService.addSession(session)

            try {
                for (frame in incoming) {
                    when (frame) {
                        is Frame.Text -> {
                            val message = frame.readText()
                            chatService.broadcast(message)
                        }
                        else -> {}
                    }
                }
            } finally {
                chatService.removeSession(session)
            }
        }
    }
}
```

## Testing

```kotlin
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.server.testing.*
import kotlin.test.*

class ApplicationTest {
    @Test
    fun testGetUsers() = testApplication {
        application {
            configureRouting()
            configureSerialization()
        }

        val response = client.get("/api/v1/users")
        assertEquals(HttpStatusCode.OK, response.status)
    }

    @Test
    fun testCreateUser() = testApplication {
        application {
            configureRouting()
            configureSerialization()
        }

        val response = client.post("/api/v1/users") {
            contentType(ContentType.Application.Json)
            setBody(CreateUserRequest("test@example.com", "Test User", "password123"))
        }

        assertEquals(HttpStatusCode.Created, response.status)
    }

    @Test
    fun testAuthenticatedRoute() = testApplication {
        application {
            configureAuth()
            configureRouting()
        }

        val token = generateToken("user123")

        val response = client.get("/api/v1/profile") {
            header(HttpHeaders.Authorization, "Bearer $token")
        }

        assertEquals(HttpStatusCode.OK, response.status)
    }
}
```

## Quick Reference

| Plugin | Purpose |
|--------|---------|
| `ContentNegotiation` | JSON serialization |
| `Authentication` | JWT/OAuth2 auth |
| `CORS` | Cross-origin requests |
| `StatusPages` | Error handling |
| `CallLogging` | Request logging |
| `WebSockets` | WebSocket support |
| `RateLimit` | Rate limiting |
| `Compression` | Response compression |

| Function | Purpose |
|----------|---------|
| `call.receive<T>()` | Parse request body |
| `call.respond()` | Send response |
| `call.parameters` | Query/path params |
| `call.principal()` | Get authenticated user |
| `authenticate { }` | Protect routes |
| `route("/path") { }` | Group routes |
