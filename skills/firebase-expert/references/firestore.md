# Cloud Firestore

Data modeling, queries, indexes, writes, listeners and cost control for Cloud Firestore with the modular JS SDK (`firebase` 13) and `firebase-admin` 14.

## When to Use

- Designing collections and document shapes for a new feature
- Writing queries, pagination, aggregation or real-time listeners
- Fixing `FAILED_PRECONDITION: The query requires an index` or contention errors
- Reducing a read bill or deciding between Firestore, Realtime Database and SQL Connect

## When Not to Use

- Relational reporting, joins and ad hoc analytics: export to BigQuery or use SQL Connect with `postgres-pro`
- Firestore Enterprise edition pipeline queries and MongoDB compatibility mode: read the editions docs first; this file covers Standard edition Core operations, which also run on Enterprise

## Choosing a Database

| Need | Pick |
| --- | --- |
| Document data, offline-first clients, real-time lists, per-user security rules | Cloud Firestore (Standard edition, the default) |
| Presence (online/offline), very frequent small state syncs, simple tree data | Realtime Database (`onDisconnect()`), billed on bandwidth and storage |
| Relational schema, joins, transactions across tables, SQL | SQL Connect (formerly Data Connect, renamed April 2026) on Cloud SQL for PostgreSQL |
| Complex server-side queries, 16 MiB documents, MongoDB drivers | Firestore Enterprise edition (no automatic single-field indexes; real-time and offline only for Core operations) |

## Modeling Rules of Thumb

- Model for the reads. Each screen should load from one query or a handful of document gets.
- Documents are capped at 1 MiB (Standard). Unbounded lists (comments, events, members of a large team) become subcollections, not arrays.
- Duplicate small, rarely changing fields (author name, avatar URL) into the documents that list them. Update copies from a function when the source changes.
- Keep fields the client must not write (`role`, `plan`, counters) in a separate document or collection that rules mark read-only.
- Avoid monotonically increasing document IDs and sequential indexed timestamps on very high write rates (above ~500 writes/s to one collection): they create hotspots. Auto IDs from `doc(collection(...))` are random.
- Store timestamps as `Timestamp` via `serverTimestamp()`, money as integer minor units.

```text
users/{uid}                          profile, owned by the user
users/{uid}/private/settings         fields only the user reads
workspaces/{wsId}                    name, ownerId, memberIds (<= a few hundred)
workspaces/{wsId}/members/{uid}      role, joinedAt (source of truth for access)
workspaces/{wsId}/tasks/{taskId}     title, status, assigneeId, dueAt, updatedAt
```

## Typed Access with Converters

```typescript
import {
  collection,
  doc,
  serverTimestamp,
  type FirestoreDataConverter,
  type QueryDocumentSnapshot,
  type Timestamp,
} from 'firebase/firestore';
import { db } from './firebase';

export type TaskStatus = 'todo' | 'doing' | 'done';

export interface Task {
  id: string;
  title: string;
  status: TaskStatus;
  assigneeId: string | null;
  dueAt: Timestamp | null;
  updatedAt: Timestamp | null; // null until the server timestamp resolves
}

const taskConverter: FirestoreDataConverter<Task> = {
  toFirestore: (task) => {
    const { id: _id, updatedAt: _u, ...data } = task as Task;
    return { ...data, updatedAt: serverTimestamp() };
  },
  fromFirestore: (snap: QueryDocumentSnapshot) => {
    const d = snap.data({ serverTimestamps: 'estimate' });
    return {
      id: snap.id,
      title: d.title,
      status: d.status,
      assigneeId: d.assigneeId ?? null,
      dueAt: d.dueAt ?? null,
      updatedAt: d.updatedAt ?? null,
    };
  },
};

export const tasksCol = (wsId: string) =>
  collection(db, 'workspaces', wsId, 'tasks').withConverter(taskConverter);

export const taskDoc = (wsId: string, taskId: string) =>
  doc(db, 'workspaces', wsId, 'tasks', taskId).withConverter(taskConverter);
```

A converter shapes data; it does not validate it. Rules validate writes (`security-rules.md`).

## Queries, Indexes and Pagination

```typescript
import {
  getDocs,
  limit,
  orderBy,
  query,
  startAfter,
  where,
  type QueryDocumentSnapshot,
} from 'firebase/firestore';
import { tasksCol, type Task, type TaskStatus } from './tasks';

const PAGE = 25;

export async function listTasks(
  wsId: string,
  status: TaskStatus,
  cursor?: QueryDocumentSnapshot<Task>,
) {
  const q = query(
    tasksCol(wsId),
    where('status', '==', status),
    orderBy('dueAt', 'asc'),
    ...(cursor ? [startAfter(cursor)] : []),
    limit(PAGE),
  );
  const snap = await getDocs(q);
  return {
    tasks: snap.docs.map((d) => d.data()),
    next: snap.docs.length === PAGE ? snap.docs[snap.docs.length - 1] : undefined,
  };
}
```

Equality on one field plus `orderBy` on another needs a composite index. Commit it so every environment gets it:

```json
{
  "indexes": [
    {
      "collectionGroup": "tasks",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "dueAt", "order": "ASCENDING" }
      ]
    }
  ],
  "fieldOverrides": [
    {
      "collectionGroup": "events",
      "fieldPath": "payload",
      "indexes": []
    }
  ]
}
```

- `firebase deploy --only firestore:indexes` deploys `firestore.indexes.json`; `firebase firestore:indexes` prints what the project has, so indexes created from the console link can be pulled back into the file.
- `fieldOverrides` with empty `indexes` turns off single-field indexing on large maps or blobs you never query. That saves storage and write cost.
- Use cursors (`startAfter`), never `offset`: skipped documents are still billed.
- Range and inequality filters may span several fields, but each needs index support and the first `orderBy` must match the inequality fields. `or()` and `in` take at most 30 disjunctions.
- Collection group queries (`collectionGroup(db, 'tasks')`) need a `COLLECTION_GROUP` scope index and a rule on the `{path=**}` form.

## Aggregation

```typescript
import {
  average,
  collection,
  count,
  getAggregateFromServer,
  query,
  sum,
  where,
} from 'firebase/firestore';
import { db } from './firebase';

export async function orderStats(shopId: string) {
  const q = query(collection(db, 'shops', shopId, 'orders'), where('status', '==', 'paid'));
  const snap = await getAggregateFromServer(q, {
    orders: count(),
    revenueCents: sum('totalCents'),
    avgCents: average('totalCents'),
  });
  return snap.data();
}
```

Aggregations bill one read per up to 1,000 index entries scanned, so they are cheap but not free. For counters shown on every page view, keep a maintained counter document instead.

## Writes: Transactions and Batches

Transactions read then write atomically and retry on contention. Every read must happen before any write.

```typescript
import { doc, increment, runTransaction, serverTimestamp } from 'firebase/firestore';
import { db } from './firebase';

export async function claimSeat(eventId: string, uid: string): Promise<boolean> {
  return runTransaction(db, async (tx) => {
    const eventRef = doc(db, 'events', eventId);
    const seatRef = doc(db, 'events', eventId, 'attendees', uid);
    const [event, seat] = await Promise.all([tx.get(eventRef), tx.get(seatRef)]);
    if (!event.exists()) throw new Error('event-not-found');
    if (seat.exists()) return true;
    if (event.data().taken >= event.data().capacity) return false;
    tx.update(eventRef, { taken: increment(1) });
    tx.set(seatRef, { joinedAt: serverTimestamp() });
    return true;
  });
}
```

- Client transactions fail offline. Anything that must hold under concurrency from untrusted clients (inventory, balances) belongs in a callable function using the Admin SDK transaction, with rules denying direct writes.
- `writeBatch(db)` groups up to 500 writes without reads. Use it for fan-out updates the client is allowed to make.
- One document sustains roughly one write per second over time. Spread hot counters across shards (`counters/{id}/shards/{0..9}`) and sum them.

## Admin SDK Writes (Node)

```typescript
import { initializeApp } from 'firebase-admin/app';
import { FieldValue, getFirestore } from 'firebase-admin/firestore';

initializeApp(); // Application Default Credentials; no key file on Google infrastructure
const db = getFirestore();

export async function archiveDoneTasks(wsId: string): Promise<number> {
  const writer = db.bulkWriter();
  let n = 0;
  const done = await db
    .collection(`workspaces/${wsId}/tasks`)
    .where('status', '==', 'done')
    .select() // ids only: still one read per document, less bandwidth
    .get();
  for (const d of done.docs) {
    writer.update(d.ref, { archived: true, updatedAt: FieldValue.serverTimestamp() });
    n++;
  }
  await writer.close();
  return n;
}
```

The Admin SDK bypasses Security Rules. Validate inputs in the function, never pass a client-supplied path straight to `db.doc()`. `db.recursiveDelete(ref)` deletes a document and its subcollections; deleting a parent document alone leaves its subcollections in place.

## Listeners and Offline Cache

```typescript
import { limit, onSnapshot, orderBy, query, where } from 'firebase/firestore';
import { tasksCol, type Task } from './tasks';

export function watchMyOpenTasks(wsId: string, uid: string, onChange: (t: Task[]) => void) {
  const q = query(
    tasksCol(wsId),
    where('assigneeId', '==', uid),
    where('status', 'in', ['todo', 'doing']),
    orderBy('dueAt'),
    limit(50),
  );
  return onSnapshot(
    q,
    { includeMetadataChanges: false },
    (snap) => onChange(snap.docs.map((d) => d.data())),
    (err) => console.error('tasks listener', err.code), // permission-denied ends the listener
  );
}
```

- Return and call the unsubscribe function when the component unmounts or the user signs out. Leaked listeners keep billing.
- Each added or changed document in the result set is a billed read. A listener on an unbounded, busy collection is the most common runaway bill.
- `persistentLocalCache` serves cached results instantly and replays pending writes when back online. `snap.metadata.fromCache` and `hasPendingWrites` tell the UI what is confirmed.
- With persistence off, a listener disconnected for more than 30 minutes is billed as a brand new query on reconnect.
- `getDocFromCache` / `getDocsFromCache` read without network or billing; they throw if the data is not cached.

## Cost Checklist

| Trap | Fix |
| --- | --- |
| Every query bills at least one read, even when empty | Combine lookups, cache results in app state |
| N+1: one `getDoc` per list row for author data | Denormalize the fields the list shows |
| `offset()` pagination | Cursor pagination |
| Rules `get()`/`exists()` on every request | Custom claims for roles; each dependent document bills one read per request |
| Trigger writes back to the document it listens on | Compare `before`/`after` and exit early (`cloud-functions.md`) |
| Large maps indexed field by field | `fieldOverrides` with no indexes |
| Count shown on every page view | Maintained counter document |

Free quota per day: 50,000 reads, 20,000 writes, 20,000 deletes, on one database per project.

## Related

- `security-rules.md` for the rules that must match each query
- `cloud-functions.md` for denormalization and counter triggers
- `postgres-pro` and `sql-pro` skills for SQL Connect schema and query design
