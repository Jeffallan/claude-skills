# Refactoring Patterns

> Reference for: Legacy Modernizer
> Load when: Extract service, branch by abstraction, adapters, facades

## Branch by Abstraction

Enables large refactorings to happen incrementally without breaking existing code.

```python
# Step 1: Create abstraction
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    @abstractmethod
    async def process_payment(self, amount: float, card: str) -> str:
        """Returns transaction_id"""
        pass

# Step 2: Implement for legacy code
class LegacyPaymentProcessor(PaymentProcessor):
    async def process_payment(self, amount: float, card: str) -> str:
        # Wrap existing legacy function
        return await asyncio.to_thread(
            legacy_payment_system.charge_card, amount, card
        )

# Step 3: Implement new version
class StripePaymentProcessor(PaymentProcessor):
    def __init__(self, stripe_client):
        self.stripe = stripe_client

    async def process_payment(self, amount: float, card: str) -> str:
        charge = await self.stripe.charges.create(
            amount=int(amount * 100),
            currency="usd",
            source=card,
        )
        return charge.id

# Step 4: Replace all call sites with abstraction
class OrderService:
    def __init__(self, payment_processor: PaymentProcessor):
        self.payment = payment_processor

    async def checkout(self, cart, card):
        # Now works with either implementation
        tx_id = await self.payment.process_payment(cart.total, card)
        return await self.create_order(cart, tx_id)

# Step 5: Switch implementation via dependency injection
def get_payment_processor() -> PaymentProcessor:
    if feature_flags.is_enabled("stripe_payments"):
        return StripePaymentProcessor(stripe_client)
    return LegacyPaymentProcessor()
```

## Extract Service Pattern

```python
# Before: Monolithic order processing
class OrderController:
    def create_order(self, user_id, items):
        # Validation
        if not items:
            raise ValueError("Empty order")

        # Calculate total
        total = sum(item.price * item.quantity for item in items)

        # Apply discounts
        discount = self.calculate_discount(user_id, total)
        final_total = total - discount

        # Process payment
        payment_id = self.charge_card(user_id, final_total)

        # Create order
        order = self.db.create_order(user_id, items, final_total)

        # Send notifications
        self.send_email(user_id, order.id)
        self.send_sms(user_id, "Order confirmed")

        # Update inventory
        self.update_inventory(items)

        return order

# After: Extracted services
class OrderService:
    def __init__(
        self,
        pricing: PricingService,
        payment: PaymentService,
        notification: NotificationService,
        inventory: InventoryService,
    ):
        self.pricing = pricing
        self.payment = payment
        self.notification = notification
        self.inventory = inventory

    async def create_order(self, user_id: int, items: list[OrderItem]):
        # Each service has single responsibility
        total = await self.pricing.calculate_total(items, user_id)
        payment_id = await self.payment.process(user_id, total)

        order = await self._save_order(user_id, items, total, payment_id)

        # Background tasks for non-critical operations
        background_tasks.add_task(self.notification.send_order_confirmation, order)
        background_tasks.add_task(self.inventory.update_stock, items)

        return order

# Extracted pricing service
class PricingService:
    async def calculate_total(
        self,
        items: list[OrderItem],
        user_id: int,
    ) -> Decimal:
        subtotal = sum(item.price * item.quantity for item in items)
        discount = await self.get_user_discount(user_id, subtotal)
        return subtotal - discount

    async def get_user_discount(self, user_id: int, subtotal: Decimal) -> Decimal:
        user = await self.user_repo.get(user_id)
        if user.is_premium:
            return subtotal * Decimal("0.1")  # 10% off
        return Decimal("0")
```

## Adapter Pattern for Legacy Integration

```python
# Legacy system with incompatible interface
class LegacyInventorySystem:
    def GetItemCount(self, itemCode: str) -> int:
        """Legacy method with different naming convention"""
        pass

    def DecrementStock(self, itemCode: str, qty: int) -> bool:
        pass

# Modern interface
class InventoryRepository(ABC):
    @abstractmethod
    async def get_stock_level(self, sku: str) -> int:
        pass

    @abstractmethod
    async def reduce_stock(self, sku: str, quantity: int) -> None:
        pass

# Adapter bridges the gap
class LegacyInventoryAdapter(InventoryRepository):
    def __init__(self, legacy_system: LegacyInventorySystem):
        self.legacy = legacy_system

    async def get_stock_level(self, sku: str) -> int:
        # Translate modern call to legacy method
        return await asyncio.to_thread(self.legacy.GetItemCount, sku)

    async def reduce_stock(self, sku: str, quantity: int) -> None:
        success = await asyncio.to_thread(
            self.legacy.DecrementStock, sku, quantity
        )
        if not success:
            raise StockError(f"Failed to reduce stock for {sku}")

# Modern code uses consistent interface
class OrderFulfillment:
    def __init__(self, inventory: InventoryRepository):
        self.inventory = inventory

    async def fulfill_order(self, order):
        for item in order.items:
            stock = await self.inventory.get_stock_level(item.sku)
            if stock >= item.quantity:
                await self.inventory.reduce_stock(item.sku, item.quantity)
```

## Facade Pattern for Simplification

```python
# Complex legacy subsystems
class LegacyAuthSystem:
    def authenticate_user(self, username, password): pass
    def check_permissions(self, user_id, resource): pass
    def get_user_roles(self, user_id): pass

class LegacySessionManager:
    def create_session(self, user_id): pass
    def validate_session(self, session_id): pass

class LegacyAuditLogger:
    def log_login(self, user_id, ip_address): pass

# Facade provides simple interface
class AuthFacade:
    """Simplified authentication interface wrapping legacy systems"""

    def __init__(
        self,
        auth: LegacyAuthSystem,
        sessions: LegacySessionManager,
        audit: LegacyAuditLogger,
    ):
        self.auth = auth
        self.sessions = sessions
        self.audit = audit

    async def login(
        self,
        username: str,
        password: str,
        ip_address: str,
    ) -> str | None:
        """One method instead of coordinating three systems"""
        # Coordinate legacy systems
        user = await asyncio.to_thread(
            self.auth.authenticate_user, username, password
        )
        if not user:
            return None

        session_id = await asyncio.to_thread(
            self.sessions.create_session, user.id
        )

        await asyncio.to_thread(
            self.audit.log_login, user.id, ip_address
        )

        return session_id

    async def check_access(self, session_id: str, resource: str) -> bool:
        """Simplified permission check"""
        session = await asyncio.to_thread(
            self.sessions.validate_session, session_id
        )
        if not session:
            return False

        return await asyncio.to_thread(
            self.auth.check_permissions, session.user_id, resource
        )

# Client code is much simpler
@app.post("/login")
async def login(credentials: LoginRequest):
    session_id = await auth_facade.login(
        credentials.username,
        credentials.password,
        request.client.host,
    )
    if session_id:
        return {"session_id": session_id}
    raise HTTPException(401, "Invalid credentials")
```

## Replace Algorithm Pattern

```python
# Legacy algorithm with poor performance
def legacy_search_products(query: str, products: list) -> list:
    """O(n) linear search through all products"""
    results = []
    for product in products:
        if query.lower() in product.name.lower():
            results.append(product)
        elif query.lower() in product.description.lower():
            results.append(product)
    return results

# Step 1: Extract algorithm to its own class
class ProductSearchStrategy(ABC):
    @abstractmethod
    def search(self, query: str) -> list[Product]:
        pass

class LegacyProductSearch(ProductSearchStrategy):
    def __init__(self, products: list):
        self.products = products

    def search(self, query: str) -> list[Product]:
        return legacy_search_products(query, self.products)

# Step 2: Implement improved algorithm
class ElasticsearchProductSearch(ProductSearchStrategy):
    def __init__(self, es_client):
        self.es = es_client

    async def search(self, query: str) -> list[Product]:
        response = await self.es.search(
            index="products",
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^2", "description"],
                        "fuzziness": "AUTO",
                    }
                }
            },
        )
        return [Product.from_es(hit) for hit in response["hits"]["hits"]]

# Step 3: Use strategy pattern for gradual rollout
class ProductService:
    def __init__(self, search_strategy: ProductSearchStrategy):
        self.search = search_strategy

    async def find_products(self, query: str) -> list[Product]:
        return await self.search.search(query)

# Dependency injection controls which algorithm is used
def get_search_strategy() -> ProductSearchStrategy:
    if feature_flags.is_enabled("elasticsearch_search"):
        return ElasticsearchProductSearch(es_client)
    return LegacyProductSearch(product_cache)
```

## Introduce Repository Pattern

```python
# Legacy data access scattered throughout code
class OrderController:
    def get_order(self, order_id):
        # Direct SQL in controller
        result = db.execute("SELECT * FROM orders WHERE id = ?", order_id)
        return result.fetchone()

# Step 1: Create repository interface
class OrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None:
        pass

    @abstractmethod
    async def create(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        pass

# Step 2: Implement for legacy database
class LegacyOrderRepository(OrderRepository):
    def __init__(self, db_connection):
        self.db = db_connection

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await asyncio.to_thread(
            self.db.execute,
            "SELECT * FROM orders WHERE id = ?",
            order_id,
        )
        row = result.fetchone()
        return Order.from_legacy_row(row) if row else None

# Step 3: Implement modern version
class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self.db.get(Order, order_id)

    async def create(self, order: Order) -> Order:
        self.db.add(order)
        await self.db.flush()
        return order

# Controllers now use repository
class OrderController:
    def __init__(self, order_repo: OrderRepository):
        self.orders = order_repo

    async def get_order(self, order_id: int):
        order = await self.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(404)
        return order
```

## Quick Reference

| Pattern | Use When | Benefit |
|---------|----------|---------|
| Branch by Abstraction | Large refactoring needed | Incremental migration |
| Extract Service | Class doing too much | Single responsibility |
| Adapter | Legacy interface incompatible | Bridge old and new |
| Facade | Complex subsystem | Simplified interface |
| Replace Algorithm | Performance/maintainability | Swap implementations |
| Repository | Data access scattered | Centralized data logic |
