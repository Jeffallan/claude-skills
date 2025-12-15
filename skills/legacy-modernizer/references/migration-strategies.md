# Migration Strategies

> Reference for: Legacy Modernizer
> Load when: Database, UI, API, framework migrations, technology upgrades

## Database Migration Strategy

### Dual-Write Pattern

```python
# Phase 1: Dual write to both databases
class DualWriteUserRepository:
    def __init__(self, legacy_db, modern_db: AsyncSession):
        self.legacy = legacy_db
        self.modern = modern_db

    async def create_user(self, user_data: dict) -> User:
        # Write to modern DB (source of truth)
        async with self.modern.begin():
            user = User(**user_data)
            self.modern.add(user)
            await self.modern.flush()

        # Async write to legacy for backwards compatibility
        asyncio.create_task(self._sync_to_legacy(user))

        return user

    async def _sync_to_legacy(self, user: User):
        try:
            await asyncio.to_thread(
                self.legacy.execute,
                "INSERT INTO users VALUES (?, ?, ?)",
                user.id, user.email, user.name,
            )
        except Exception as e:
            # Log but don't fail - modern DB is source of truth
            logger.error(f"Legacy sync failed: {e}", extra={"user_id": user.id})

# Phase 2: Dual read with lazy migration
async def get_user(self, user_id: int) -> User | None:
    # Try modern DB first
    user = await self.modern.get(User, user_id)
    if user:
        return user

    # Fallback to legacy, then migrate
    legacy_user = await self._read_from_legacy(user_id)
    if legacy_user:
        return await self._lazy_migrate(legacy_user)

    return None

async def _lazy_migrate(self, legacy_data: dict) -> User:
    """Migrate user from legacy to modern on read"""
    user = User(**legacy_data)
    async with self.modern.begin():
        self.modern.add(user)
        await self.modern.flush()
    return user

# Phase 3: Stop dual-write after 100% migrated
async def create_user(self, user_data: dict) -> User:
    if migration_complete:
        # Only write to modern DB
        return await self._create_modern(user_data)
    else:
        # Continue dual-write during migration
        return await self._create_dual_write(user_data)
```

### Schema Evolution

```python
# Expand-Contract pattern for schema changes
# Step 1: EXPAND - Add new column (nullable or default value)
"""
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
"""

# Step 2: WRITE BOTH - Application writes to both old and new
class User(Base):
    __tablename__ = "users"

    # Old field (deprecated)
    is_confirmed = Column(Boolean, default=False)

    # New field
    email_verified = Column(Boolean, default=False)

    def set_verified(self, verified: bool):
        # Write to both during migration
        self.email_verified = verified
        self.is_confirmed = verified  # Backwards compatibility

# Step 3: MIGRATE - Backfill existing data
"""
UPDATE users
SET email_verified = is_confirmed
WHERE email_verified IS NULL;
"""

# Step 4: READ NEW - Application reads from new column
@property
def is_email_verified(self) -> bool:
    # Prefer new field, fallback to old
    return self.email_verified or self.is_confirmed

# Step 5: CONTRACT - Remove old column (after all code deployed)
"""
ALTER TABLE users DROP COLUMN is_confirmed;
"""
```

## API Versioning Migration

```python
# Version 1: Legacy API
@app.get("/api/users/{user_id}")
async def get_user_v1(user_id: int):
    user = await users.get(user_id)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created": user.created_at.isoformat(),
    }

# Version 2: New API with improved structure
@app.get("/api/v2/users/{user_id}")
async def get_user_v2(user_id: int):
    user = await users.get(user_id)
    return {
        "data": {
            "id": user.id,
            "type": "user",
            "attributes": {
                "name": user.name,
                "email": user.email,
            },
            "metadata": {
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
        }
    }

# Content negotiation for gradual migration
@app.get("/api/users/{user_id}")
async def get_user(
    user_id: int,
    accept_version: str = Header(default="1"),
):
    user = await users.get(user_id)

    if accept_version == "2":
        return format_user_v2(user)
    else:
        return format_user_v1(user)

# Deprecation headers
response.headers["X-API-Deprecation"] = "V1 deprecated, migrate to V2"
response.headers["X-API-Sunset"] = "2024-12-31"
```

## Framework Migration (Flask to FastAPI)

```python
# Original Flask code
from flask import Flask, request, jsonify

flask_app = Flask(__name__)

@flask_app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

# Step 1: Run both frameworks (different ports)
# Step 2: Create FastAPI equivalent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

fastapi_app = FastAPI()

class UserCreate(BaseModel):
    email: str
    name: str

@fastapi_app.post("/users", status_code=201)
async def create_user(user_data: UserCreate):
    async with db.begin():
        user = User(**user_data.model_dump())
        db.add(user)
        await db.flush()
        return user.to_dict()

# Step 3: Proxy layer routes traffic between frameworks
from fastapi import Request
import httpx

@fastapi_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_flask(request: Request, path: str):
    """Route unmigrated endpoints to Flask"""
    migrated_endpoints = {"/users", "/orders", "/products"}

    if f"/{path}" in migrated_endpoints:
        # Handle in FastAPI (new)
        return await handle_in_fastapi(request, path)
    else:
        # Proxy to Flask (legacy)
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"http://localhost:5000/{path}",
                content=await request.body(),
                headers=dict(request.headers),
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

# Step 4: Gradually migrate endpoints, update routing
# Step 5: Shutdown Flask once all endpoints migrated
```

## Frontend Migration (jQuery to React)

```javascript
// Step 1: Load both frameworks
// index.html
<script src="jquery.min.js"></script>
<script src="legacy-app.js"></script>
<div id="react-root"></div>
<script src="react-bundle.js"></script>

// Step 2: Create React wrapper for legacy components
function LegacyWrapper({ selector, onMount }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      // Initialize legacy jQuery component
      $(ref.current).find(selector).legacyPlugin();
      onMount?.();
    }

    return () => {
      // Cleanup
      $(ref.current).find(selector).legacyPlugin('destroy');
    };
  }, [selector]);

  return <div ref={ref} dangerouslySetInnerHTML={{ __html: getLegacyHTML() }} />;
}

// Step 3: Replace components incrementally
function UserTable() {
  const useLegacy = !useFeatureFlag('react-user-table');

  if (useLegacy) {
    return <LegacyWrapper selector="#user-table" />;
  }

  // Modern React component
  return (
    <Table>
      {users.map(user => (
        <UserRow key={user.id} user={user} />
      ))}
    </Table>
  );
}

// Step 4: Share state between jQuery and React
window.appState = new Proxy({
  currentUser: null,
  notifications: [],
}, {
  set(target, prop, value) {
    target[prop] = value;
    // Notify React of changes
    window.dispatchEvent(new CustomEvent('appStateChange', {
      detail: { prop, value }
    }));
    return true;
  }
});

// React hook to sync with global state
function useAppState(key) {
  const [value, setValue] = useState(window.appState[key]);

  useEffect(() => {
    function handleChange(e) {
      if (e.detail.prop === key) {
        setValue(e.detail.value);
      }
    }
    window.addEventListener('appStateChange', handleChange);
    return () => window.removeEventListener('appStateChange', handleChange);
  }, [key]);

  return value;
}
```

## Microservices Extraction

```python
# Monolith with tightly coupled modules
class MonolithApp:
    def process_order(self, order_data):
        # Payment logic
        payment = self.charge_card(order_data['card'])

        # Inventory logic
        self.update_inventory(order_data['items'])

        # Notification logic
        self.send_email(order_data['user_email'])

# Step 1: Identify bounded contexts and extract
# New Payment Service (separate codebase/deployment)
from fastapi import FastAPI

payment_service = FastAPI()

@payment_service.post("/payments")
async def process_payment(payment: PaymentRequest):
    charge = await stripe.create_charge(payment.amount, payment.card)
    await db.save_payment(charge.id, payment.order_id)
    return {"payment_id": charge.id}

# Step 2: Modify monolith to call extracted service
class MonolithApp:
    def __init__(self, payment_client: PaymentClient):
        self.payment_client = payment_client

    async def process_order(self, order_data):
        # Call payment microservice instead of local code
        payment = await self.payment_client.process_payment(
            amount=order_data['total'],
            card=order_data['card'],
            order_id=order_data['id'],
        )

        # Rest still in monolith (for now)
        self.update_inventory(order_data['items'])
        self.send_email(order_data['user_email'])

# Step 3: Event-driven communication
# Payment service publishes events
@payment_service.post("/payments")
async def process_payment(payment: PaymentRequest):
    charge = await stripe.create_charge(payment.amount, payment.card)

    # Publish event instead of direct coupling
    await event_bus.publish("payment.completed", {
        "payment_id": charge.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
    })

    return {"payment_id": charge.id}

# Inventory service subscribes to events
@event_bus.subscribe("payment.completed")
async def handle_payment_completed(event):
    order = await orders.get(event['order_id'])
    await inventory.reduce_stock(order.items)

# Monolith is now just orchestration
async def process_order(order_data):
    # Fire and forget - services are autonomous
    await event_bus.publish("order.created", order_data)
```

## Language Version Upgrade (Python 2 to 3)

```python
# Use six library for compatibility during migration
import six

# Works in both Python 2 and 3
if six.PY2:
    from urllib2 import urlopen
else:
    from urllib.request import urlopen

# Gradual type hint adoption
def process_user(user_id):  # type: (int) -> dict
    """Python 2 compatible type hints"""
    return {"id": user_id}

# After Python 3 only
def process_user(user_id: int) -> dict:
    """Modern type hints"""
    return {"id": user_id}

# String handling migration
# Python 2
user_name = unicode(raw_name, 'utf-8')

# Compatibility
user_name = six.text_type(raw_name)

# Python 3
user_name = str(raw_name)
```

## Quick Reference

| Migration Type | Strategy | Key Considerations |
|----------------|----------|-------------------|
| Database | Dual-write, lazy migration | Data consistency, rollback |
| API | Versioning, content negotiation | Client migration timeline |
| Framework | Proxy, parallel run | Performance overhead |
| Frontend | Incremental, shared state | Bundle size, compatibility |
| Microservices | Extract, events | Network reliability, data |
| Language | Compatibility layer | Dependency updates |
