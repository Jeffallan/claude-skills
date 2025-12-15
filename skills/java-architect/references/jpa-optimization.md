# JPA Optimization

> Reference for: Java Architect
> Load when: JPA, Hibernate, database queries, performance tuning

## Optimized Entity Design

```java
package com.example.domain.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.BatchSize;
import org.hibernate.annotations.Cache;
import org.hibernate.annotations.CacheConcurrencyStrategy;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(
    name = "users",
    indexes = {
        @Index(name = "idx_email", columnList = "email"),
        @Index(name = "idx_created_at", columnList = "created_at")
    }
)
@EntityListeners(AuditingEntityListener.class)
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @Column(nullable = false, length = 50)
    private String username;

    @Column(nullable = false)
    private Boolean active = true;

    @OneToMany(
        mappedBy = "user",
        cascade = CascadeType.ALL,
        orphanRemoval = true,
        fetch = FetchType.LAZY
    )
    @BatchSize(size = 25)
    @Builder.Default
    private List<Order> orders = new ArrayList<>();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "department_id")
    private Department department;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;

    @Version
    private Long version;

    // Helper methods
    public void addOrder(Order order) {
        orders.add(order);
        order.setUser(this);
    }

    public void removeOrder(Order order) {
        orders.remove(order);
        order.setUser(null);
    }
}
```

## Repository with Custom Queries

```java
package com.example.domain.repository;

import com.example.domain.model.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.repository.query.Param;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    // N+1 prevention with EntityGraph
    @EntityGraph(attributePaths = {"orders", "department"})
    @Query("SELECT u FROM User u WHERE u.id = :id")
    Optional<User> findByIdWithOrders(@Param("id") Long id);

    // Projection for read-only queries
    @Query("""
        SELECT new com.example.application.dto.UserSummary(
            u.id, u.email, u.username, COUNT(o)
        )
        FROM User u
        LEFT JOIN u.orders o
        WHERE u.active = true
        GROUP BY u.id, u.email, u.username
        """)
    List<UserSummary> findActiveUsersSummary();

    // Fetch join to avoid N+1
    @Query("""
        SELECT DISTINCT u FROM User u
        LEFT JOIN FETCH u.orders
        WHERE u.department.id = :deptId
        """)
    List<User> findByDepartmentWithOrders(@Param("deptId") Long deptId);

    // Pagination with count query optimization
    @Query(
        value = "SELECT u FROM User u WHERE u.active = true",
        countQuery = "SELECT COUNT(u) FROM User u WHERE u.active = true"
    )
    Page<User> findActiveUsers(Pageable pageable);

    // Batch update
    @Modifying
    @Query("UPDATE User u SET u.active = false WHERE u.createdAt < :date")
    int deactivateOldUsers(@Param("date") Instant date);

    // Native query for complex operations
    @Query(
        value = """
            SELECT u.* FROM users u
            WHERE u.id IN (
                SELECT DISTINCT o.user_id
                FROM orders o
                WHERE o.total > :amount
            )
            """,
        nativeQuery = true
    )
    List<User> findUsersWithLargeOrders(@Param("amount") Double amount);
}
```

## DTO Projections

```java
package com.example.application.dto;

// Interface-based projection
public interface UserProjection {
    Long getId();
    String getEmail();
    String getUsername();
    DepartmentProjection getDepartment();

    interface DepartmentProjection {
        String getName();
    }
}

// Class-based projection (constructor expression)
public record UserSummary(
    Long id,
    String email,
    String username,
    Long orderCount
) {}

// Dynamic projection
public interface UserRepository extends JpaRepository<User, Long> {
    <T> List<T> findByActive(boolean active, Class<T> type);
}

// Usage
List<UserProjection> users = userRepository.findByActive(true, UserProjection.class);
```

## Query Optimization Patterns

```java
package com.example.application.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserQueryService {

    private final UserRepository userRepository;
    private final EntityManager entityManager;

    // Batch fetching
    public List<User> findUsersWithOrders(List<Long> userIds) {
        return entityManager.createQuery("""
            SELECT DISTINCT u FROM User u
            LEFT JOIN FETCH u.orders
            WHERE u.id IN :ids
            """, User.class)
            .setParameter("ids", userIds)
            .setHint("hibernate.default_batch_fetch_size", 25)
            .getResultList();
    }

    // Pagination with total count
    public Page<UserSummary> findUsersPaged(Pageable pageable) {
        List<UserSummary> users = entityManager.createQuery("""
            SELECT new com.example.application.dto.UserSummary(
                u.id, u.email, u.username, COUNT(o)
            )
            FROM User u
            LEFT JOIN u.orders o
            GROUP BY u.id, u.email, u.username
            """, UserSummary.class)
            .setFirstResult((int) pageable.getOffset())
            .setMaxResults(pageable.getPageSize())
            .getResultList();

        Long total = entityManager.createQuery(
            "SELECT COUNT(DISTINCT u) FROM User u",
            Long.class
        ).getSingleResult();

        return new PageImpl<>(users, pageable, total);
    }

    // Stream large datasets
    @Transactional(readOnly = true)
    public void processLargeDataset() {
        try (Stream<User> stream = userRepository.streamByActiveTrue()) {
            stream
                .filter(user -> user.getOrders().size() > 10)
                .forEach(this::processUser);
        }
    }

    // Criteria API for dynamic queries
    public List<User> findUsersByCriteria(UserSearchCriteria criteria) {
        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        CriteriaQuery<User> query = cb.createQuery(User.class);
        Root<User> user = query.from(User.class);

        List<Predicate> predicates = new ArrayList<>();

        if (criteria.email() != null) {
            predicates.add(cb.like(user.get("email"), "%" + criteria.email() + "%"));
        }
        if (criteria.active() != null) {
            predicates.add(cb.equal(user.get("active"), criteria.active()));
        }
        if (criteria.createdAfter() != null) {
            predicates.add(cb.greaterThan(user.get("createdAt"), criteria.createdAfter()));
        }

        query.where(predicates.toArray(new Predicate[0]));
        return entityManager.createQuery(query).getResultList();
    }
}
```

## Batch Operations

```java
@Service
@RequiredArgsConstructor
public class UserBatchService {

    private final UserRepository userRepository;
    private final EntityManager entityManager;

    @Transactional
    public void batchInsert(List<User> users) {
        int batchSize = 50;
        for (int i = 0; i < users.size(); i++) {
            entityManager.persist(users.get(i));
            if (i % batchSize == 0 && i > 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }
        entityManager.flush();
        entityManager.clear();
    }

    @Transactional
    public void batchUpdate(List<User> users) {
        int batchSize = 50;
        for (int i = 0; i < users.size(); i++) {
            entityManager.merge(users.get(i));
            if (i % batchSize == 0 && i > 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }
        entityManager.flush();
        entityManager.clear();
    }
}
```

## Second-Level Cache Configuration

```yaml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          use_query_cache: true
          region:
            factory_class: org.hibernate.cache.jcache.JCacheRegionFactory
        javax:
          cache:
            provider: org.ehcache.jsr107.EhcacheCachingProvider
            uri: classpath:ehcache.xml
```

```xml
<!-- ehcache.xml -->
<config xmlns="http://www.ehcache.org/v3">
    <cache alias="users">
        <key-type>java.lang.Long</key-type>
        <value-type>com.example.domain.model.User</value-type>
        <expiry>
            <ttl unit="minutes">10</ttl>
        </expiry>
        <resources>
            <heap unit="entries">1000</heap>
        </resources>
    </cache>
</config>
```

## Performance Monitoring

```java
@Component
@Aspect
@Slf4j
public class QueryPerformanceAspect {

    @Around("@annotation(org.springframework.data.jpa.repository.Query)")
    public Object logQueryPerformance(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            return joinPoint.proceed();
        } finally {
            long duration = System.currentTimeMillis() - start;
            if (duration > 1000) {
                log.warn("Slow query detected: {} took {}ms",
                    joinPoint.getSignature(), duration);
            }
        }
    }
}
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `@EntityGraph` | Prevent N+1 queries |
| `JOIN FETCH` | Eager fetch associations |
| DTO Projection | Read-only queries |
| `@BatchSize` | Batch fetch collections |
| `@Query` with pagination | Large datasets |
| `@Modifying` | Bulk updates/deletes |
| Criteria API | Dynamic queries |
| Second-level cache | Frequently accessed data |
| Stream API | Process large results |
| `readOnly = true` | Optimization hint |
