# OpenTelemetry Tracing

> Reference for: Monitoring Expert
> Load when: Distributed tracing, spans

## Node.js Setup

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'my-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://jaeger:4318/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

## Manual Spans

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(orderId: string) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    span.setAttribute('order.id', orderId);

    try {
      // Child span for database
      await tracer.startActiveSpan('db.getOrder', async (dbSpan) => {
        const order = await db.orders.findById(orderId);
        dbSpan.setAttribute('db.rows_affected', 1);
        dbSpan.end();
        return order;
      });

      // Child span for external API
      await tracer.startActiveSpan('api.processPayment', async (apiSpan) => {
        await paymentService.process(order);
        apiSpan.end();
      });

      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## Context Propagation

```typescript
import { propagation, context } from '@opentelemetry/api';

// Extract from incoming request
app.use((req, res, next) => {
  const ctx = propagation.extract(context.active(), req.headers);
  context.with(ctx, next);
});

// Inject into outgoing request
async function callExternalService() {
  const headers = {};
  propagation.inject(context.active(), headers);

  await fetch('http://other-service/api', { headers });
}
```

## Python Setup

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        # ... process order
```

## Quick Reference

| Concept | Purpose |
|---------|---------|
| Span | Single operation |
| Trace | Full request flow |
| Context | Correlation across services |
| Attributes | Metadata on spans |
| Events | Timestamped logs in span |

| Attribute | Example |
|-----------|---------|
| `http.method` | GET, POST |
| `http.status_code` | 200, 500 |
| `db.system` | postgresql |
| `db.statement` | SELECT ... |
