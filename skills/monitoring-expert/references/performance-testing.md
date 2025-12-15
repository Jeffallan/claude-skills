# Performance Testing

> Reference for: Monitoring Expert
> Load when: Load testing, stress testing, performance benchmarks

## Load Testing with k6

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp-up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp-up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp-down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.1'],
  },
};

export default function () {
  const res = http.get('https://api.example.com/products');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);
}
```

## Test Types

### Load Test
```javascript
// Gradual ramp-up to expected production load
export const options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '30m', target: 100 },
    { duration: '5m', target: 0 },
  ],
};
```

### Stress Test
```javascript
// Push beyond normal capacity to find breaking point
export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '5m', target: 400 },
    { duration: '2m', target: 0 },
  ],
};
```

### Spike Test
```javascript
// Sudden increase in load
export const options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '30s', target: 1000 }, // Spike
    { duration: '3m', target: 100 },
    { duration: '1m', target: 0 },
  ],
};
```

### Soak Test
```javascript
// Extended duration at normal load
export const options = {
  stages: [
    { duration: '5m', target: 100 },
    { duration: '8h', target: 100 },  // Long duration
    { duration: '5m', target: 0 },
  ],
};
```

## Artillery.io

```yaml
# load-test.yml
config:
  target: 'https://api.example.com'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50
      name: "Sustained load"

  processor: "./custom-functions.js"

  variables:
    userId:
      - "user1"
      - "user2"

scenarios:
  - name: "Product browsing"
    weight: 70
    flow:
      - get:
          url: "/products"
      - think: 2
      - get:
          url: "/products/{{ $randomNumber(1, 100) }}"

  - name: "Checkout"
    weight: 30
    flow:
      - post:
          url: "/cart"
          json:
            productId: "{{ $randomNumber(1, 100) }}"
      - post:
          url: "/checkout"
          json:
            userId: "{{ userId }}"
```

## Locust (Python)

```python
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_products(self):
        self.client.get("/products")

    @task(1)
    def view_product(self):
        product_id = random.randint(1, 100)
        self.client.get(f"/products/{product_id}")

    @task(1)
    def create_order(self):
        self.client.post("/orders", json={
            "product_id": random.randint(1, 100),
            "quantity": random.randint(1, 5)
        })

    def on_start(self):
        # Login or setup
        self.client.post("/login", json={
            "username": "test",
            "password": "test"
        })
```

## JMeter Thread Groups

```xml
<!-- Basic HTTP Request -->
<ThreadGroup>
  <stringProp name="ThreadGroup.num_threads">100</stringProp>
  <stringProp name="ThreadGroup.ramp_time">60</stringProp>
  <stringProp name="ThreadGroup.duration">300</stringProp>
  <boolProp name="ThreadGroup.scheduler">true</boolProp>
</ThreadGroup>
```

## Performance Metrics to Track

```javascript
// k6 custom metrics
import { Counter, Trend, Gauge } from 'k6/metrics';

const checkoutDuration = new Trend('checkout_duration');
const cartSize = new Gauge('cart_size');
const orderCounter = new Counter('orders_created');

export default function () {
  const startTime = Date.now();

  const res = http.post('https://api.example.com/checkout', payload);

  checkoutDuration.add(Date.now() - startTime);
  orderCounter.add(1);
  cartSize.add(payload.items.length);
}
```

## Test Scenario Design

```javascript
// Realistic user journey
import { scenario } from 'k6/execution';

export const options = {
  scenarios: {
    browser_users: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '5m', target: 100 },
        { duration: '10m', target: 100 },
      ],
      gracefulRampDown: '30s',
    },
    api_users: {
      executor: 'constant-arrival-rate',
      rate: 50,
      timeUnit: '1s',
      duration: '15m',
      preAllocatedVUs: 100,
    },
  },
};

export default function () {
  // Homepage
  http.get('https://example.com/');
  sleep(Math.random() * 3);

  // Search
  http.get('https://example.com/search?q=laptop');
  sleep(Math.random() * 5);

  // Product page
  http.get('https://example.com/products/123');
  sleep(Math.random() * 10);

  // Add to cart (30% conversion)
  if (Math.random() < 0.3) {
    http.post('https://example.com/cart', { productId: 123 });
  }
}
```

## Quick Reference

| Test Type | Purpose | Duration |
|-----------|---------|----------|
| Load | Normal capacity | 30m - 2h |
| Stress | Find limits | 1h - 4h |
| Spike | Sudden traffic | 15m - 30m |
| Soak | Memory leaks | 4h - 24h |

| Tool | Language | Best For |
|------|----------|----------|
| k6 | JavaScript | API testing, CI/CD |
| Artillery | YAML/JS | Simple scenarios |
| Locust | Python | Complex scenarios |
| JMeter | GUI/XML | Legacy systems |

| Metric | Target |
|--------|--------|
| p95 latency | < 500ms |
| p99 latency | < 1s |
| Error rate | < 1% |
| RPS | 10x normal |
