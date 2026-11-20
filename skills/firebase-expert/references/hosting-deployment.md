# Hosting and Deployment

Choosing between Firebase Hosting and App Hosting, configuring each, separating environments, and deploying rules, indexes and functions from CI without service-account keys.

## When to Use

- Shipping a static site, SPA, or an SSR app (Next.js, Angular, others) on Firebase
- Setting up dev, staging and production projects
- Writing the CI job that deploys Firebase resources

## When Not to Use

- Kubernetes, multi-cloud or custom networking: `cloud-architect`, `kubernetes-specialist` or `terraform-engineer`
- Framework build questions unrelated to Firebase: the framework's own skill (`nextjs-developer`, `angular-architect`)

## Hosting or App Hosting

| | Firebase Hosting | App Hosting |
| --- | --- | --- |
| Serves | Static files and SPAs from a global CDN; rewrites to Functions or Cloud Run | Full-stack SSR apps built from source |
| Frameworks | Any static build; framework-aware deploys are still an experiment | Next.js and Angular preconfigured; other frameworks through community adapters |
| Build | Your CI builds, `firebase deploy` uploads | Cloud Build from a connected GitHub branch, runs on Cloud Run behind Cloud CDN |
| Plan | Spark works for static | Blaze required |
| Config | `firebase.json` `hosting` block | `apphosting.yaml` (plus `apphosting.<env>.yaml`) |

Rule of thumb: static or client-rendered app, use Hosting. SSR, server actions or API routes in the framework, use App Hosting.

## Firebase Hosting

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "cleanUrls": true,
    "rewrites": [
      { "source": "/api/**", "function": { "functionId": "api", "region": "us-central1" } },
      { "source": "**", "destination": "/index.html" }
    ],
    "headers": [
      {
        "source": "/assets/**",
        "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }]
      },
      {
        "source": "**",
        "headers": [
          { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains" },
          { "key": "X-Content-Type-Options", "value": "nosniff" },
          { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
        ]
      }
    ]
  }
}
```

- Rewrites to functions forward only the cookie named `__session`; name the session cookie that (`authentication.md`).
- Preview channels give each pull request a temporary URL: `firebase hosting:channel:deploy pr-123 --expires 7d`. Add the channel domain to Auth authorized domains if the preview signs users in.
- Content Security Policy depends on the app; build it with `secure-code-guardian` and allow the Firebase endpoints you use (`*.googleapis.com`, `*.firebaseapp.com`, the reCAPTCHA domains for App Check).

## App Hosting

```yaml
# apphosting.yaml (committed; values here apply to every environment)
runConfig:
  minInstances: 0 # 1+ removes cold starts and bills idle time
  maxInstances: 10 # caps spend
  concurrency: 80
  cpu: 1
  memoryMiB: 1024

env:
  - variable: APP_ORIGIN
    value: https://app.example.com
    availability: [BUILD, RUNTIME]
  - variable: PAYMENTS_API_KEY
    secret: paymentsApiKey # Cloud Secret Manager, never a plain value
    availability: [RUNTIME]
```

```yaml
# apphosting.staging.yaml (overrides for the backend whose environment is "staging")
env:
  - variable: APP_ORIGIN
    value: https://staging.example.com
```

```bash
firebase apphosting:backends:create --project my-app-prod           # once, links GitHub repo and branch
firebase apphosting:secrets:set paymentsApiKey --project my-app-prod # creates the secret and grants access
firebase apphosting:rollouts:create <backend-id> --git_branch main   # manual rollout; pushes to the live branch also roll out
```

- App Hosting injects the project's Firebase config at build and run time, so `initializeApp()` from `firebase-admin/app` needs no arguments and runs as the backend's service account.
- Only variables needed in the browser get `BUILD` availability (for Next.js, the `NEXT_PUBLIC_` ones). Secrets stay `RUNTIME` only.
- Roll back from the console or by rolling out an earlier commit.

## Environments

Use one Firebase project per environment. Rules, indexes and data never leak between them, and quotas and billing alerts stay separate.

```json
{
  "projects": {
    "default": "demo-myapp",
    "staging": "my-app-staging",
    "prod": "my-app-prod"
  }
}
```

```bash
firebase use staging                     # .firebaserc alias
firebase deploy --only firestore:rules,firestore:indexes,storage --project staging
firebase deploy --only functions:createCheckout --project prod   # one function
```

- Functions read per-project params from `functions/.env.<projectId>` or `.env.<alias>`, and secrets from each project's Secret Manager.
- Web config (`apiKey`, `appId`) differs per project. Supply it from build-time env vars, not a hardcoded object shared by all builds.
- Restrict each browser API key in Google Cloud console to the Firebase APIs and the app's HTTP referrers.
- Set a billing budget with alerts on every Blaze project.

## Deploying from CI without Keys

Use Workload Identity Federation: GitHub's OIDC token is exchanged for short-lived Google credentials, so no JSON key exists to leak.

```yaml
name: deploy-firebase
on:
  push:
    branches: [main]
permissions:
  contents: read
  id-token: write # required for OIDC
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: npm }
      - run: npm ci && npm run build && npm --prefix functions ci && npm --prefix functions run build
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.WIF_PROVIDER }}
          service_account: ${{ vars.DEPLOY_SERVICE_ACCOUNT }}
      - run: >
          npx firebase-tools deploy
          --project my-app-prod
          --only hosting,functions,firestore:rules,firestore:indexes,storage
          --non-interactive --force
```

- Grant the deploy service account only the roles the targets need (for example Firebase Hosting Admin, Firebase Rules Admin, Cloud Datastore Index Admin, Cloud Functions Developer, Service Account User on the runtime account, Secret Manager Viewer). Avoid Owner and Editor.
- `--force` lets the CLI delete functions removed from source without a prompt; drop it if deletions should need a human.
- Run the emulator test job (`emulators-testing.md`) before deploy, and deploy rules in the same pipeline as the code that depends on them.
- `firebase deploy --dry-run` validates config and reports which resources it would create.

## Indexes and Rules Drift

- `firebase firestore:indexes > firestore.indexes.json` pulls indexes created in the console into the repo. Review the diff: deploying with `--force` deletes indexes that are not in the file.
- Never edit rules in the console on a project CI deploys to; the next deploy overwrites the change.
- Index builds on large collections take minutes to hours. Deploy indexes before the code that queries them.

## Related

- `authentication.md` for session cookies behind Hosting rewrites
- `cloud-functions.md` for function runtime options
- `devops-engineer` skill for wider CI/CD design, `cloud-architect` for multi-region and disaster recovery
