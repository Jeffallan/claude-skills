# Testing Patterns

> Reference for: Java Architect
> Load when: Testing, JUnit 5, Mockito, TestContainers, integration tests

## Unit Testing with JUnit 5

```java
package com.example.application.service;

import com.example.application.dto.UserRequest;
import com.example.application.dto.UserResponse;
import com.example.application.mapper.UserMapper;
import com.example.domain.model.User;
import com.example.domain.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("User Service Tests")
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private UserMapper userMapper;

    @InjectMocks
    private UserService userService;

    private User testUser;
    private UserRequest userRequest;
    private UserResponse userResponse;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
            .id(1L)
            .email("test@example.com")
            .username("testuser")
            .active(true)
            .build();

        userRequest = new UserRequest("test@example.com", "testuser");
        userResponse = new UserResponse(1L, "test@example.com", "testuser");
    }

    @Test
    @DisplayName("Should find user by ID successfully")
    void shouldFindUserById() {
        // Given
        when(userRepository.findById(1L)).thenReturn(Optional.of(testUser));
        when(userMapper.toResponse(testUser)).thenReturn(userResponse);

        // When
        UserResponse result = userService.findById(1L);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.email()).isEqualTo("test@example.com");
        verify(userRepository).findById(1L);
        verify(userMapper).toResponse(testUser);
    }

    @Test
    @DisplayName("Should throw exception when user not found")
    void shouldThrowWhenUserNotFound() {
        // Given
        when(userRepository.findById(anyLong())).thenReturn(Optional.empty());

        // When / Then
        assertThatThrownBy(() -> userService.findById(999L))
            .isInstanceOf(EntityNotFoundException.class)
            .hasMessageContaining("User not found");

        verify(userRepository).findById(999L);
        verifyNoInteractions(userMapper);
    }

    @Test
    @DisplayName("Should create user successfully")
    void shouldCreateUser() {
        // Given
        when(userMapper.toEntity(userRequest)).thenReturn(testUser);
        when(userRepository.save(any(User.class))).thenReturn(testUser);
        when(userMapper.toResponse(testUser)).thenReturn(userResponse);

        // When
        UserResponse result = userService.create(userRequest);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.id()).isEqualTo(1L);
        verify(userRepository).save(any(User.class));
    }

    @ParameterizedTest
    @ValueSource(strings = {"admin", "user", "moderator"})
    @DisplayName("Should validate different user roles")
    void shouldValidateUserRoles(String role) {
        // Test with multiple roles
        assertThat(role).isNotBlank();
    }
}
```

## Integration Testing with TestContainers

```java
package com.example.integration;

import com.example.application.dto.UserRequest;
import com.example.application.dto.UserResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class UserIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @BeforeEach
    void setUp() {
        // Clean up database before each test
    }

    @Test
    void shouldCreateAndRetrieveUser() {
        // Create user
        UserRequest request = new UserRequest("test@example.com", "testuser");
        ResponseEntity<UserResponse> createResponse = restTemplate.postForEntity(
            "/api/users",
            request,
            UserResponse.class
        );

        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(createResponse.getBody()).isNotNull();
        Long userId = createResponse.getBody().id();

        // Retrieve user
        ResponseEntity<UserResponse> getResponse = restTemplate.getForEntity(
            "/api/users/" + userId,
            UserResponse.class
        );

        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().email()).isEqualTo("test@example.com");
    }
}
```

## Repository Testing

```java
package com.example.domain.repository;

import com.example.domain.model.User;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class UserRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private UserRepository userRepository;

    @Test
    void shouldFindUserByEmail() {
        // Given
        User user = User.builder()
            .email("test@example.com")
            .username("testuser")
            .active(true)
            .build();
        entityManager.persistAndFlush(user);

        // When
        Optional<User> found = userRepository.findByEmail("test@example.com");

        // Then
        assertThat(found).isPresent();
        assertThat(found.get().getEmail()).isEqualTo("test@example.com");
    }

    @Test
    void shouldCountActiveUsers() {
        // Given
        User activeUser = User.builder()
            .email("active@example.com")
            .username("active")
            .active(true)
            .build();
        User inactiveUser = User.builder()
            .email("inactive@example.com")
            .username("inactive")
            .active(false)
            .build();
        entityManager.persist(activeUser);
        entityManager.persist(inactiveUser);
        entityManager.flush();

        // When
        long count = userRepository.countByActiveTrue();

        // Then
        assertThat(count).isEqualTo(1);
    }
}
```

## REST Controller Testing

```java
package com.example.presentation.rest;

import com.example.application.dto.UserRequest;
import com.example.application.dto.UserResponse;
import com.example.application.service.UserService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(UserController.class)
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private UserService userService;

    @Test
    @WithMockUser
    void shouldGetUserById() throws Exception {
        // Given
        UserResponse response = new UserResponse(1L, "test@example.com", "testuser");
        when(userService.findById(1L)).thenReturn(response);

        // When / Then
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(1))
            .andExpect(jsonPath("$.email").value("test@example.com"));
    }

    @Test
    @WithMockUser
    void shouldCreateUser() throws Exception {
        // Given
        UserRequest request = new UserRequest("test@example.com", "testuser");
        UserResponse response = new UserResponse(1L, "test@example.com", "testuser");
        when(userService.create(any(UserRequest.class))).thenReturn(response);

        // When / Then
        mockMvc.perform(post("/api/users")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value(1));
    }

    @Test
    void shouldReturn401WhenNotAuthenticated() throws Exception {
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isUnauthorized());
    }
}
```

## Test Configuration

```java
package com.example.config;

import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.security.crypto.password.NoOpPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@TestConfiguration
public class TestSecurityConfig {

    @Bean
    @Primary
    public PasswordEncoder passwordEncoder() {
        return NoOpPasswordEncoder.getInstance();
    }
}
```

## Test Data Builders

```java
package com.example.test.builders;

import com.example.domain.model.User;

public class UserTestBuilder {

    private Long id = 1L;
    private String email = "test@example.com";
    private String username = "testuser";
    private Boolean active = true;

    public static UserTestBuilder aUser() {
        return new UserTestBuilder();
    }

    public UserTestBuilder withId(Long id) {
        this.id = id;
        return this;
    }

    public UserTestBuilder withEmail(String email) {
        this.email = email;
        return this;
    }

    public UserTestBuilder inactive() {
        this.active = false;
        return this;
    }

    public User build() {
        return User.builder()
            .id(id)
            .email(email)
            .username(username)
            .active(active)
            .build();
    }
}

// Usage
User user = aUser()
    .withEmail("custom@example.com")
    .inactive()
    .build();
```

## Performance Testing with JMH

```java
package com.example.benchmark;

import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;

import java.util.concurrent.TimeUnit;

@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@State(Scope.Benchmark)
@Fork(value = 2, warmups = 1)
@Warmup(iterations = 3)
@Measurement(iterations = 5)
public class UserServiceBenchmark {

    private UserService userService;

    @Setup
    public void setup() {
        // Initialize test data
        userService = new UserService();
    }

    @Benchmark
    public void benchmarkFindUser() {
        userService.findById(1L);
    }

    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
            .include(UserServiceBenchmark.class.getSimpleName())
            .build();
        new Runner(opt).run();
    }
}
```

## Test Containers Shared Instance

```java
package com.example.test;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

public abstract class AbstractIntegrationTest {

    static final PostgreSQLContainer<?> postgres;

    static {
        postgres = new PostgreSQLContainer<>("postgres:16-alpine")
            .withReuse(true);
        postgres.start();
    }

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }
}
```

## Quick Reference

| Annotation | Purpose |
|-----------|---------|
| `@Test` | Mark test method |
| `@BeforeEach` | Run before each test |
| `@AfterEach` | Run after each test |
| `@DisplayName` | Readable test name |
| `@ParameterizedTest` | Data-driven tests |
| `@ExtendWith` | Register extensions |
| `@SpringBootTest` | Full application context |
| `@WebMvcTest` | Test MVC layer only |
| `@DataJpaTest` | Test repository layer |
| `@MockBean` | Mock Spring bean |
| `@WithMockUser` | Mock authenticated user |
| `assertThat()` | AssertJ fluent assertions |
| `verify()` | Mockito verification |
