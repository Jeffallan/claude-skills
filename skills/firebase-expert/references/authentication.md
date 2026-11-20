# Authentication

Firebase Authentication on the client (`firebase/auth`), token and session verification with `firebase-admin/auth` 14, custom claims for roles, and Identity Platform features such as blocking functions.

## When to Use

- Adding sign-in to a web app, or reading the current user in UI code
- Verifying users on a server, an API route or an `onRequest` function
- Assigning roles that Security Rules and servers can trust
- SSR apps (Next.js, Nuxt, Angular SSR) that need the user on the server
- Restricting sign-up (domain allowlist, invite-only) or adding MFA, SAML or OIDC

## When Not to Use

- Building your own password storage or JWT issuance: Firebase does this; see `secure-code-guardian` only if the project runs its own auth
- Mobile UI flows: FlutterFire (`flutter-expert`) and React Native Firebase (`react-native-expert`) use their own APIs; the Admin side below is the same

## Plans and Identity Platform

Upgrading to Firebase Authentication with Identity Platform needs no code migration and adds MFA, blocking functions, SAML (web) and OIDC providers, multi-tenancy and an SLA. Pricing as of late 2026:

| Plan | Email, social, anonymous, custom | SAML / OIDC |
| --- | --- | --- |
| Spark | 3,000 daily active users | 2 daily active users |
| Blaze | 49,999 MAU free, then per-MAU | 49 MAU free, then per-MAU |

Phone (SMS) sign-in bills per message on Blaze and is a fraud target. Turn on SMS region policy and App Check before enabling it.

## Client Sign-In

```typescript
// src/lib/auth.ts
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  type User,
} from 'firebase/auth';
import { auth } from './firebase';

export function watchUser(cb: (user: User | null) => void): () => void {
  return onAuthStateChanged(auth, cb); // fires once with the restored session, then on changes
}

export async function signInWithGoogle(): Promise<User> {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });
  const { user } = await signInWithPopup(auth, provider);
  return user;
}

export async function signInWithPassword(email: string, password: string): Promise<User> {
  const { user } = await signInWithEmailAndPassword(auth, email, password);
  return user;
}

export const logout = () => signOut(auth);

// Claims ride in the ID token. Force a refresh after a server changes them.
export async function currentRole(user: User, forceRefresh = false): Promise<string | undefined> {
  const { claims } = await user.getIdTokenResult(forceRefresh);
  return typeof claims.role === 'string' ? claims.role : undefined;
}
```

- Turn on email enumeration protection in the console; it makes sign-in errors generic.
- Show a generic message on `auth/invalid-credential`; never reveal whether an email exists.
- Add the production domain to Authorized domains; `localhost` is there by default.
- `signInWithRedirect` needs the auth helper served from the app's own domain in browsers that block third-party storage. Popup is the simpler default on the web.

## Verifying Users on a Server

```typescript
// server/firebase-admin.ts
import { getApp, getApps, initializeApp } from 'firebase-admin/app';
import { getAuth } from 'firebase-admin/auth';

// Application Default Credentials: the runtime service account on Cloud Run, Functions
// and App Hosting; `gcloud auth application-default login` locally. No key files.
const app = getApps().length ? getApp() : initializeApp();
export const adminAuth = getAuth(app);
```

```typescript
// server/require-user.ts (Express)
import type { NextFunction, Request, Response } from 'express';
import type { DecodedIdToken } from 'firebase-admin/auth';
import { adminAuth } from './firebase-admin';

declare module 'express-serve-static-core' {
  interface Request {
    user?: DecodedIdToken;
  }
}

export function requireUser(opts: { checkRevoked?: boolean } = {}) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const header = req.headers.authorization ?? '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;
    if (!token) return res.status(401).json({ error: 'unauthenticated' });
    try {
      // checkRevoked costs an extra Auth backend call; use it on sensitive routes
      req.user = await adminAuth.verifyIdToken(token, opts.checkRevoked ?? false);
      return next();
    } catch {
      return res.status(401).json({ error: 'unauthenticated' });
    }
  };
}

export function requireRole(role: string) {
  return (req: Request, res: Response, next: NextFunction) =>
    req.user?.role === role ? next() : res.status(403).json({ error: 'forbidden' });
}
```

The client sends `Authorization: Bearer ${await auth.currentUser.getIdToken()}`. ID tokens last one hour and the SDK refreshes them. Callable functions verify the token for you (`request.auth`), so prefer `onCall` over `onRequest` plus this middleware when the caller is your own app.

## Custom Claims for Roles

Claims are set only by trusted code, are capped at 1,000 bytes, and appear in the next ID token. Keep them to small, slow-changing facts (`admin: true`, `role: 'editor'`, `orgId`). Per-resource permissions belong in Firestore documents.

```typescript
// functions/src/roles.ts
import { getAuth } from 'firebase-admin/auth';
import { HttpsError, onCall } from 'firebase-functions/v2/https';

const ROLES = ['viewer', 'editor', 'admin'] as const;
type Role = (typeof ROLES)[number];

export const setUserRole = onCall<{ uid: string; role: Role }>(
  { enforceAppCheck: true },
  async (request) => {
    if (request.auth?.token.role !== 'admin') {
      throw new HttpsError('permission-denied', 'Admins only');
    }
    const { uid, role } = (request.data ?? {}) as Partial<{ uid: string; role: Role }>;
    if (typeof uid !== 'string' || !role || !ROLES.includes(role)) {
      throw new HttpsError('invalid-argument', 'uid and a valid role are required');
    }
    const user = await getAuth().getUser(uid);
    await getAuth().setCustomUserClaims(uid, { ...user.customClaims, role });
    return { ok: true };
  },
);
```

`setCustomUserClaims` replaces the whole claims object, hence the merge. The affected user sees the change after `getIdTokenResult(user, true)` or within the hour. Bootstrap the first admin from a one-off Admin script, not from client code.

## Session Cookies for SSR

SSR pages cannot read the client SDK's IndexedDB session. Exchange a fresh ID token for an httpOnly session cookie (5 minutes to 2 weeks).

```typescript
// app/api/session/route.ts (Next.js App Router)
import { cookies, headers } from 'next/headers';
import { NextResponse } from 'next/server';
import { adminAuth } from '@/server/firebase-admin';

const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;

export async function POST(req: Request) {
  // CSRF: only accept same-origin posts
  const origin = (await headers()).get('origin');
  if (origin !== process.env.APP_ORIGIN) {
    return NextResponse.json({ error: 'bad origin' }, { status: 403 });
  }
  const { idToken } = (await req.json()) as { idToken?: string };
  if (!idToken) return NextResponse.json({ error: 'missing token' }, { status: 400 });

  const decoded = await adminAuth.verifyIdToken(idToken);
  if (Date.now() / 1000 - decoded.auth_time > 5 * 60) {
    return NextResponse.json({ error: 'recent sign-in required' }, { status: 401 });
  }
  const session = await adminAuth.createSessionCookie(idToken, { expiresIn: FIVE_DAYS_MS });
  // Firebase Hosting forwards only the cookie named __session to rewrites
  (await cookies()).set('__session', session, {
    maxAge: FIVE_DAYS_MS / 1000,
    httpOnly: true,
    secure: true,
    sameSite: 'lax',
    path: '/',
  });
  return NextResponse.json({ ok: true });
}

export async function DELETE() {
  const jar = await cookies();
  const session = jar.get('__session')?.value;
  jar.delete('__session');
  if (session) {
    const decoded = await adminAuth.verifySessionCookie(session).catch(() => null);
    if (decoded) await adminAuth.revokeRefreshTokens(decoded.sub);
  }
  return NextResponse.json({ ok: true });
}
```

```typescript
// server/current-user.ts
import { cookies } from 'next/headers';
import type { DecodedIdToken } from 'firebase-admin/auth';
import { adminAuth } from './firebase-admin';

export async function currentUser(): Promise<DecodedIdToken | null> {
  const session = (await cookies()).get('__session')?.value;
  if (!session) return null;
  try {
    return await adminAuth.verifySessionCookie(session, true); // true: honour revocation
  } catch {
    return null;
  }
}
```

The client calls `POST /api/session` with `await user.getIdToken()` right after sign-in. Server reads with the Admin SDK bypass rules, so filter by `currentUser().uid` in every query the server runs.

## Blocking Functions (Identity Platform)

Blocking functions run before sign-up or sign-in completes, can reject it, and can set claims. They time out after 7 seconds, so keep them to fast checks.

```typescript
// functions/src/auth-blocking.ts
import { beforeUserCreated, beforeUserSignedIn } from 'firebase-functions/v2/identity';
import { HttpsError } from 'firebase-functions/v2/https';

const ALLOWED_DOMAIN = 'acme.com';

export const allowCompanyAccounts = beforeUserCreated((event) => {
  const email = event.data?.email?.toLowerCase() ?? '';
  if (!email.endsWith(`@${ALLOWED_DOMAIN}`) || !event.data?.emailVerified) {
    throw new HttpsError('permission-denied', 'Use a verified company account');
  }
  return { customClaims: { role: 'viewer' } };
});

export const blockDisabledTenants = beforeUserSignedIn((event) => {
  if (event.data?.customClaims?.suspended === true) {
    throw new HttpsError('permission-denied', 'Account suspended');
  }
});
```

After the first deploy, confirm they are registered under Authentication, Settings, Blocking functions in the console. Email-and-password sign-ups arrive with `emailVerified: false`; send a verification email and check `request.auth.token.email_verified` in rules for anything sensitive.

## Account Lifecycle

- Delete user data in a function triggered by account deletion (2nd gen Auth triggers became GA in firebase-functions 7.4.0) or by a callable "delete my account" flow that calls `getAuth().deleteUser(uid)` and `recursiveDelete` on the user's documents.
- Disable instead of delete when you need an audit trail: `updateUser(uid, { disabled: true })` plus `revokeRefreshTokens(uid)`.
- Anonymous accounts can be linked later with `linkWithPopup`/`linkWithCredential`; turn on automatic clean-up of anonymous accounts older than 30 days.

## Related

- `security-rules.md` for rules that read `request.auth.token` claims
- `cloud-functions.md` for callable function patterns
- `nextjs-developer` skill for middleware and Server Components around `currentUser()`
- `secure-code-guardian` skill for CSRF, cookie and header hardening
