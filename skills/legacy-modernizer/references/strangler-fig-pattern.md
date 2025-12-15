# Strangler Fig Pattern

> Reference for: Legacy Modernizer
> Load when: Incremental replacement, facade layer, routing between old and new

## Pattern Overview

The strangler fig pattern gradually replaces legacy systems by incrementally building new functionality around the old system, eventually "strangling" it out of existence.

```
Legacy System → Facade/Router → New System
     ↓              ↓               ↓
  Old Code    Feature Flags    Modern Code
     ↓              ↓               ↓
  Phase 1:    Route 10%       Validate New
  Phase 2:    Route 50%       Monitor Metrics
  Phase 3:    Route 100%      Remove Legacy
```

## API Gateway Strangler

```python
# Facade layer routing requests to old/new systems
from fastapi import FastAPI, Request
from typing import Literal

app = FastAPI()

MIGRATION_CONFIG = {
    "users.create": {"new_percentage": 100, "module": "new"},
    "users.update": {"new_percentage": 50, "module": "new"},
    "users.list": {"new_percentage": 10, "module": "new"},
    "orders.create": {"new_percentage": 0, "module": "legacy"},
}

@app.post("/api/users")
async def create_user(request: Request):
    feature = "users.create"
    config = MIGRATION_CONFIG.get(feature, {"new_percentage": 0})

    # Feature flag + canary rollout
    use_new = should_use_new_system(request, config["new_percentage"])

    if use_new:
        return await new_user_service.create(request)
    else:
        return await legacy_user_service.create(request)

def should_use_new_system(request: Request, percentage: int) -> bool:
    """Determine routing based on percentage + user attributes"""
    if percentage == 0:
        return False
    if percentage == 100:
        return True

    # Canary: use user_id hash for consistent routing
    user_id = request.headers.get("X-User-Id", "")
    hash_val = hash(user_id) % 100
    return hash_val < percentage
```

## Service Extraction with Adapter

```python
# Legacy monolith code
class LegacyOrderService:
    def create_order(self, user_id: int, items: list) -> dict:
        # Complex legacy logic with database calls
        order = {"id": 123, "user_id": user_id, "items": items}
        self.db.execute("INSERT INTO orders ...")
        return order

# Step 1: Extract interface
from abc import ABC, abstractmethod

class OrderServiceInterface(ABC):
    @abstractmethod
    async def create_order(self, user_id: int, items: list) -> dict:
        pass

# Step 2: Adapter for legacy code
class LegacyOrderAdapter(OrderServiceInterface):
    def __init__(self, legacy_service: LegacyOrderService):
        self.legacy = legacy_service

    async def create_order(self, user_id: int, items: list) -> dict:
        # Wrap synchronous legacy in async
        return await asyncio.to_thread(
            self.legacy.create_order, user_id, items
        )

# Step 3: New implementation
class ModernOrderService(OrderServiceInterface):
    def __init__(self, db: AsyncSession, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus

    async def create_order(self, user_id: int, items: list) -> dict:
        async with self.db.begin():
            order = Order(user_id=user_id, items=items)
            self.db.add(order)
            await self.db.flush()

            # Emit event for other services
            await self.event_bus.publish(
                "order.created", {"order_id": order.id}
            )
            return order.to_dict()

# Step 4: Feature flag routing
async def get_order_service(
    request: Request,
    db: AsyncSession,
) -> OrderServiceInterface:
    if feature_flags.is_enabled("modern_orders", request):
        return ModernOrderService(db, event_bus)
    else:
        return LegacyOrderAdapter(legacy_order_service)
```

## Database Strangler Pattern

```python
# Dual-write to old and new databases during migration
class DualWriteOrderRepository:
    def __init__(
        self,
        legacy_db: Connection,
        modern_db: AsyncSession,
    ):
        self.legacy_db = legacy_db
        self.modern_db = modern_db

    async def create(self, order_data: dict) -> Order:
        # Write to new system (source of truth)
        async with self.modern_db.begin():
            order = Order(**order_data)
            self.modern_db.add(order)
            await self.modern_db.flush()
            order_id = order.id

        # Background sync to legacy (best effort)
        try:
            await self._sync_to_legacy(order_id, order_data)
        except Exception as e:
            # Log but don't fail - new DB is source of truth
            logger.error(f"Legacy sync failed: {e}")

        return order

    async def get(self, order_id: int) -> Order | None:
        # Read from new system
        result = await self.modern_db.get(Order, order_id)
        if result:
            return result

        # Fallback to legacy if not found (migration in progress)
        legacy_data = await self._read_from_legacy(order_id)
        if legacy_data:
            # Lazy migration: move to new DB
            return await self._migrate_order(legacy_data)

        return None
```

## UI Component Strangler

```typescript
// React: Replace legacy jQuery components incrementally
import { lazy, Suspense } from 'react';

// Feature flag component wrapper
function StranglerComponent({
  feature,
  legacySelector,
  NewComponent,
  ...props
}) {
  const useNew = useFeatureFlag(feature);

  if (useNew) {
    return (
      <Suspense fallback={<Spinner />}>
        <NewComponent {...props} />
      </Suspense>
    );
  }

  // Render legacy jQuery component
  return <LegacyWrapper selector={legacySelector} />;
}

// Usage
const ModernUserTable = lazy(() => import('./UserTable'));

export function UserManagement() {
  return (
    <StranglerComponent
      feature="modern-user-table"
      legacySelector="#legacy-user-table"
      NewComponent={ModernUserTable}
      onUserClick={handleUserClick}
    />
  );
}
```

## Event Interception

```python
# Intercept events from legacy system
from typing import Callable
import functools

def intercept_legacy_event(event_name: str):
    """Decorator to intercept and modernize legacy events"""
    def decorator(handler: Callable):
        @functools.wraps(handler)
        async def wrapper(*args, **kwargs):
            # Transform legacy event to modern format
            modern_event = transform_legacy_event(event_name, args, kwargs)

            # Emit to new event bus
            await event_bus.publish(event_name, modern_event)

            # Still call legacy handler (during transition)
            return await handler(*args, **kwargs)
        return wrapper
    return decorator

# Apply to legacy code
@intercept_legacy_event("user.registered")
async def legacy_user_registration_handler(user_data):
    # Old code continues to work
    send_welcome_email(user_data["email"])

# New services can now subscribe to modernized events
@event_bus.subscribe("user.registered")
async def modern_analytics_handler(event):
    await analytics.track_registration(event["user_id"])
```

## Migration Phases

```python
# Phase tracking and rollback
class MigrationPhase:
    def __init__(self, name: str, percentage: int, metrics: dict):
        self.name = name
        self.percentage = percentage
        self.metrics = metrics

    async def validate(self) -> bool:
        """Check if phase is successful before proceeding"""
        for metric, threshold in self.metrics.items():
            current = await monitoring.get_metric(metric)
            if current > threshold:
                await self.rollback()
                return False
        return True

    async def rollback(self):
        """Instant rollback to previous phase"""
        await feature_flags.set_percentage(self.name, self.percentage - 10)
        await alerts.send(f"Rollback triggered for {self.name}")

# Migration plan
PHASES = [
    MigrationPhase("orders_v2", 0, {}),  # Setup
    MigrationPhase("orders_v2", 10, {"error_rate": 0.01}),  # Canary
    MigrationPhase("orders_v2", 50, {"error_rate": 0.005}),  # Ramp
    MigrationPhase("orders_v2", 100, {"error_rate": 0.001}),  # Full
]
```

## Quick Reference

| Stage | Actions | Validation |
|-------|---------|------------|
| Setup | Create facade, feature flags | Smoke tests pass |
| Canary | Route 10% traffic | Error rate < 1% |
| Ramp | Route 50% traffic | Performance parity |
| Full | Route 100% traffic | All metrics green |
| Cleanup | Remove legacy code | Legacy unused 30 days |
