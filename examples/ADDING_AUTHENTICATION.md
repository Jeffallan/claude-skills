# Adding Authentication

> **Skills used:** Secure Code Guardian (`secure-code-guardian`), Spring Boot Engineer (`spring-boot-engineer`),
> Test Master (`test-master`), Security Reviewer (`security-reviewer`)
> **Estimated time:** 2-3 hours
> **Difficulty:** Intermediate

## Overview

An existing Spring Boot 3 API has no login at all. Every endpoint is open. This walkthrough adds JWT-based
authentication: first a threat model, then the Spring Security 6 setup, then tests, then an audit pass over the
result.

---

## Step 1: Threat model with Secure Code Guardian

**Prompt:**

```text
We are adding JWT authentication to a Spring Boot API. Threat-model this change: what can go wrong, and which
controls do we need from day one?
```

**What the skill does:** `secure-code-guardian` starts with a threat model before any code, then designs the
controls. Its validation checkpoints name the tests to run later: token expiration, brute-force protection, and
error messages that do not reveal whether a user exists.

**Output excerpt:**

| Threat                                    | Control                                                             |
| ----------------------------------------- | ------------------------------------------------------------------- |
| Stolen token used from another machine    | Short token lifetime (15 minutes), refresh token in an httpOnly cookie |
| Caller reads another user's data          | Check ownership in the service layer, not only in the filter chain  |
| Login errors reveal valid usernames       | One error message for both bad username and bad password            |
| Token accepted after logout               | Stateless tokens stay valid until expiry, so keep expiry short      |

One row needs a decision: the refresh token travels in an httpOnly cookie, and every later step has to match
that choice. Write it down now, because a mismatch between where a token is sent and where it is read is a
common way this setup breaks.

---

## Step 2: Configure Spring Security with Spring Boot Engineer

**Prompt:**

```text
Configure Spring Security 6 for this API as a JWT resource server. Only /api/auth/** and /actuator/health are
public. Everything else needs a valid token.
```

**What the skill does:** `spring-boot-engineer` sets up the filter chain in its Secure step, following the
pattern in its own `references/security.md`, and then runs `./mvnw test` before moving on.

**Output excerpt:**

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}
```

Two details matter. CSRF is off because the API is stateless and sends no session cookie; that reasoning goes in
the commit message. Passwords use BCrypt with a cost of 12, the same encoder this project's security reference
uses.

---

## Step 3: Test the rules with Test Master

**Prompt:**

```text
Write MockMvc tests for the security rules: a request with no token gets 401, a request with a valid JWT gets
200, and /actuator/health stays public.
```

**What the skill does:** `test-master` writes tests from the rules in step 1. The `jwt()` request post-processor
from `spring-security-test` builds a test token, so the tests need no real identity provider.

**Output excerpt:**

```java
@WebMvcTest(TaskController.class)
@Import(SecurityConfig.class)
class TaskControllerSecurityTests {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private TaskService taskService;

    @Test
    void listTasksWithoutTokenIsUnauthorized() throws Exception {
        mockMvc.perform(get("/api/tasks"))
            .andExpect(status().isUnauthorized());
    }

    @Test
    void listTasksWithJwtSucceeds() throws Exception {
        mockMvc.perform(get("/api/tasks")
                .with(jwt().jwt(token -> token.subject("user-42"))))
            .andExpect(status().isOk());
    }
}
```

---

## Step 4: Audit with Security Reviewer

**Prompt:**

```text
Audit the authentication code we just added. List findings by severity, with the file and line for each one.
```

**What the skill does:** `security-reviewer` scans first, then reports. One scan it runs is
`semgrep --config=auto .`, from its own workflow. Findings come back as a short list with a fix for each, not a
pass or fail stamp.

**Output excerpt:**

| Severity | Finding                                                             | Fix                                                  |
| -------- | ------------------------------------------------------------------- | ---------------------------------------------------- |
| Medium   | Token lifetime is set in two places with two values                 | Move it to one property, `app.jwt.expiry`, and read it in both |
| Low      | Login failures are not logged                                       | Log the attempt with the username, never the password |
| Low      | `/actuator/health` shows component details to anonymous callers     | Set `management.endpoint.health.show-details=never`  |

Fix the findings, run `./mvnw test` again, and the change is ready for review.

---

## Key takeaways

1. The threat model in step 1 decided where the refresh token lives. Steps 2-4 just kept that promise.
2. The tests in step 3 encode the access rules, so a later config edit cannot open an endpoint by accident.
3. The audit in step 4 checks the finished code, not the plan. Run it last, on the code you will actually ship.
