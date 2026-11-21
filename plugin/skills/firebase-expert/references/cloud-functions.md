# Cloud Functions for Firebase (2nd gen)

Callable, HTTP, Firestore, Storage, scheduled and task queue functions with `firebase-functions` 7 and `firebase-admin` 14 on Cloud Functions 2nd gen (Cloud Run).

## When to Use

- Privileged writes the client must not make: roles, payments, counters, membership
- Reacting to Firestore, Storage or Auth events (denormalization, thumbnails, clean-up)
- Calling third-party APIs with secret keys
- Scheduled jobs and retryable background work

## When Not to Use

- A full web server with many routes or SSR: deploy to App Hosting or Cloud Run directly (`hosting-deployment.md`)
- Work that rules can enforce alone: a function adds latency, cost and a cold start
- New 1st gen functions: 2nd gen is the recommended generation; 1st gen remains only for existing code and Analytics triggers

## Facts That Shape the Code

- Functions require the Blaze plan.
- 2nd gen runs on Cloud Run: one instance serves up to 1,000 concurrent requests (default 80), so module-level state is shared across requests. Never keep per-request data in globals.
- Runtimes: set `"runtime": "nodejs22"` (or `nodejs24`) in `firebase.json`. Node 18 is decommissioned and Node 20 reached decommission on 2026-10-30.
- `functions.config()` was removed in firebase-functions 7. Configuration comes from `firebase-functions/params` (`defineString`, `defineInt`, `defineSecret`) backed by `.env` files and Secret Manager.
- firebase-functions 7 supports ESM as well as CommonJS.
- Event triggers deliver at least once. Every event handler must be idempotent.

## Project Layout

```text
functions/
  package.json        "main": "lib/index.js", engines node 22
  tsconfig.json
  .env                APP_ORIGIN=https://example.com  (non-secret params, committed)
  .env.my-project-dev per-project overrides
  src/index.ts        exports every function
  src/*.ts
```

```typescript
// functions/src/index.ts
import { initializeApp } from 'firebase-admin/app';
import { setGlobalOptions } from 'firebase-functions/v2';

initializeApp();
setGlobalOptions({ region: 'us-central1', maxInstances: 10 }); // cap runaway scale and spend

export { setUserRole } from './roles';
export { createCheckout } from './checkout';
export { countTasks, normalizeProfile } from './triggers';
export { nightlyCleanup } from './scheduled';
export { makeThumbnail } from './storage';
```

Put Firestore triggers in the database's region (for the `nam5` or `eur3` multi-regions, a region inside them such as `us-central1` or `europe-west1`). Callers pass the same region to `getFunctions(app, region)`.

## Callable Functions

Callables verify the Firebase ID token and App Check token for you and expose them as `request.auth` and `request.app`.

```typescript
// functions/src/checkout.ts
import { getFirestore } from 'firebase-admin/firestore';
import { defineSecret, defineString } from 'firebase-functions/params';
import { HttpsError, onCall } from 'firebase-functions/v2/https';
import { logger } from 'firebase-functions';

const PAYMENTS_KEY = defineSecret('PAYMENTS_API_KEY');
const APP_ORIGIN = defineString('APP_ORIGIN');

interface CheckoutInput {
  planId: string;
}

export const createCheckout = onCall<CheckoutInput>(
  {
    secrets: [PAYMENTS_KEY],
    enforceAppCheck: true, // reject requests without a valid App Check token
    consumeAppCheckToken: false, // true adds replay protection at extra latency
    timeoutSeconds: 30,
  },
  async (request) => {
    const uid = request.auth?.uid;
    if (!uid) throw new HttpsError('unauthenticated', 'Sign in first');

    const planId = request.data?.planId;
    if (typeof planId !== 'string' || !/^[a-z0-9_-]{1,40}$/.test(planId)) {
      throw new HttpsError('invalid-argument', 'Unknown plan');
    }

    // Price comes from the server's own data, never from the client
    const plan = await getFirestore().doc(`plans/${planId}`).get();
    if (!plan.exists) throw new HttpsError('not-found', 'Unknown plan');

    const res = await fetch('https://payments.example.com/v1/checkout', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${PAYMENTS_KEY.value()}`,
        'Content-Type': 'application/json',
        'Idempotency-Key': `${uid}:${planId}:${new Date().toISOString().slice(0, 13)}`,
      },
      body: JSON.stringify({
        customer: uid,
        amountCents: plan.get('priceCents'),
        successUrl: `${APP_ORIGIN.value()}/billing/done`,
      }),
    });
    if (!res.ok) {
      logger.error('checkout failed', { status: res.status, uid });
      throw new HttpsError('unavailable', 'Payment provider error');
    }
    const { url } = (await res.json()) as { url: string };
    return { url };
  },
);
```

```typescript
// client
import { getFunctions, httpsCallable } from 'firebase/functions';
import { app } from './firebase';

const functions = getFunctions(app, 'us-central1');
const createCheckout = httpsCallable<{ planId: string }, { url: string }>(functions, 'createCheckout');

export async function startCheckout(planId: string) {
  const { data } = await createCheckout({ planId });
  window.location.assign(data.url);
}
```

- Set secrets with `firebase functions:secrets:set PAYMENTS_API_KEY`. Only functions listing the secret in `secrets` can read it.
- Throw `HttpsError` for expected failures. Any other error reaches the client as `internal` with no details, which is what you want for bugs.
- Read `.value()` inside the handler, not at module load: params resolve at runtime.

## HTTP Functions

Use `onRequest` for webhooks and third-party callers. Verify the caller yourself: the provider's signature for webhooks, an ID token (`authentication.md`) for users.

```typescript
import { onRequest } from 'firebase-functions/v2/https';
import { defineSecret } from 'firebase-functions/params';
import { createHmac, timingSafeEqual } from 'node:crypto';

const WEBHOOK_SECRET = defineSecret('WEBHOOK_SECRET');

export const paymentsWebhook = onRequest({ secrets: [WEBHOOK_SECRET] }, async (req, res) => {
  const sig = req.get('x-signature') ?? '';
  const expected = createHmac('sha256', WEBHOOK_SECRET.value()).update(req.rawBody).digest('hex');
  const ok = sig.length === expected.length && timingSafeEqual(Buffer.from(sig), Buffer.from(expected));
  if (!ok) {
    res.status(401).send('bad signature');
    return;
  }
  // ... record the event id first, then act (idempotency)
  res.status(200).send('ok');
});
```

## Firestore Triggers: Idempotency and Loops

```typescript
// functions/src/triggers.ts
import { FieldValue, Timestamp, getFirestore } from 'firebase-admin/firestore';
import { onDocumentWritten } from 'firebase-functions/v2/firestore';

const db = () => getFirestore();

// Keeps workspaces/{wsId}.taskCount in step. Retries are on, so the event id
// marker makes a redelivered event a no-op.
export const countTasks = onDocumentWritten(
  { document: 'workspaces/{wsId}/tasks/{taskId}', retry: true },
  async (event) => {
    const existedBefore = event.data?.before.exists ?? false;
    const existsAfter = event.data?.after.exists ?? false;
    if (existedBefore === existsAfter) return; // plain update: count unchanged

    const marker = db().doc(`_processedEvents/${event.id}`);
    const workspace = db().doc(`workspaces/${event.params.wsId}`);
    await db().runTransaction(async (tx) => {
      if ((await tx.get(marker)).exists) return;
      tx.set(marker, {
        expireAt: Timestamp.fromMillis(Date.now() + 7 * 24 * 3600 * 1000), // TTL policy on expireAt
      });
      tx.update(workspace, { taskCount: FieldValue.increment(existsAfter ? 1 : -1) });
    });
  },
);

// Writes back to the document that triggered it: exit when there is nothing to change,
// or the function triggers itself forever (and bills every round).
export const normalizeProfile = onDocumentWritten('users/{uid}', async (event) => {
  const after = event.data?.after;
  if (!after?.exists) return;
  const name = after.get('displayName');
  if (typeof name !== 'string') return;
  const normalized = name.trim().replace(/\s+/g, ' ');
  if (normalized === name) return; // loop guard
  await after.ref.update({ displayName: normalized });
});
```

- Add a TTL policy on `_processedEvents.expireAt` in the console or with `gcloud firestore fields ttls update`.
- Keep rules `allow write: if false` on `_processedEvents` and on any counter fields.
- `retry: true` redelivers failed events with backoff until they succeed or the retry window expires. Only turn it on for idempotent handlers, and do not throw for permanent errors (bad data): log and return.
- `onDocumentCreated`, `onDocumentUpdated` and `onDocumentDeleted` exist for narrower cases; `...WithAuthContext` variants add the writer's identity.

## Scheduled and Storage Functions

```typescript
// functions/src/scheduled.ts
import { getFirestore, Timestamp } from 'firebase-admin/firestore';
import { onSchedule } from 'firebase-functions/v2/scheduler';
import { logger } from 'firebase-functions';

export const nightlyCleanup = onSchedule(
  { schedule: '0 3 * * *', timeZone: 'Etc/UTC', retryCount: 2 },
  async () => {
    const cutoff = Timestamp.fromMillis(Date.now() - 30 * 24 * 3600 * 1000);
    const stale = await getFirestore()
      .collection('invites')
      .where('createdAt', '<', cutoff)
      .limit(500)
      .get();
    const writer = getFirestore().bulkWriter();
    stale.docs.forEach((d) => writer.delete(d.ref));
    await writer.close();
    logger.info('deleted stale invites', { count: stale.size });
  },
);
```

```typescript
// functions/src/storage.ts
import { getStorage } from 'firebase-admin/storage';
import { onObjectFinalized } from 'firebase-functions/v2/storage';
import sharp from 'sharp';

const isThumb = (name: string) => name.startsWith('thumbs/') || name.includes('/thumbs/');

export const makeThumbnail = onObjectFinalized({ memory: '1GiB' }, async (event) => {
  const { name, contentType, bucket } = event.data;
  if (!contentType?.startsWith('image/') || isThumb(name)) return; // loop guard: output retriggers
  const files = getStorage().bucket(bucket);
  const [bytes] = await files.file(name).download();
  const thumb = await sharp(bytes).resize(256, 256, { fit: 'inside' }).webp().toBuffer();
  const thumbName = name.replace(/([^/]+)$/, 'thumbs/$1.webp');
  await files.file(thumbName).save(thumb, { contentType: 'image/webp' });
});
```

Scheduled functions need Cloud Scheduler in the chosen region. For queued work with rate limits and retries, use `onTaskDispatched` from `firebase-functions/v2/tasks` and enqueue with `getFunctions().taskQueue(...)` from `firebase-admin/functions`.

## Performance and Cost Settings

| Option | Use |
| --- | --- |
| `maxInstances` | Always set; it caps spend when traffic or a loop spikes |
| `minInstances` | Removes cold starts but bills idle time around the clock; reserve for latency-critical callables |
| `concurrency` | Lower it (e.g. 1 to 10) for CPU-heavy handlers; keep the default for I/O |
| `memory` / `cpu` | Raise for image or PDF work; 2nd gen bills both |
| `timeoutSeconds` | Up to 3,600 for HTTP and callables, 540 for event triggers |

Initialize SDK clients at module scope (they are reused across requests), but lazily import heavy libraries inside the handler that needs them.

## Testing

Run functions in the emulator with Firestore and Auth so triggers fire for real (`emulators-testing.md`). For unit tests of handler logic, export plain functions and keep the trigger wrappers thin.

## Related

- `authentication.md` for blocking functions and claims
- `storage-app-check.md` for client App Check setup
- `cloud-architect` skill for Cloud Run, Pub/Sub and Eventarc beyond Firebase triggers
