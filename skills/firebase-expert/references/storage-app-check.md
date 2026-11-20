# Cloud Storage, App Check and AI Logic

File uploads with Cloud Storage for Firebase, App Check to keep scripted clients off your backends, and Firebase AI Logic calls from the client behind App Check.

## When to Use

- Users upload or download files (avatars, attachments, exports)
- Protecting Firestore, Storage, Functions, Auth or AI Logic from traffic that does not come from your app
- Calling Gemini models from a web or mobile client without shipping an API key

## When Not to Use

- Server-side AI pipelines, agents, RAG or evals: use Genkit or a server SDK with the `prompt-engineer` and `rag-architect` skills
- Bulk object storage with no Firebase client: plain Google Cloud Storage with the `cloud-architect` skill

## Plan Requirements

Since 2026-02-03 a default Storage bucket needs the Blaze plan, and Spark projects lose access to all buckets (API calls fail with 402 or 403) until they upgrade. New default buckets are named `PROJECT_ID.firebasestorage.app`; existing `PROJECT_ID.appspot.com` buckets keep their names and their no-cost usage level on Blaze.

## Uploads

```typescript
// src/lib/uploads.ts
import {
  getDownloadURL,
  getStorage,
  ref,
  uploadBytesResumable,
  type UploadTask,
} from 'firebase/storage';
import { app, auth } from './firebase';

const storage = getStorage(app);
const MAX_BYTES = 25 * 1024 * 1024; // keep in step with storage.rules

export function uploadAttachment(
  wsId: string,
  file: File,
  onProgress: (pct: number) => void,
): { task: UploadTask; done: Promise<string> } {
  if (!auth.currentUser) throw new Error('Sign in first');
  if (file.size > MAX_BYTES) throw new Error('File too large');

  // Random object name: never use the user's file name as the path
  const path = `workspaces/${wsId}/files/${crypto.randomUUID()}`;
  const task = uploadBytesResumable(ref(storage, path), file, {
    contentType: file.type || 'application/octet-stream',
    customMetadata: { originalName: file.name.slice(0, 200), uploadedBy: auth.currentUser.uid },
  });

  const done = new Promise<string>((resolve, reject) => {
    task.on(
      'state_changed',
      (s) => onProgress(Math.round((s.bytesTransferred / s.totalBytes) * 100)),
      reject, // storage/unauthorized means the rules said no
      () => resolve(path),
    );
  });
  return { task, done }; // task.cancel() aborts
}

export const fileUrl = (path: string) => getDownloadURL(ref(storage, path));
```

- Store the object **path** in Firestore, not the download URL. A download URL carries a long-lived token: anyone holding it can read the file whatever the rules say, until the token is revoked in the console.
- For private files, read through the SDK (`getBlob`, `getBytes`), which applies rules, or have a function return a short-lived signed URL from `firebase-admin/storage` (`file.getSignedUrl({ action: 'read', expires })`).
- Client-side checks are for UX only. Rules enforce size and content type (`security-rules.md`).
- Set a lifecycle rule on the bucket for temporary uploads, and a CORS config (`gsutil cors set`) only if the browser fetches download URLs directly with `fetch`.

## App Check

App Check attaches an attestation token to requests to Firestore, Storage, Realtime Database, Auth, callable functions and AI Logic. Providers: reCAPTCHA Enterprise (web), Play Integrity (Android), App Attest with DeviceCheck fallback (Apple). It blocks nothing until you enforce it per product.

```typescript
// src/lib/app-check.ts: import this right after initializeApp, before other SDK calls
import { initializeAppCheck, ReCaptchaEnterpriseProvider } from 'firebase/app-check';
import { app } from './firebase';

declare global {
  // eslint-disable-next-line no-var
  var FIREBASE_APPCHECK_DEBUG_TOKEN: boolean | string | undefined;
}

if (import.meta.env.DEV) {
  // Prints a debug token in the console; register it under App Check, Apps, Manage debug tokens.
  // In CI, set it to the registered token string from a secret instead of true.
  globalThis.FIREBASE_APPCHECK_DEBUG_TOKEN = import.meta.env.VITE_APPCHECK_DEBUG_TOKEN ?? true;
}

export const appCheck = initializeAppCheck(app, {
  provider: new ReCaptchaEnterpriseProvider(import.meta.env.VITE_RECAPTCHA_ENTERPRISE_KEY),
  isTokenAutoRefreshEnabled: true, // off by default
});
```

### Rolling Out Enforcement

1. Ship the client with App Check initialized; old app versions without it keep working while unenforced.
2. Watch the App Check metrics per product until verified requests dominate and the unverified ones look like abuse, not your users on old builds.
3. Enforce per product in the console (Firestore, Storage, Auth, AI Logic), and in code for callables with `enforceAppCheck: true` (`cloud-functions.md`).
4. Keep debug tokens out of production builds and rotate any that leak.

### Custom Backends

A server you run yourself (Cloud Run, Express) verifies the header the client sends:

```typescript
// server/app-check.ts
import type { NextFunction, Request, Response } from 'express';
import { getAppCheck } from 'firebase-admin/app-check';

export async function requireAppCheck(req: Request, res: Response, next: NextFunction) {
  const token = req.get('X-Firebase-AppCheck');
  if (!token) return res.status(401).json({ error: 'unauthorized' });
  try {
    await getAppCheck().verifyToken(token);
    return next();
  } catch {
    return res.status(401).json({ error: 'unauthorized' });
  }
}
```

The client gets the token with `getToken(appCheck, false)` from `firebase/app-check` and sends it in that header. For one-shot sensitive endpoints, request a limited-use token (`getLimitedUseToken(appCheck)`) and verify with `verifyToken(token, { consume: true })` for replay protection.

App Check raises the cost of abuse; it does not authenticate users. Keep Auth checks and rules in place.

## Firebase AI Logic

AI Logic (formerly Vertex AI in Firebase) proxies Gemini calls from the client, so no model API key ships in the bundle. Backends: the Gemini Developer API (`GoogleAIBackend`) or the Agent Platform Gemini API (formerly Vertex AI, `AgentPlatformBackend` since JS SDK 13; `VertexAIBackend` was removed).

```typescript
// src/lib/ai.ts
import { getAI, getGenerativeModel, GoogleAIBackend } from 'firebase/ai';
import { app } from './firebase';
import './app-check';

const ai = getAI(app, {
  backend: new GoogleAIBackend(),
  useLimitedUseAppCheckTokens: true, // pairs with replay protection in the console
});

// Check the AI Logic models page for current names before shipping
const model = getGenerativeModel(ai, { model: 'gemini-3.5-flash-lite' });

export async function summarize(text: string): Promise<string> {
  const result = await model.generateContent(
    `Summarize in three bullet points:\n\n${text.slice(0, 20_000)}`,
  );
  return result.response.text();
}
```

- Enforce App Check on AI Logic before launch, and set per-user rate limits in the console. Without them, anyone can spend your model quota.
- Treat model output as untrusted input: escape it before rendering and never pass it to `eval`, rules or Admin writes unchecked.
- JS SDK 13 deprecated `temperature`, `topP`, `topK` and `candidateCount` (unsupported on Gemini 3.x); remove them from older code.
- Use server prompt templates to change the model or prompt without a client release, and keep secret system instructions there rather than in the bundle.

## Related

- `security-rules.md` for Storage rules and their tests
- `cloud-functions.md` for `onObjectFinalized` processing and callables with `enforceAppCheck`
- `prompt-engineer` skill for prompt design and evaluation
