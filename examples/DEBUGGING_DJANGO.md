# Django API Debugging: Intermittent 500 Errors

> **Skills used:** `debugging-wizard`, `django-expert`, `test-master`, `code-reviewer`
> **Difficulty:** Intermediate
> **Language:** Python
> **Workflow:** [Bug Fixing](../SKILLS_GUIDE.md#bug-fixing)

## Overview

A multi-tenant Django REST Framework application serves report data through `/api/v1/reports/`. The `TenantMiddleware` (`reports/middleware.py`) resolves the current tenant via a database lookup on every request, while a `post_save` signal (`analytics/signals.py`) updates a denormalized `report_count` on the `Tenant` row. Under concurrent load in production (PostgreSQL), users encounter intermittent `OperationalError: could not obtain lock on row in relation tenants_tenant`, resulting in 500 responses.

### Why Multi-Skill?

Database lock contention spans infrastructure behavior, ORM semantics, testing strategy, and code quality:

- **debugging-wizard** -- systematic root cause isolation before any code changes.
- **django-expert** -- idiomatic Django fixes using `F()` expressions and caching.
- **test-master** -- regression tests verifying atomicity under concurrency.
- **code-reviewer** -- audit for correctness, security, and missed edge cases.

---

## Step 1 -- Root Cause Analysis with `debugging-wizard`

### Prompt

> I'm getting intermittent 500 errors on my Django API endpoint `/api/v1/reports/`. The error is `OperationalError: could not obtain lock on row in relation tenants_tenant` in production (PostgreSQL). It happens under load but not in local testing.

### Skill Output

#### Root Cause

The `post_save` signal acquires an **exclusive lock** on the tenant row every time a report is saved:

```python
# analytics/signals.py:16-18
tenant = instance.tenant
tenant.report_count = Report.objects.filter(tenant=tenant).count()
tenant.save()  # EXCLUSIVE LOCK acquired here
```

Simultaneously, `TenantMiddleware` acquires a **shared lock** on the same row for every request:

```python
# reports/middleware.py:20
request.tenant = Tenant.objects.get(subdomain=subdomain)
```

Under concurrent load: Request A (POST) creates a report, triggers `tenant.save()` (exclusive lock). Request B (any endpoint) enters middleware, issues `SELECT` (shared lock) -- blocked by Request A. If `lock_timeout` fires, Request B gets `OperationalError`.

Compounding factors: the signal performs a full `COUNT(*)` before writing (extending lock hold), and the middleware has zero caching (documented bug at `reports/middleware.py:8-10`).

#### Evidence

- **Error message** confirms lock target is `tenants_tenant` (`tenants/models.py:17`, `db_table = 'tenants_tenant'`).
- **Intermittent nature** -- only under load, consistent with concurrent lock timing.
- **Stack trace** passes through `analytics/signals.py` into `tenant.save()`, confirming the exclusive lock origin.
- **Middleware source** (`reports/middleware.py:20`) confirms no caching on `Tenant.objects.get()`.

#### Fix

**Fix A** -- Atomic `F()` expression in `analytics/signals.py`:

```python
@receiver(post_save, sender=Report)
def update_tenant_report_count(sender, instance, created, **kwargs):
    if created:
        Tenant.objects.filter(pk=instance.tenant_id).update(
            report_count=F('report_count') + 1
        )
```

**Fix B** -- Cached tenant lookup in `reports/middleware.py` with 5-minute TTL.

#### Prevention

- Regression test with `TransactionTestCase` and `ThreadPoolExecutor` for concurrent creates.
- Coding rule: never call `.save()` on a full model instance inside a signal -- use `.update()` with `F()`.
- Cache invalidation signal when tenant data changes.

### What This Skill Provided

The debugging-wizard traced the 500 error from the generic `OperationalError` back to two specific code locations (`reports/middleware.py:20` and `analytics/signals.py:18`), identifying read-write lock contention as the root cause rather than a simple query bug.

---

## Step 2 -- Django-Specific Fix with `django-expert`

### Prompt

> Fix the lock contention issue found in `analytics/signals.py` and `reports/middleware.py`. Use `F()` expressions, cached tenant lookup, and `update()` instead of `save()`.

### Skill Output

#### 1. Model Definitions with Indexes

`Tenant` model (`tenants/models.py`) already has `subdomain` with `unique=True, db_index=True` -- correct. Add composite indexes to `Report` (`reports/models.py`):

```python
class Meta:
    db_table = 'reports_report'
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=['tenant', 'status']),
        models.Index(fields=['tenant', '-created_at']),
    ]
```

#### 2. Serializers with Validation

Add title validation to `reports/serializers.py`:

```python
def validate_title(self, value):
    if not value.strip():
        raise serializers.ValidationError("Title cannot be blank.")
    return value.strip()
```

#### 3. ViewSet with Permissions

`ReportViewSet` (`reports/views.py`) already uses `select_related('author')` and tenant scoping. No changes needed -- the fix lives in the signal and middleware layers.

#### 4. Signal Fix -- Atomic Update with `F()` Expression

```python
# analytics/signals.py -- FIXED
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from reports.models import Report
from tenants.models import Tenant

@receiver(post_save, sender=Report)
def update_tenant_report_count(sender, instance, created, **kwargs):
    """Atomically increment report_count on creation only."""
    if created:
        Tenant.objects.filter(pk=instance.tenant_id).update(
            report_count=F('report_count') + 1
        )

@receiver(post_delete, sender=Report)
def decrement_tenant_report_count(sender, instance, **kwargs):
    """Atomically decrement report_count on deletion."""
    Tenant.objects.filter(pk=instance.tenant_id).update(
        report_count=F('report_count') - 1
    )
```

| Aspect | Before (buggy) | After (fixed) |
|--------|----------------|---------------|
| SQL | `SELECT COUNT(*)` + full-row `UPDATE` | Single `UPDATE ... SET report_count = report_count + 1` |
| Lock duration | Long (aggregate + full write) | Minimal (single atomic update) |
| Fires on | Every save | Only `created=True` |
| Deletion | Not handled (count drifts) | `post_delete` decrements |

#### 5. Middleware Fix -- Cached Tenant Lookup

```python
# reports/middleware.py -- FIXED
from django.core.cache import cache
from tenants.models import Tenant

class TenantMiddleware:
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        subdomain = self._extract_subdomain(request)
        if subdomain:
            request.tenant = self._get_tenant(subdomain)
        return self.get_response(request)

    def _get_tenant(self, subdomain):
        cache_key = f"tenant:subdomain:{subdomain}"
        tenant = cache.get(cache_key)
        if tenant is None:
            tenant = Tenant.objects.get(subdomain=subdomain)
            cache.set(cache_key, tenant, self.CACHE_TTL)
        return tenant

    def _extract_subdomain(self, request):
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        return parts[0] if len(parts) > 2 else None
```

#### 6. Cache Invalidation Signal

```python
# tenants/signals.py -- invalidate cache on tenant update
@receiver(post_save, sender=Tenant)
def invalidate_tenant_cache(sender, instance, **kwargs):
    cache.delete(f"tenant:subdomain:{instance.subdomain}")
```

#### Query Optimization Note

Per-request queries drop from 4 (middleware SELECT + signal COUNT + signal UPDATE + viewset) to 2 (cache hit + viewset), with the signal UPDATE being a lightweight atomic increment.

### What This Skill Provided

The django-expert applied ORM-specific knowledge -- `F()` expressions for atomic updates, `update()` vs `save()` semantics, composite indexes, and Django cache framework patterns -- to eliminate lock contention at its source.

---

## Step 3 -- Regression Tests with `test-master`

### Prompt

> Write regression tests for the lock contention fixes. Test `F()` expression atomicity, tenant cache behavior, and concurrent report creation.

### Skill Output

**Testing Mode: [Test] -- Functional Correctness**

#### 1. Test Scope and Approach

| Area | Type | What We Test |
|------|------|-------------|
| Signal atomicity | Unit | `F()` increment correctness under sequential creates |
| Signal guard | Unit | Signal only fires on `created=True` |
| Deletion handling | Unit | `post_delete` decrements count |
| F() database-level ops | Unit | Increment uses DB value, not stale Python value |
| Middleware caching | Unit | Second request uses cache (zero queries) |
| Concurrent creates | Integration | 20 simultaneous creates yield correct count |

#### 2. Test Cases with Expected Outcomes

```python
# tests/test_signals.py
class TestReportCountSignal(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(subdomain='acme', name='Acme Corp', report_count=0)
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_report_creation_increments_count(self):
        Report.objects.create(tenant=self.tenant, author=self.user, title='Q1 Report')
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.report_count, 1)

    def test_report_update_does_not_increment_count(self):
        report = Report.objects.create(tenant=self.tenant, author=self.user, title='Draft')
        report.title = 'Final Version'
        report.save()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.report_count, 1)  # unchanged

    def test_report_deletion_decrements_count(self):
        report = Report.objects.create(tenant=self.tenant, author=self.user, title='Temp')
        report.delete()
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.report_count, 0)

    def test_f_expression_uses_database_value(self):
        """F() uses DB value, not stale Python value."""
        Tenant.objects.filter(pk=self.tenant.pk).update(report_count=42)
        Report.objects.create(tenant=self.tenant, author=self.user, title='Test')
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.report_count, 43)  # 42 + 1

    def test_uses_update_not_save(self):
        """Verify UPDATE...SET count=count+1 pattern, not full save."""
        with CaptureQueriesContext(connection) as ctx:
            Report.objects.create(tenant=self.tenant, author=self.user, title='Check')
        tenant_updates = [q['sql'] for q in ctx.captured_queries
                          if 'tenants_tenant' in q['sql'] and 'UPDATE' in q['sql']]
        self.assertEqual(len(tenant_updates), 1)
        self.assertIn('+', tenant_updates[0])

class TestReportCountConcurrency(TransactionTestCase):
    """Uses TransactionTestCase -- threads need committed data."""

    def test_concurrent_creates_no_lost_counts(self):
        tenant = Tenant.objects.create(subdomain='acme', name='Acme Corp', report_count=0)
        user = User.objects.create_user(username='testuser', password='testpass123')

        def create_report(i):
            close_old_connections()
            Report.objects.create(tenant_id=tenant.pk, author=user, title=f'Report {i}')

        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(create_report, range(20)))
        tenant.refresh_from_db()
        self.assertEqual(tenant.report_count, 20)
```

```python
# tests/test_middleware.py
class TestTenantMiddleware(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(subdomain='acme', name='Acme Corp')
        self.middleware = TenantMiddleware(get_response=lambda r: r)
        cache.clear()

    def test_resolves_tenant_from_subdomain(self):
        request = self.factory.get('/', HTTP_HOST='acme.example.com')
        self.middleware(request)
        self.assertEqual(request.tenant.pk, self.tenant.pk)

    def test_caches_tenant_after_first_lookup(self):
        self.middleware(self.factory.get('/', HTTP_HOST='acme.example.com'))
        with self.assertNumQueries(0):
            request2 = self.factory.get('/', HTTP_HOST='acme.example.com')
            self.middleware(request2)
            self.assertEqual(request2.tenant.pk, self.tenant.pk)

    def test_cache_invalidation_on_tenant_update(self):
        self.middleware(self.factory.get('/', HTTP_HOST='acme.example.com'))
        self.tenant.name = 'Updated'
        self.tenant.save()  # triggers invalidation signal
        request2 = self.factory.get('/', HTTP_HOST='acme.example.com')
        self.middleware(request2)
        self.assertEqual(request2.tenant.name, 'Updated')
```

#### 3. Coverage Analysis

| File | Covered | Gap |
|------|---------|-----|
| `analytics/signals.py` | Full | None -- `created=True`, `created=False`, deletion all tested |
| `reports/middleware.py` | 20/22 | Missing: `Tenant.DoesNotExist` exception path |
| `tenants/signals.py` | Full | Covered via `test_cache_invalidation_on_tenant_update` |

#### 4. Findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | **Medium** | `Tenant.DoesNotExist` unhandled in middleware -- invalid subdomain produces raw 500 |
| 2 | **Low** | Cache invalidation does not handle subdomain *changes* -- old key persists |
| 3 | **Low** | Concurrent test uses 5 workers; consider parameterizing for CI |

#### 5. Recommendations

- Implement `Http404` handling in `_get_tenant()` for unknown subdomains.
- Add `pre_save` signal to invalidate old subdomain cache key on rename.
- Add a periodic management command to reconcile `report_count` with actual `COUNT(*)`.

### What This Skill Provided

The test-master designed regression tests across sequential correctness, concurrent atomicity, and cache behavior. Coverage analysis surfaced the missing `DoesNotExist` handling -- a gap that would become the next production bug.

---

## Step 4 -- Code Review with `code-reviewer`

### Prompt

> Review the lock contention fixes in `analytics/signals.py`, `reports/middleware.py`, and `tenants/signals.py`.

### Skill Output

#### 1. Summary

The changeset replaces a read-modify-write `tenant.save()` with an atomic `F()` update, adds `post_delete` handling, and introduces cached tenant resolution in middleware. The approach is sound and targets both sides of the lock contention.

#### 2. Critical Issues (Must Fix)

**C1: Uncaught `Tenant.DoesNotExist` in middleware** (`reports/middleware.py`)

```python
# Recommended: catch and return 404
try:
    tenant = Tenant.objects.get(subdomain=subdomain)
except Tenant.DoesNotExist:
    raise Http404(f"Unknown tenant: {subdomain}")
```

#### 3. Major Issues (Should Fix)

**M1: Subdomain rename leaves stale cache** (`tenants/signals.py`)
Add `pre_save` to invalidate old subdomain key when subdomain field changes.

**M2: Bulk operations bypass signals** (`analytics/signals.py`)
`QuerySet.delete()` and `bulk_create()` skip signals. Add a reconciliation management command:

```python
for tenant in Tenant.objects.annotate(actual=Count('reports')):
    if tenant.report_count != tenant.actual:
        Tenant.objects.filter(pk=tenant.pk).update(report_count=tenant.actual)
```

#### 4. Minor Issues (Nice to Have)

- **m1:** `CACHE_TTL = 300` should be a Django setting (`TENANT_CACHE_TTL`).
- **m2:** Add type hints to middleware methods.
- **m3:** Add monitoring for cache hit rate -- `LocMemCache` is per-worker and less effective.

#### 5. Positive Feedback

- `F()` expression is the idiomatic Django approach for atomic counter updates.
- `created` guard prevents unnecessary updates on every report save.
- Good separation of concerns -- only signal and middleware layers are modified.
- `instance.tenant_id` avoids an extra SELECT to resolve the foreign key.
- Existing `select_related('author')` in `reports/views.py:14` was already optimized.

#### 6. Questions for Author

1. Is there a periodic reconciliation task for `report_count` drift?
2. What cache backend is used in production? `LocMemCache` is not shared across workers.
3. Should middleware fail open (no tenant) or fail closed (404) for unknown subdomains?

#### 7. Verdict

**Request Changes** -- Core fix is correct and well-designed. Must address C1 (uncaught `DoesNotExist`) before merge. After C1 and M1, ready to approve.

### What This Skill Provided

The code-reviewer caught issues the previous skills missed: the uncaught exception for unknown subdomains (C1 -- replacing one 500 with another), subdomain-rename cache staleness (M1), and the bulk-operation signal bypass (M2). Structured severity categories made prioritization clear.

---

## Key Takeaways

- **Lock contention hides in innocent code.** `tenant.save()` in a signal (`analytics/signals.py:18`) and `Tenant.objects.get()` in middleware (`reports/middleware.py:20`) are both correct in isolation but create a deadlock-prone bottleneck under concurrent load.

- **`F()` expressions are a correctness tool, not just an optimization.** The original read-modify-write pattern is inherently racy. `F('report_count') + 1` pushes arithmetic into a single atomic SQL statement. The test setting `report_count=42` and checking for `43` explicitly validates this.

- **Caching middleware lookups has outsized impact.** A 5-minute cache on `TenantMiddleware` eliminates thousands of queries per minute and removes shared-lock contention entirely. Cache invalidation signals handle the staleness tradeoff.

- **Multi-skill chains catch gaps that single-pass analysis misses.** Each skill surfaced issues the previous ones did not: debugging-wizard found the root cause, django-expert implemented the fix, test-master revealed missing `DoesNotExist` handling, and code-reviewer caught subdomain-rename staleness and bulk-operation drift.

- **Concurrency tests require `TransactionTestCase`.** Django's `TestCase` wraps tests in a transaction invisible to other threads. `TransactionTestCase` uses committed data, matching production behavior.
