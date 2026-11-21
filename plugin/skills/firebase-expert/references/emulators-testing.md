# Emulator Suite and Testing

Local development and automated tests against the Firebase Emulator Suite (firebase-tools 15): Auth, Firestore, Functions, Storage, Realtime Database, Pub/Sub, Hosting and SQL Connect.

## When to Use

- Setting up local development so nothing touches a real project
- Integration tests for triggers, callables and client code paths
- Running rules and function tests in CI

## When Not to Use

- Pure business logic with no Firebase calls: plain unit tests, no emulator
- Load or quota testing: emulators do not model production limits, latency or billing
- Rules tests themselves are in `security-rules.md`; this file sets up the environment they run in

## Requirements

- firebase-tools 15 needs Java 21 or newer for the emulators (`java -version`).
- Use a `demo-` project ID (`demo-myapp`) for local work and CI. Emulators accept it without a real project and SDKs cannot reach production with it.

## Configuration

```json
{
  "firestore": { "rules": "firestore.rules", "indexes": "firestore.indexes.json" },
  "storage": { "rules": "storage.rules" },
  "functions": [{ "source": "functions", "codebase": "default", "runtime": "nodejs22" }],
  "emulators": {
    "auth": { "port": 9099 },
    "firestore": { "port": 8080 },
    "functions": { "port": 5001 },
    "storage": { "port": 9199 },
    "ui": { "enabled": true, "port": 4000 },
    "singleProjectMode": true
  }
}
```

```bash
# Local development with seed data that survives restarts
firebase emulators:start --project demo-myapp --import ./emulator-data --export-on-exit

# One-shot: start emulators, run the command, shut down, exit with its code
firebase emulators:exec --project demo-myapp --only auth,firestore,functions,storage "npm test"
```

Functions must be built before the emulator loads them (`npm --prefix functions run build`, or `tsc --watch` during development).

## Connecting SDKs

Client SDK: call the `connect*Emulator` functions once, right after creating each service and before any request (see the init in `SKILL.md`):

```typescript
import { connectFunctionsEmulator, getFunctions } from 'firebase/functions';
import { connectStorageEmulator, getStorage } from 'firebase/storage';
import { app } from './firebase';

export const functions = getFunctions(app, 'us-central1');
export const storage = getStorage(app);

if (import.meta.env.DEV) {
  connectFunctionsEmulator(functions, '127.0.0.1', 5001);
  connectStorageEmulator(storage, '127.0.0.1', 9199);
}
```

Use `127.0.0.1`, not `localhost`: Node 17+ may resolve `localhost` to `::1` while the emulators listen on IPv4.

Admin SDK: reads environment variables, which `emulators:exec` sets for the child process. For scripts run outside it, set them yourself:

```bash
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
export FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
export FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199
export GCLOUD_PROJECT=demo-myapp
```

## Seeding and Resetting

```typescript
// test/helpers/emulator.ts
import { initializeApp, getApps } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';
import { getFirestore } from 'firebase-admin/firestore';

export const PROJECT_ID = process.env.GCLOUD_PROJECT ?? 'demo-myapp';

if (!process.env.FIRESTORE_EMULATOR_HOST || !PROJECT_ID.startsWith('demo-')) {
  // Refuse to run tests that wipe data against anything but the emulator
  throw new Error('Run tests under `firebase emulators:exec` with a demo- project');
}

if (!getApps().length) initializeApp({ projectId: PROJECT_ID });
export const adminDb = getFirestore();
export const adminAuth = getAuth();

export async function resetEmulators(): Promise<void> {
  const fs = process.env.FIRESTORE_EMULATOR_HOST;
  const au = process.env.FIREBASE_AUTH_EMULATOR_HOST;
  await fetch(`http://${fs}/emulator/v1/projects/${PROJECT_ID}/databases/(default)/documents`, {
    method: 'DELETE',
  });
  if (au) {
    await fetch(`http://${au}/emulator/v1/projects/${PROJECT_ID}/accounts`, { method: 'DELETE' });
  }
}

export async function createUser(uid: string, claims: Record<string, unknown> = {}) {
  await adminAuth.createUser({ uid, email: `${uid}@example.test`, password: 'test-password-1' });
  if (Object.keys(claims).length) await adminAuth.setCustomUserClaims(uid, claims);
}

// Poll until a trigger has done its work; triggers run asynchronously after the write.
export async function waitFor<T>(
  read: () => Promise<T>,
  done: (v: T) => boolean,
  timeoutMs = 10_000,
): Promise<T> {
  const start = Date.now();
  for (;;) {
    const v = await read();
    if (done(v)) return v;
    if (Date.now() - start > timeoutMs) throw new Error('waitFor timed out');
    await new Promise((r) => setTimeout(r, 200));
  }
}
```

## Integration Test: a Firestore Trigger

```typescript
// test/count-tasks.test.ts
import { beforeEach, describe, expect, it } from 'vitest';
import { adminDb, resetEmulators, waitFor } from './helpers/emulator';

describe('countTasks trigger', () => {
  beforeEach(async () => {
    await resetEmulators();
    await adminDb.doc('workspaces/ws1').set({ name: 'Acme', taskCount: 0 });
  });

  it('increments on create and decrements on delete', async () => {
    const task = adminDb.collection('workspaces/ws1/tasks').doc();
    await task.set({ title: 'Ship', status: 'todo' });
    await waitFor(
      () => adminDb.doc('workspaces/ws1').get(),
      (s) => s.get('taskCount') === 1,
    );

    await task.delete();
    const ws = await waitFor(
      () => adminDb.doc('workspaces/ws1').get(),
      (s) => s.get('taskCount') === 0,
    );
    expect(ws.get('taskCount')).toBe(0);
  });

  it('ignores plain updates', async () => {
    const task = adminDb.collection('workspaces/ws1/tasks').doc();
    await task.set({ title: 'Ship', status: 'todo' });
    await waitFor(() => adminDb.doc('workspaces/ws1').get(), (s) => s.get('taskCount') === 1);
    await task.update({ status: 'done' });
    await new Promise((r) => setTimeout(r, 1_000)); // give a wrong trigger time to fire
    expect((await adminDb.doc('workspaces/ws1').get()).get('taskCount')).toBe(1);
  });
});
```

Run test files sequentially (`vitest --no-file-parallelism`, or `--runInBand` in Jest): they share one emulator and `resetEmulators` would wipe a parallel file's data.

## Testing Callables as a Signed-In User

The client SDK pointed at the Auth and Functions emulators exercises the real token path:

```typescript
// test/set-user-role.test.ts
import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth, signInWithEmailAndPassword } from 'firebase/auth';
import { connectFunctionsEmulator, getFunctions, httpsCallable } from 'firebase/functions';
import { beforeEach, expect, it } from 'vitest';
import { PROJECT_ID, adminAuth, createUser, resetEmulators } from './helpers/emulator';

const app = initializeApp({ projectId: PROJECT_ID, apiKey: 'demo-key' }, 'test-client');
const auth = getAuth(app);
connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
const functions = getFunctions(app, 'us-central1');
connectFunctionsEmulator(functions, '127.0.0.1', 5001);
const setUserRole = httpsCallable(functions, 'setUserRole');

beforeEach(async () => {
  await resetEmulators();
  await createUser('admin1', { role: 'admin' });
  await createUser('user1');
});

it('lets an admin grant a role', async () => {
  await signInWithEmailAndPassword(auth, 'admin1@example.test', 'test-password-1');
  await setUserRole({ uid: 'user1', role: 'editor' });
  expect((await adminAuth.getUser('user1')).customClaims?.role).toBe('editor');
});

it('rejects a non-admin', async () => {
  await signInWithEmailAndPassword(auth, 'user1@example.test', 'test-password-1');
  await expect(setUserRole({ uid: 'user1', role: 'admin' })).rejects.toMatchObject({
    code: 'functions/permission-denied',
  });
});
```

Callables with `enforceAppCheck: true` reject emulator calls without a token. Set the App Check debug token in the test client, or read the flag from a param so tests run with it off locally.

## CI (GitHub Actions)

```yaml
name: firebase-tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: 21 }
      - run: npm ci && npm --prefix functions ci && npm --prefix functions run build
      - uses: actions/cache@v4
        with:
          path: ~/.cache/firebase/emulators
          key: emulators-${{ hashFiles('package-lock.json') }}
      - run: npx firebase-tools emulators:exec --project demo-myapp "npm test"
```

No credentials are needed: `demo-` projects never call Google APIs. Pin `firebase-tools` as a dev dependency so local and CI emulators match.

## Related

- `security-rules.md` for `@firebase/rules-unit-testing` suites
- `cloud-functions.md` for the triggers under test
- `test-master` and `playwright-expert` skills for wider test strategy and E2E against the emulators
