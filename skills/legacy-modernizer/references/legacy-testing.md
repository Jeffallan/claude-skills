# Legacy Testing Strategies

> Reference for: Legacy Modernizer
> Load when: Characterization tests, golden master, approval testing, safety nets

## Characterization Tests

Tests that document current behavior (even if buggy) before refactoring.

```python
# Legacy function with unknown behavior
def calculate_shipping_cost(order):
    """Legacy shipping calculator - behavior unclear"""
    cost = 0
    if order['weight'] > 10:
        cost += order['weight'] * 0.5
    if order['destination'] == 'international':
        cost *= 2
    if order['priority']:
        cost *= 1.5
    # ... more mysterious logic
    return round(cost, 2)

# Characterization test: Capture current behavior
import pytest

class TestShippingCostCharacterization:
    """These tests document existing behavior, not correct behavior"""

    def test_domestic_lightweight(self):
        order = {'weight': 5, 'destination': 'domestic', 'priority': False}
        # This IS the current behavior (0.0 might be wrong!)
        assert calculate_shipping_cost(order) == 0.0

    def test_domestic_heavy(self):
        order = {'weight': 15, 'destination': 'domestic', 'priority': False}
        assert calculate_shipping_cost(order) == 7.5  # weight * 0.5

    def test_international_heavy(self):
        order = {'weight': 15, 'destination': 'international', 'priority': False}
        assert calculate_shipping_cost(order) == 15.0  # (15 * 0.5) * 2

    def test_priority_international_heavy(self):
        order = {'weight': 15, 'destination': 'international', 'priority': True}
        assert calculate_shipping_cost(order) == 22.5  # ((15 * 0.5) * 2) * 1.5

# After characterization, refactor with confidence
def calculate_shipping_cost_v2(order: Order) -> Decimal:
    """Refactored with clear logic"""
    base_cost = Decimal('0')

    if order.weight > 10:
        base_cost = Decimal(str(order.weight)) * Decimal('0.5')

    if order.destination == Destination.INTERNATIONAL:
        base_cost *= Decimal('2')

    if order.priority:
        base_cost *= Decimal('1.5')

    return base_cost.quantize(Decimal('0.01'))

# Characterization tests should still pass
```

## Golden Master Testing

Capture output snapshots for complex legacy systems.

```python
# Legacy report generator with complex formatting
def generate_monthly_report(start_date, end_date):
    """Generates complex text report"""
    report = []
    report.append(f"Report Period: {start_date} to {end_date}")
    # ... 500 lines of complex logic
    return "\n".join(report)

# Golden master test
import hashlib
import os
from pathlib import Path

class TestMonthlyReportGoldenMaster:
    def test_january_2024_report(self):
        """Compare against known-good output"""
        report = generate_monthly_report('2024-01-01', '2024-01-31')

        # First run: Save golden master
        golden_path = Path(__file__).parent / 'golden_masters' / 'jan_2024.txt'
        if not golden_path.exists():
            golden_path.parent.mkdir(exist_ok=True)
            golden_path.write_text(report)
            pytest.skip("Golden master saved, run again to verify")

        # Subsequent runs: Compare
        expected = golden_path.read_text()
        assert report == expected, "Output differs from golden master"

    def test_report_hash_unchanged(self):
        """Faster comparison using hash"""
        report = generate_monthly_report('2024-01-01', '2024-01-31')
        report_hash = hashlib.sha256(report.encode()).hexdigest()

        # Known good hash
        expected_hash = "a3f5b2c8d9e1f4a7b6c5d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"
        assert report_hash == expected_hash

# Approval testing library
from approvaltests import verify

def test_monthly_report_approval():
    """Uses approvaltests library for easy golden master testing"""
    report = generate_monthly_report('2024-01-01', '2024-01-31')
    verify(report)  # Creates .approved file first run, compares after
```

## Snapshot Testing for APIs

```python
# Legacy API with complex responses
@app.get("/api/dashboard")
async def get_dashboard():
    # Complex aggregation logic
    return {
        "user": {...},
        "stats": {...},
        "notifications": [...],
        # ... many nested fields
    }

# Snapshot test
import pytest
from syrupy import SnapshotAssertion

@pytest.mark.asyncio
async def test_dashboard_structure(snapshot: SnapshotAssertion):
    """Ensure dashboard structure doesn't change unexpectedly"""
    response = await client.get("/api/dashboard")

    # First run creates snapshot, subsequent runs compare
    assert response.json() == snapshot

# Custom snapshot serializer for stable output
from syrupy.extensions.json import JSONSnapshotExtension

class SortedJSONExtension(JSONSnapshotExtension):
    def serialize(self, data, **kwargs):
        # Sort keys for consistent snapshots
        return super().serialize(data, sort_keys=True, **kwargs)

@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(SortedJSONExtension)
```

## Parallel Run Testing

Run old and new implementations side-by-side to compare.

```python
# Parallel run decorator
import functools
import asyncio
from typing import Callable, Any

def parallel_run(legacy_func: Callable, new_func: Callable):
    """Run both implementations and compare results"""
    @functools.wraps(new_func)
    async def wrapper(*args, **kwargs):
        # Run both in parallel
        legacy_task = asyncio.create_task(
            asyncio.to_thread(legacy_func, *args, **kwargs)
        )
        new_task = asyncio.create_task(new_func(*args, **kwargs))

        legacy_result, new_result = await asyncio.gather(
            legacy_task, new_task, return_exceptions=True
        )

        # Log discrepancies
        if legacy_result != new_result:
            logger.warning(
                "Parallel run mismatch",
                extra={
                    "function": new_func.__name__,
                    "args": args,
                    "legacy_result": legacy_result,
                    "new_result": new_result,
                }
            )

        # Use legacy result in production (new is shadow)
        if isinstance(legacy_result, Exception):
            raise legacy_result
        return legacy_result

    return wrapper

# Usage
@parallel_run(legacy_func=legacy_calculate_price, new_func=new_calculate_price)
async def calculate_price(product_id: int, quantity: int):
    """This will run both and compare results"""
    pass

# In production, route to parallel_run
@app.get("/price/{product_id}")
async def get_price(product_id: int, quantity: int = 1):
    return await calculate_price(product_id, quantity)
```

## Mutation Testing for Legacy Code

```python
# Install: pip install mutmut

# Legacy function we want to refactor
def validate_email(email):
    if '@' not in email:
        return False
    if '.' not in email:
        return False
    if len(email) < 5:
        return False
    return True

# Basic tests
def test_validate_email():
    assert validate_email("user@example.com") is True
    assert validate_email("invalid") is False

# Run mutation testing to find missing test cases
# $ mutmut run --paths-to-mutate=validate.py

# Mutmut will create mutations like:
# - Change '@' to '!' (caught by test)
# - Change 5 to 6 (NOT caught - missing edge case!)
# - Remove conditions (caught by test)

# Add missing test cases discovered by mutation testing
def test_validate_email_comprehensive():
    # Original tests
    assert validate_email("user@example.com") is True
    assert validate_email("invalid") is False

    # Edge cases found by mutation testing
    assert validate_email("a@b.c") is True   # Exactly 5 chars
    assert validate_email("a@b.") is False   # Dot at end
    assert validate_email(".@b.c") is False  # Dot at start
    assert validate_email("a@.com") is False # Dot after @
```

## Property-Based Testing for Legacy Logic

```python
from hypothesis import given, strategies as st

# Legacy function with unclear edge cases
def calculate_discount(price, quantity, customer_type):
    """Legacy discount logic"""
    discount = 0
    if quantity > 10:
        discount += 0.1
    if customer_type == 'premium':
        discount += 0.15
    if price > 1000:
        discount += 0.05
    return price * (1 - min(discount, 0.5))

# Property-based tests discover edge cases
@given(
    price=st.floats(min_value=0.01, max_value=100000),
    quantity=st.integers(min_value=1, max_value=1000),
    customer_type=st.sampled_from(['regular', 'premium']),
)
def test_discount_properties(price, quantity, customer_type):
    result = calculate_discount(price, quantity, customer_type)

    # Property: Result should never be negative
    assert result >= 0

    # Property: Result should never exceed original price
    assert result <= price

    # Property: Discount should never exceed 50%
    assert result >= price * 0.5

# Run this 100+ times with random inputs
# Hypothesis will find edge cases that break these properties
```

## Coverage-Guided Test Generation

```python
# Use coverage.py to find untested code paths
# $ pytest --cov=legacy_module --cov-report=html

# Example: Legacy function with many branches
def process_order(order):
    if not order.get('items'):
        raise ValueError("Empty order")

    total = sum(item['price'] * item['qty'] for item in order['items'])

    if order.get('coupon'):
        discount = apply_coupon(order['coupon'], total)
        total -= discount

    if order.get('shipping_method') == 'express':
        total += 25
    elif order.get('shipping_method') == 'international':
        total += 50

    if total < 0:  # This line never tested!
        total = 0

    return {'total': total, 'order_id': generate_id()}

# Coverage report shows line "total = 0" never executed
# Add test case:
def test_process_order_negative_total():
    """Test case discovered from coverage analysis"""
    order = {
        'items': [{'price': 10, 'qty': 1}],
        'coupon': 'SUPER_DISCOUNT_100',  # 100% off
    }
    result = process_order(order)
    assert result['total'] == 0  # Should handle negative total
```

## Database State Testing

```python
# Test database-dependent legacy code
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def legacy_db():
    """Create test database matching legacy schema"""
    engine = create_engine("sqlite:///:memory:")

    # Recreate legacy schema (exact structure)
    engine.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

def test_legacy_user_creation(legacy_db):
    """Test legacy code against test database"""
    # Insert using legacy code
    legacy_create_user(legacy_db, "John", "john@example.com")

    # Verify using raw SQL
    result = legacy_db.execute("SELECT * FROM users WHERE name = 'John'")
    user = result.fetchone()

    assert user is not None
    assert user['email'] == "john@example.com"
```

## Quick Reference

| Test Type | Use When | Tool |
|-----------|----------|------|
| Characterization | Unknown behavior | pytest |
| Golden Master | Complex output | approvaltests |
| Snapshot | API responses | syrupy |
| Parallel Run | Comparing implementations | Custom decorator |
| Mutation | Finding gaps | mutmut |
| Property-based | Edge cases | hypothesis |
| Coverage-guided | Untested paths | coverage.py |
