---
name: firebase-expert
description: "Builds, secures and reviews Firebase apps with the modular JS SDK (firebase 13), firebase-admin 14 and Cloud Functions 2nd gen: Firestore data modeling, queries, indexes, transactions and offline cache, Firestore and Storage Security Rules with emulator tests, Firebase Authentication and Identity Platform (custom claims, session cookies, blocking functions), callable and event-triggered functions with secrets, App Check, Firebase Hosting and App Hosting deploys, and Firestore cost control. Use when code imports from firebase/*, firebase-admin or firebase-functions, when editing firestore.rules, storage.rules, firestore.indexes.json, firebase.json or apphosting.yaml, when choosing between Firestore, Realtime Database and SQL Connect, or when diagnosing permission-denied errors, missing-index errors, runaway read costs or functions that loop on their own writes. Not for Supabase, AWS Amplify or plain Google Cloud projects with no Firebase."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: platform
  triggers: Firebase, Firestore, Cloud Firestore, Firebase Auth, Firebase Authentication, Identity Platform, Security Rules, firestore.rules, storage.rules, Cloud Functions for Firebase, firebase-functions, firebase-admin, Firebase Hosting, App Hosting, Firebase Emulator, App Check, Cloud Storage for Firebase, Realtime Database, SQL Connect, Data Connect, Firebase AI Logic
  role: expert
  scope: implementation
  output-format: code
  related-skills: cloud-architect, secure-code-guardian, nextjs-developer, react-expert, flutter-expert, react-native-expert
---

# Firebase Expert

Senior Firebase engineer for the modular JS SDK 13, firebase-admin 14 (Node 22+), firebase-functions 7 on Cloud Functions 2nd gen and firebase-tools 15: data shaped for the queries the app runs, Security Rules that enforce every invariant the client could fake, and every change proven against the Emulator Suite before deploy.

## When to Use This Skill

- Designing Firestore collections, queries, composite indexes, transactions and listeners for a web or Node app
- Writing or auditing `firestore.rules` and `storage.rules`, and testing them with `@firebase/rules-unit-testing`
- Adding sign-in, custom claims, SSR session cookies or blocking functions with Firebase Auth / Identity Platform
- Writing 2nd gen Cloud Functions (callable, HTTP, Firestore, Storage, scheduled, task queue) with params and secrets
- Deploying to Firebase Hosting or App Hosting, wiring App Check, or cutting a Firestore bill

## Core Workflow

1. **Inventory**: Read `package.json` pins, `firebase.json`, `.firebaserc`, the rules and index files; note the Firestore edition, the plan (Blaze is required for Functions, App Hosting and Cloud Storage) and whether the code is modular or compat
2. **Model**: Shape documents around the screens' queries, list every query with its index, estimate reads per screen
3. **Secure**: Write rules for every collection and bucket path first: auth, ownership from `request.auth.uid`, validated fields, server-only fields; privileged work goes to functions using the Admin SDK
4. **Build**: Modular client code, 2nd gen functions with `defineSecret`/`defineString`, idempotent triggers, App Check on clients and enforced on callables
5. **Verify & deploy**: Run rules and function tests under `firebase emulators:exec`, fix failures and re-run until green, then `firebase deploy --only` the changed targets and check the console for index builds and errors

## Reference Guide

| Topic | Reference | Load When |
| --- | --- | --- |
| Firestore | `references/firestore.md` | Data modeling, converters, queries, indexes, pagination, aggregation, transactions, batches, listeners, offline cache, read costs, RTDB and SQL Connect choice |
| Security Rules | `references/security-rules.md` | `firestore.rules`, `storage.rules`, validation helpers, role claims, rules-vs-queries, rules unit tests |
| Authentication | `references/authentication.md` | Client sign-in, Admin token verification, custom claims, session cookies for SSR, blocking functions, Identity Platform |
| Cloud Functions | `references/cloud-functions.md` | 2nd gen triggers, callable functions, params and secrets, idempotency, retries, concurrency, regions |
| Storage, App Check & AI Logic | `references/storage-app-check.md` | Uploads, Storage paths and metadata, App Check providers and enforcement, Firebase AI Logic client calls |
| Emulators & testing | `references/emulators-testing.md` | `firebase.json` emulators, connecting SDKs, seeding, function integration tests, CI with `emulators:exec` |
| Hosting & deployment | `references/hosting-deployment.md` | Hosting vs App Hosting, `apphosting.yaml`, environments and project aliases, CI auth without keys, index and rules deploys |

## Minimal Working Example

Client init that talks to the emulators in development and caches offline:

```typescript
// src/lib/firebase.ts
import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import {
  connectFirestoreEmulator,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from 'firebase/firestore';

export const app = initializeApp({
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY, // public identifier, not a secret
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
});

export const auth = getAuth(app);
export const db = initializeFirestore(app, {
  localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }),
});

if (import.meta.env.DEV) {
  connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
  connectFirestoreEmulator(db, '127.0.0.1', 8080);
}
```

## Constraints

### MUST DO

- Use the modular API (`firebase/firestore`, `firebase-admin/firestore`); leave existing compat code alone unless asked to migrate
- Deny by default in rules; derive identity from `request.auth.uid` and custom claims, set timestamps with `request.time` / `serverTimestamp()`, restrict updates with `diff().affectedKeys().hasOnly()`
- Give every query a bounded `limit()` and its composite index in `firestore.indexes.json`
- Make event-triggered functions idempotent (key on `event.id`) and guard against re-triggering on their own writes
- Read secrets with `defineSecret` and bind them per function; enforce App Check on callables the client uses
- Test rules and functions against the emulators, and commit rules and indexes to the repo

### MUST NOT DO

- Ship test-mode or `allow read, write: if true` rules, or trust `role`, `ownerId` or `createdAt` sent by the client
- Commit service-account JSON keys or call `initializeApp` with a key file on Google infrastructure (use ADC, Workload Identity Federation in CI)
- Use `functions.config()` (removed in firebase-functions 7) or start new 1st gen functions
- Attach `onSnapshot` to unbounded collections, or read one document per list row (N+1)
- Use the Admin SDK in client bundles, or treat the web `apiKey` as the security boundary

## Output Templates

When implementing a Firebase feature, provide:

1. Data model (collection paths, document shapes, the queries and their indexes) and the `firestore.indexes.json` entries
2. Rules for every new path, with emulator tests that show allowed and denied cases
3. Client and function code, plus the `firebase deploy --only ...` targets, secrets to set and plan requirements
4. A note on expected reads per screen and any cost or quota risk

## Knowledge Reference

Firebase JS SDK 13 (modular), firebase-admin 14, firebase-functions 7, firebase-tools 15, Cloud Firestore Standard and Enterprise editions, Security Rules v2, @firebase/rules-unit-testing 6, Firebase Authentication, Identity Platform, custom claims, session cookies, blocking functions, Cloud Functions 2nd gen (Cloud Run, Eventarc), params and Secret Manager, Cloud Storage for Firebase, App Check (reCAPTCHA Enterprise, Play Integrity, App Attest), Firebase Hosting, App Hosting, Emulator Suite, Realtime Database, SQL Connect, Firebase AI Logic

## Related Skills

- `cloud-architect`: wider Google Cloud topology, multi-region and disaster recovery beyond Firebase
- `secure-code-guardian`: generic auth hardening, input validation and OWASP controls
- `nextjs-developer`, `react-expert`: UI and SSR around the Firebase data layer
- `flutter-expert`, `react-native-expert`: mobile clients (FlutterFire, React Native Firebase); rules, indexes and functions here still apply

Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/platform/firebase-expert/)
