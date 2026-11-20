# Security Rules

Firestore and Cloud Storage Security Rules (rules language v2) and their unit tests with `@firebase/rules-unit-testing` 6 against the Emulator Suite.

## When to Use

- Any new collection, subcollection or Storage path
- Auditing rules before launch or after a `permission-denied` report
- Moving a privileged write (roles, balances, counters) out of the client

## When Not to Use

- Admin SDK code in functions or servers: rules do not apply there, so validate in code (`cloud-functions.md`)
- Generic web hardening (CSP, CORS, rate limiting): use `secure-code-guardian`

## Principles

1. **Deny by default.** No `match /{document=**}` allow-all, no test-mode expiry rule in a deployed project.
2. **Identity comes from the token.** `request.auth.uid` and custom claims (`request.auth.token.role`) are trustworthy; any `ownerId`, `role` or `createdAt` in `request.resource.data` is whatever the client sent.
3. **Validate the whole document on create** with `keys().hasOnly()` plus type and size checks, and **restrict updates** with `diff().affectedKeys().hasOnly()`.
4. **Rules are not filters.** A query is rejected unless every document it could return passes the rule, so the query must constrain on the fields the rule checks.
5. **Server-only fields live where clients cannot write**, and privileged changes go through functions using the Admin SDK.
6. **Each `get()`/`exists()` costs a read** per dependent document per request, and a request may evaluate at most 10 (20 for batched writes and transactions). Prefer custom claims for roles that rarely change.

## Firestore Rules

```text
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    function signedIn() {
      return request.auth != null;
    }
    function isSelf(uid) {
      return signedIn() && request.auth.uid == uid;
    }
    function isAdmin() {
      return signedIn() && request.auth.token.admin == true;
    }
    function memberPath(wsId) {
      return /databases/$(database)/documents/workspaces/$(wsId)/members/$(request.auth.uid);
    }
    function isMember(wsId) {
      return signedIn() && exists(memberPath(wsId));
    }
    function roleIn(wsId, roles) {
      return isMember(wsId) && get(memberPath(wsId)).data.role in roles;
    }
    function validName(v) {
      return v is string && v.size() > 0 && v.size() <= 80;
    }

    match /users/{uid} {
      allow read: if isSelf(uid);
      allow create: if isSelf(uid)
        && request.resource.data.keys().hasOnly(['displayName', 'photoURL', 'createdAt'])
        && validName(request.resource.data.displayName)
        && request.resource.data.createdAt == request.time;
      allow update: if isSelf(uid)
        && request.resource.data.diff(resource.data).affectedKeys().hasOnly(['displayName', 'photoURL'])
        && validName(request.resource.data.displayName);
      allow delete: if false; // account deletion runs in a function

      match /private/{docId} {
        allow read, write: if isSelf(uid);
      }
    }

    match /workspaces/{wsId} {
      allow read: if isMember(wsId);
      allow create: if signedIn()
        && request.resource.data.keys().hasOnly(['name', 'ownerId', 'createdAt'])
        && request.resource.data.ownerId == request.auth.uid
        && validName(request.resource.data.name)
        && request.resource.data.createdAt == request.time;
      allow update: if roleIn(wsId, ['owner', 'admin'])
        && request.resource.data.diff(resource.data).affectedKeys().hasOnly(['name']);
      allow delete: if false;

      // Membership is written by a function (Admin SDK) when an invite is accepted.
      match /members/{memberId} {
        allow read: if isMember(wsId);
        allow write: if false;
      }

      match /tasks/{taskId} {
        allow read: if isMember(wsId);
        allow create: if roleIn(wsId, ['owner', 'admin', 'editor'])
          && request.resource.data.keys().hasOnly(['title', 'status', 'assigneeId', 'dueAt', 'updatedAt'])
          && validName(request.resource.data.title)
          && request.resource.data.status in ['todo', 'doing', 'done']
          && request.resource.data.updatedAt == request.time;
        allow update: if roleIn(wsId, ['owner', 'admin', 'editor'])
          && request.resource.data.diff(resource.data).affectedKeys()
               .hasOnly(['title', 'status', 'assigneeId', 'dueAt', 'updatedAt'])
          && request.resource.data.status in ['todo', 'doing', 'done']
          && request.resource.data.updatedAt == request.time;
        allow delete: if roleIn(wsId, ['owner', 'admin']);
      }
    }

    // Collection group query over every workspace's tasks: only for admins.
    match /{path=**}/tasks/{taskId} {
      allow read: if isAdmin();
    }
  }
}
```

Notes:

- `request.time` equality works because the client writes `serverTimestamp()`.
- `allow write` splits into `create`, `update` and `delete`; `allow read` into `get` and `list`. Split `list` off when a document may be fetched by ID but the collection must not be enumerated, and cap list sizes with `request.query.limit <= 50`.
- Rules OR together: if any `allow` matches, the request passes, so a broad rule on a parent path with `{document=**}` overrides every narrower rule beneath it.

## Matching Queries to Rules

```typescript
import { collection, getDocs, limit, query, where } from 'firebase/firestore';
import { db } from './firebase';

// Rule on /invites/{id}: allow list: if request.auth.uid == resource.data.toUid;
// Rejected: the query could return invites addressed to other users.
// await getDocs(collection(db, 'invites'));

// Accepted: the filter proves every result passes.
export const myInvites = (uid: string) =>
  getDocs(query(collection(db, 'invites'), where('toUid', '==', uid), limit(50)));
```

## Cloud Storage Rules

```text
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {

    function signedIn() { return request.auth != null; }
    function isImage() { return request.resource.contentType.matches('image/(png|jpeg|webp)'); }

    match /users/{uid}/avatar.{ext} {
      allow read: if signedIn();
      allow write: if signedIn() && request.auth.uid == uid
        && request.resource.size < 2 * 1024 * 1024
        && isImage();
    }

    // Cross-service check: member documents live in Firestore.
    match /workspaces/{wsId}/files/{fileId} {
      allow read: if signedIn() && firestore.exists(
        /databases/(default)/documents/workspaces/$(wsId)/members/$(request.auth.uid));
      allow create: if signedIn()
        && firestore.exists(/databases/(default)/documents/workspaces/$(wsId)/members/$(request.auth.uid))
        && request.resource.size < 25 * 1024 * 1024;
      allow update, delete: if false;
    }
  }
}
```

- Cross-service rules need the Storage service agent to have Firestore read access; the console prompts for it on first deploy.
- Without App Check enforcement, a valid user can still script uploads up to the size cap. Combine size limits with App Check (`storage-app-check.md`).

## Rules Unit Tests

`firebase.json` points the emulators at the rule files. Tests run under `firebase emulators:exec` so the ports are up.

```typescript
// test/firestore.rules.test.ts (vitest)
import { readFileSync } from 'node:fs';
import {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
  type RulesTestContext,
  type RulesTestEnvironment,
} from '@firebase/rules-unit-testing';
import {
  doc,
  getDoc,
  serverTimestamp,
  setDoc,
  updateDoc,
  type Firestore,
} from 'firebase/firestore';
import { afterAll, beforeAll, beforeEach, describe, it } from 'vitest';

let env: RulesTestEnvironment;

// shortcut: context.firestore() is typed as the compat instance; modular functions
// accept it at runtime. Drop the cast if rules-unit-testing ships modular types.
const dbOf = (ctx: RulesTestContext) => ctx.firestore() as unknown as Firestore;

beforeAll(async () => {
  env = await initializeTestEnvironment({
    projectId: 'demo-rules-test', // demo- prefix: never touches a real project
    firestore: { rules: readFileSync('firestore.rules', 'utf8') },
  });
});

beforeEach(async () => {
  await env.clearFirestore();
  await env.withSecurityRulesDisabled(async (ctx) => {
    const db = dbOf(ctx);
    await setDoc(doc(db, 'workspaces/ws1'), { name: 'Acme', ownerId: 'alice' });
    await setDoc(doc(db, 'workspaces/ws1/members/alice'), { role: 'owner' });
    await setDoc(doc(db, 'workspaces/ws1/members/bob'), { role: 'viewer' });
    await setDoc(doc(db, 'workspaces/ws1/tasks/t1'), { title: 'Ship', status: 'todo' });
  });
});

afterAll(async () => {
  await env.cleanup();
});

describe('users', () => {
  it('lets a user create their own profile with a server timestamp', async () => {
    const db = dbOf(env.authenticatedContext('alice'));
    await assertSucceeds(
      setDoc(doc(db, 'users/alice'), { displayName: 'Alice', createdAt: serverTimestamp() }),
    );
  });

  it('rejects extra fields such as a self-assigned role', async () => {
    const db = dbOf(env.authenticatedContext('alice'));
    await assertFails(
      setDoc(doc(db, 'users/alice'), {
        displayName: 'Alice',
        createdAt: serverTimestamp(),
        role: 'admin',
      }),
    );
  });

  it('denies reading another user', async () => {
    const db = dbOf(env.authenticatedContext('bob'));
    await assertFails(getDoc(doc(db, 'users/alice')));
  });
});

describe('workspace tasks', () => {
  it('lets members read tasks and denies outsiders', async () => {
    await assertSucceeds(getDoc(doc(dbOf(env.authenticatedContext('bob')), 'workspaces/ws1/tasks/t1')));
    await assertFails(getDoc(doc(dbOf(env.authenticatedContext('eve')), 'workspaces/ws1/tasks/t1')));
    await assertFails(getDoc(doc(dbOf(env.unauthenticatedContext()), 'workspaces/ws1/tasks/t1')));
  });

  it('denies viewers editing tasks', async () => {
    const db = dbOf(env.authenticatedContext('bob'));
    await assertFails(
      updateDoc(doc(db, 'workspaces/ws1/tasks/t1'), { status: 'done', updatedAt: serverTimestamp() }),
    );
  });

  it('honours an admin custom claim for collection group reads', async () => {
    const db = dbOf(env.authenticatedContext('root', { admin: true }));
    await assertSucceeds(getDoc(doc(db, 'workspaces/ws1/tasks/t1')));
  });
});
```

Run with `firebase emulators:exec --only firestore "npx vitest run test/firestore.rules.test.ts"`. Storage rules are tested the same way with `storage: { rules }` in the config, `ctx.storage()`, and `env.clearStorage()`.

Every rule gets at least one allowed and one denied case, including unauthenticated access, another user's data, an extra field and a forged server field.

## Audit Checklist

| Check | Look for |
| --- | --- |
| Open rules | `if true`, `request.time < timestamp.date(` , `{document=**}` with allow |
| Client-trusted identity | `request.resource.data.ownerId` compared to nothing, roles read from the request |
| Unvalidated create | No `keys().hasOnly(...)` on create |
| Unrestricted update | No `diff(...).affectedKeys().hasOnly(...)` |
| Enumerable private data | `allow read` where only `get` was intended |
| Storage | No `request.resource.size` and `contentType` checks |
| Deploy drift | Rules edited in the console and not in the repo; `firebase deploy --only firestore:rules,storage` from CI |

## Related

- `authentication.md` for setting the custom claims these rules read
- `emulators-testing.md` for `firebase.json` emulator config and CI
- `secure-code-guardian` and `security-reviewer` skills for broader audits
