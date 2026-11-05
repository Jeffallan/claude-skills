# Debugging a Production Issue

> **Skills used:** Monitoring Expert (`monitoring-expert`), Debugging Wizard (`debugging-wizard`), Django Expert
> (`django-expert`), Test Master (`test-master`)
> **Estimated time:** 1-2 hours
> **Difficulty:** Intermediate

## Overview

A Django REST Framework endpoint, `GET /api/orders/`, got slow after a deploy. Most requests now take over two
seconds. This walkthrough finds the cause with monitoring data, proves it with a small reproduction, fixes the
query, and adds a test so the problem stays fixed.

---

## Step 1: Find the slow path with Monitoring Expert

**Prompt:**

```text
Our /api/orders/ endpoint is slow in production. What should I check first in our logs and metrics, and which
queries show whether this is one endpoint or the whole service?
```

**What the skill does:** `monitoring-expert` starts from what to measure: rate, errors, and duration per endpoint
(the RED method in its workflow). It asks for p95 duration grouped by route, not averages, because averages hide
a slow endpoint inside a fast service.

**Output excerpt:**

```text
Route                p50     p95     Requests/min
/api/orders/         1.8s    2.6s    42
/api/orders/{id}/    40ms    90ms    118
/api/products/       25ms    60ms    210
```

Only the list view is slow. The detail view reads the same tables and is fast, so the database itself is probably
fine. That narrows the search to the list view's queries.

---

## Step 2: Reproduce and isolate with Debugging Wizard

**Prompt:**

```text
The list view is slow but the detail view is fast. Help me reproduce this locally and find the root cause before
changing any code.
```

**What the skill does:** `debugging-wizard` works in order: reproduce, isolate, then test one hypothesis at a
time. The first hypothesis here is the classic list-view problem: one extra query per row (an N+1 query).

**Output excerpt:**

```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    response = client.get("/api/orders/")
print(len(ctx))  # 203 queries for a page of 100 orders
```

203 queries for 100 rows confirms the hypothesis: one query for the orders, then one per order for the customer
and one per order for its items. No fix yet. The count is the evidence the fix has to change.

---

## Step 3: Fix the query with Django Expert

**Prompt:**

```text
Fix the N+1 queries in the orders list view. The serializer reads order.customer.name and the item count for
each order.
```

**What the skill does:** `django-expert` covers ORM optimization with `select_related` and `prefetch_related`
in its workflow. Foreign keys get `select_related`. Reverse relations get `prefetch_related`.

**Output excerpt:**

```python
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(owner=self.request.user)
            .select_related("customer")
            .prefetch_related("items")
            .order_by("-created_at")
        )
```

Run the step 2 snippet again after this change. The count drops from 203 to 3: orders, customers joined in the
same query, and one prefetch query for all items.

---

## Step 4: Lock it in with Test Master

**Prompt:**

```text
Write a regression test that fails if the orders list view goes back to per-row queries.
```

**What the skill does:** `test-master` turns the bug into a test case. Django's `assertNumQueries` fits this bug
exactly, because the bug is a query count, not a wrong value.

**Output excerpt:**

```python
class OrderListQueryTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="sam")
        self.client.force_authenticate(user=self.user)
        customer = Customer.objects.create(name="Ada")
        for i in range(5):
            order = Order.objects.create(owner=self.user, customer=customer)
            OrderItem.objects.create(order=order, sku=f"SKU-{i}", quantity=1)

    def test_list_view_uses_a_fixed_number_of_queries(self):
        with self.assertNumQueries(3):
            response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
```

---

## Key takeaways

1. Start from per-route duration data. It told us which view to read before we read any code.
2. Prove the cause with a count (203 queries) before editing. The same count proves the fix (3 queries).
3. The regression test asserts the query count, so the bug cannot come back silently.
