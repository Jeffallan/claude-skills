# Reactive WebFlux

> Reference for: Java Architect
> Load when: Reactive programming, WebFlux, Project Reactor, R2DBC

## WebFlux Controller

```java
package com.example.presentation.rest;

import com.example.application.dto.UserRequest;
import com.example.application.dto.UserResponse;
import com.example.application.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping
    public Flux<UserResponse> getAllUsers() {
        return userService.findAll();
    }

    @GetMapping("/{id}")
    public Mono<UserResponse> getUserById(@PathVariable Long id) {
        return userService.findById(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Mono<UserResponse> createUser(@RequestBody @Valid UserRequest request) {
        return userService.create(request);
    }

    @PutMapping("/{id}")
    public Mono<UserResponse> updateUser(
        @PathVariable Long id,
        @RequestBody @Valid UserRequest request
    ) {
        return userService.update(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public Mono<Void> deleteUser(@PathVariable Long id) {
        return userService.delete(id);
    }
}
```

## Reactive Service Layer

```java
package com.example.application.service;

import com.example.application.dto.UserRequest;
import com.example.application.dto.UserResponse;
import com.example.application.mapper.UserMapper;
import com.example.domain.model.User;
import com.example.domain.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;
    private final UserMapper userMapper;

    public Flux<UserResponse> findAll() {
        return userRepository.findAll()
            .map(userMapper::toResponse);
    }

    public Mono<UserResponse> findById(Long id) {
        return userRepository.findById(id)
            .map(userMapper::toResponse)
            .switchIfEmpty(Mono.error(
                new EntityNotFoundException("User not found: " + id)
            ));
    }

    @Transactional
    public Mono<UserResponse> create(UserRequest request) {
        return Mono.just(request)
            .map(userMapper::toEntity)
            .flatMap(userRepository::save)
            .map(userMapper::toResponse);
    }

    @Transactional
    public Mono<UserResponse> update(Long id, UserRequest request) {
        return userRepository.findById(id)
            .switchIfEmpty(Mono.error(
                new EntityNotFoundException("User not found: " + id)
            ))
            .flatMap(existing -> {
                userMapper.updateEntity(request, existing);
                return userRepository.save(existing);
            })
            .map(userMapper::toResponse);
    }

    @Transactional
    public Mono<Void> delete(Long id) {
        return userRepository.findById(id)
            .switchIfEmpty(Mono.error(
                new EntityNotFoundException("User not found: " + id)
            ))
            .flatMap(userRepository::delete);
    }
}
```

## R2DBC Repository

```java
package com.example.domain.repository;

import com.example.domain.model.User;
import org.springframework.data.r2dbc.repository.Query;
import org.springframework.data.r2dbc.repository.R2dbcRepository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface UserRepository extends R2dbcRepository<User, Long> {

    Mono<User> findByEmail(String email);

    Flux<User> findByActiveTrue();

    @Query("""
        SELECT u.* FROM users u
        WHERE u.email LIKE CONCAT('%', :domain, '%')
        ORDER BY u.created_at DESC
        """)
    Flux<User> findByEmailDomain(String domain);

    @Query("""
        SELECT COUNT(*) FROM users
        WHERE created_at > :since
        """)
    Mono<Long> countCreatedSince(Instant since);
}
```

## R2DBC Entity

```java
package com.example.domain.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.relational.core.mapping.Table;

import java.time.Instant;

@Table("users")
public record User(
    @Id Long id,
    String email,
    String username,
    Boolean active,
    @CreatedDate Instant createdAt,
    @LastModifiedDate Instant updatedAt
) {
    public User withId(Long id) {
        return new User(id, email, username, active, createdAt, updatedAt);
    }

    public User withEmail(String email) {
        return new User(id, email, username, active, createdAt, updatedAt);
    }
}
```

## R2DBC Configuration

```yaml
spring:
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/demo
    username: demo
    password: demo
    pool:
      initial-size: 10
      max-size: 20
      max-idle-time: 30m

  data:
    r2dbc:
      repositories:
        enabled: true
```

## WebClient for External APIs

```java
package com.example.infrastructure.client;

import com.example.application.dto.ExternalUserDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.util.retry.Retry;

import java.time.Duration;

@Component
@RequiredArgsConstructor
public class ExternalUserClient {

    private final WebClient webClient;

    public Mono<ExternalUserDto> getUser(Long id) {
        return webClient
            .get()
            .uri("/users/{id}", id)
            .retrieve()
            .bodyToMono(ExternalUserDto.class)
            .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)))
            .timeout(Duration.ofSeconds(5));
    }

    public Mono<ExternalUserDto> createUser(ExternalUserDto user) {
        return webClient
            .post()
            .uri("/users")
            .bodyValue(user)
            .retrieve()
            .bodyToMono(ExternalUserDto.class);
    }
}

@Configuration
class WebClientConfig {

    @Bean
    public WebClient webClient(WebClient.Builder builder) {
        return builder
            .baseUrl("https://api.example.com")
            .defaultHeader("User-Agent", "Demo Service")
            .build();
    }
}
```

## Reactor Operators

```java
// Transform data
Mono<String> mono = Mono.just("hello")
    .map(String::toUpperCase)
    .map(s -> s + "!")
    .defaultIfEmpty("empty");

// Chain async operations
Mono<UserResponse> result = userRepository.findById(id)
    .flatMap(user -> orderRepository.findByUserId(user.id())
        .collectList()
        .map(orders -> new UserResponse(user, orders))
    );

// Combine multiple sources
Mono<UserDetails> combined = Mono.zip(
    userService.getUser(id),
    addressService.getAddress(id),
    (user, address) -> new UserDetails(user, address)
);

// Error handling
Mono<User> safe = userRepository.findById(id)
    .onErrorResume(DatabaseException.class, e ->
        cacheRepository.findById(id)
    )
    .doOnError(e -> log.error("Failed to fetch user", e));

// Backpressure
Flux<Data> stream = dataRepository.findAll()
    .buffer(100)  // Process in batches
    .flatMap(batch -> processBatch(batch), 5);  // Max 5 concurrent
```

## Testing Reactive Code

```java
package com.example.application.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    void shouldFindUserById() {
        User user = new User(1L, "test@example.com", "testuser", true, null, null);
        when(userRepository.findById(1L)).thenReturn(Mono.just(user));

        StepVerifier.create(userService.findById(1L))
            .expectNextMatches(response ->
                response.email().equals("test@example.com")
            )
            .verifyComplete();
    }

    @Test
    void shouldThrowWhenUserNotFound() {
        when(userRepository.findById(1L)).thenReturn(Mono.empty());

        StepVerifier.create(userService.findById(1L))
            .expectError(EntityNotFoundException.class)
            .verify();
    }
}
```

## Quick Reference

| Operator | Purpose |
|----------|---------|
| `Mono.just()` | Create Mono from value |
| `Flux.fromIterable()` | Create Flux from collection |
| `.map()` | Transform synchronously |
| `.flatMap()` | Transform to Mono/Flux |
| `.filter()` | Filter elements |
| `.switchIfEmpty()` | Fallback for empty |
| `.zip()` | Combine multiple sources |
| `.retry()` | Retry on error |
| `.timeout()` | Set timeout |
| `.subscribe()` | Trigger execution |
