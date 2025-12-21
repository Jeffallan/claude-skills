# GitOps

> Reference for: Kubernetes Specialist
> Load when: ArgoCD, Flux, GitOps, continuous delivery, progressive delivery, Flagger, sealed secrets, SOPS

---

## GitOps Principles

1. **Declarative** - Entire system described declaratively
2. **Versioned and immutable** - Desired state stored in Git
3. **Pulled automatically** - Agents pull state from Git
4. **Continuously reconciled** - Agents ensure actual matches desired

## ArgoCD Installation

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Install CLI
brew install argocd

# Login
argocd login localhost:8080 --username admin --password <password>

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/myapp-manifests.git
    targetRevision: main
    path: overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

## ArgoCD ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-environments
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: dev
            namespace: development
            revision: develop
          - cluster: staging
            namespace: staging
            revision: main
          - cluster: prod
            namespace: production
            revision: main
  template:
    metadata:
      name: 'myapp-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/myapp-manifests.git
        targetRevision: '{{revision}}'
        path: 'overlays/{{cluster}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

## ArgoCD with Helm

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-helm
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://charts.example.com
    chart: myapp
    targetRevision: 1.2.0
    helm:
      releaseName: myapp
      valueFiles:
        - values-production.yaml
      values: |
        replicaCount: 5
        image:
          tag: v2.0.0
      parameters:
        - name: service.type
          value: LoadBalancer
  destination:
    server: https://kubernetes.default.svc
    namespace: production
```

## ArgoCD Project

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production applications
  sourceRepos:
    - 'https://github.com/myorg/*'
    - 'https://charts.example.com'
  destinations:
    - namespace: production
      server: https://kubernetes.default.svc
    - namespace: production-*
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota
    - group: ''
      kind: LimitRange
  roles:
    - name: developer
      description: Developer access
      policies:
        - p, proj:production:developer, applications, get, production/*, allow
        - p, proj:production:developer, applications, sync, production/*, allow
      groups:
        - developers
```

## Flux Installation

```bash
# Install Flux CLI
brew install fluxcd/tap/flux

# Check prerequisites
flux check --pre

# Bootstrap Flux (GitHub)
flux bootstrap github \
  --owner=myorg \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production \
  --personal

# Bootstrap Flux (GitLab)
flux bootstrap gitlab \
  --owner=myorg \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production
```

## Flux GitRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/myorg/myapp-manifests
  ref:
    branch: main
  secretRef:
    name: github-credentials
  ignore: |
    # Exclude files
    .git/
    *.md
```

## Flux Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 10m
  targetNamespace: production
  sourceRef:
    kind: GitRepository
    name: myapp
  path: ./overlays/production
  prune: true
  timeout: 2m
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: myapp
      namespace: production
  postBuild:
    substitute:
      environment: production
      replicas: "5"
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

## Flux HelmRepository

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: bitnami
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.bitnami.com/bitnami
---
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: redis
  namespace: production
spec:
  interval: 5m
  chart:
    spec:
      chart: redis
      version: '17.x'
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
  values:
    architecture: standalone
    auth:
      enabled: true
      existingSecret: redis-credentials
    master:
      persistence:
        size: 10Gi
```

## Flux ImageUpdateAutomation

```yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageRepository
metadata:
  name: myapp
  namespace: flux-system
spec:
  image: myregistry.io/myapp
  interval: 1m
  secretRef:
    name: registry-credentials
---
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImagePolicy
metadata:
  name: myapp
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: myapp
  policy:
    semver:
      range: '>=1.0.0'
---
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: myapp
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: fluxcdbot@users.noreply.github.com
        name: fluxcdbot
      messageTemplate: 'Update image to {{.NewTag}}'
    push:
      branch: main
  update:
    path: ./overlays/production
    strategy: Setters
```

## Progressive Delivery with Flagger

```yaml
# Install Flagger
kubectl apply -k github.com/fluxcd/flagger/kustomize/istio

---
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8080
    gateways:
      - myapp-gateway
    hosts:
      - myapp.example.com
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 1m
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.test/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 -c 2 http://myapp-canary.production:80/"
```

## Sealed Secrets

```bash
# Install controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Install kubeseal CLI
brew install kubeseal

# Create sealed secret
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=secret123 \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > sealed-db-credentials.yaml

# Apply sealed secret
kubectl apply -f sealed-db-credentials.yaml
```

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  encryptedData:
    username: AgBy8h...encrypted...
    password: AgCtr2...encrypted...
  template:
    type: Opaque
    metadata:
      labels:
        app: myapp
```

## SOPS with Age

```bash
# Install SOPS
brew install sops

# Generate age key
age-keygen -o age.agekey

# Create SOPS config
cat > .sops.yaml << EOF
creation_rules:
  - path_regex: .*\.enc\.yaml$
    encrypted_regex: ^(data|stringData)$
    age: age1...publickey...
EOF

# Encrypt secret
sops --encrypt --in-place secrets.enc.yaml

# Configure Flux decryption
kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey
```

```yaml
# Flux Kustomization with SOPS
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp
  namespace: flux-system
spec:
  decryption:
    provider: sops
    secretRef:
      name: sops-age
  # ... rest of spec
```

## Repository Strategies

### Mono-repo
```
fleet-repo/
├── apps/
│   ├── myapp/
│   │   ├── base/
│   │   └── overlays/
│   └── another-app/
├── infrastructure/
│   ├── cert-manager/
│   └── ingress-nginx/
└── clusters/
    ├── dev/
    ├── staging/
    └── production/
```

### Multi-repo
```
# App repos (one per app)
myapp-manifests/
├── base/
└── overlays/

# Infrastructure repo
infrastructure/
├── cert-manager/
└── ingress-nginx/

# Fleet repo (references others)
fleet-infra/
├── apps.yaml      # Points to app repos
└── infra.yaml     # Points to infra repo
```

## ArgoCD vs Flux Comparison

| Feature | ArgoCD | Flux |
|---------|--------|------|
| UI | Built-in web UI | Third-party (Weave GitOps) |
| Multi-tenancy | AppProject | Namespaced resources |
| Helm | Native support | HelmController |
| Image automation | ArgoCD Image Updater | Native ImagePolicy |
| Notifications | ArgoCD Notifications | Alerts/Receivers |
| RBAC | Built-in | Kubernetes RBAC |
| Architecture | Centralized | Distributed |

## Best Practices

1. **Use separate repos** for app code and manifests
2. **Protect main branch** with required reviews
3. **Use sealed secrets or SOPS** for sensitive data
4. **Enable auto-sync with prune** for drift correction
5. **Set up notifications** for sync failures
6. **Use ApplicationSets/Kustomizations** for multi-environment
7. **Implement progressive delivery** for safe rollouts
8. **Version your Helm charts** semantically
9. **Keep manifests DRY** with Kustomize overlays
10. **Monitor reconciliation metrics** and alerts
