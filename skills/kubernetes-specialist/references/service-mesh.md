# Service Mesh

> Reference for: Kubernetes Specialist
> Load when: Istio, Linkerd, service mesh, traffic management, mTLS, sidecar proxy, canary deployment, traffic mirroring

---

## Istio Installation

```bash
# Install Istio CLI
curl -L https://istio.io/downloadIstio | sh -
export PATH=$PWD/istio-*/bin:$PATH

# Install Istio with default profile
istioctl install --set profile=default -y

# Enable sidecar injection for namespace
kubectl label namespace production istio-injection=enabled

# Verify installation
istioctl verify-install
kubectl get pods -n istio-system
```

## Istio Profiles

```bash
# Minimal - only control plane
istioctl install --set profile=minimal

# Default - control plane + ingress gateway
istioctl install --set profile=default

# Demo - includes egress gateway, extra features
istioctl install --set profile=demo

# Production - tuned for production
istioctl install --set profile=default \
  --set values.global.proxy.resources.requests.cpu=100m \
  --set values.global.proxy.resources.requests.memory=128Mi \
  --set values.global.proxy.resources.limits.cpu=500m \
  --set values.global.proxy.resources.limits.memory=256Mi
```

## VirtualService

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp
  namespace: production
spec:
  hosts:
    - myapp
    - myapp.example.com
  gateways:
    - mesh                    # Internal mesh traffic
    - myapp-gateway           # External gateway
  http:
    # Route based on headers
    - match:
        - headers:
            x-version:
              exact: "v2"
      route:
        - destination:
            host: myapp
            subset: v2

    # Canary release (90/10 split)
    - match:
        - uri:
            prefix: /api
      route:
        - destination:
            host: myapp
            subset: v1
          weight: 90
        - destination:
            host: myapp
            subset: v2
          weight: 10

    # Default route
    - route:
        - destination:
            host: myapp
            subset: v1
      timeout: 30s
      retries:
        attempts: 3
        perTryTimeout: 10s
        retryOn: connect-failure,refused-stream,503
```

## DestinationRule

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp
  namespace: production
spec:
  host: myapp
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 5s
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 100
    loadBalancer:
      simple: LEAST_REQUEST
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
      trafficPolicy:
        loadBalancer:
          simple: ROUND_ROBIN
    - name: v2
      labels:
        version: v2
```

## Gateway

```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: myapp-gateway
  namespace: production
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - myapp.example.com
      tls:
        httpsRedirect: true
    - port:
        number: 443
        name: https
        protocol: HTTPS
      hosts:
        - myapp.example.com
      tls:
        mode: SIMPLE
        credentialName: myapp-tls-secret
```

## Traffic Mirroring (Shadow Traffic)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-mirror
  namespace: production
spec:
  hosts:
    - myapp
  http:
    - route:
        - destination:
            host: myapp
            subset: v1
      mirror:
        host: myapp
        subset: v2
      mirrorPercentage:
        value: 100.0
```

## mTLS Configuration

```yaml
# Strict mTLS for namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
---
# Per-workload mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: legacy-service
  namespace: production
spec:
  selector:
    matchLabels:
      app: legacy-service
  mtls:
    mode: PERMISSIVE  # Allow both mTLS and plaintext
---
# Mesh-wide mTLS policy
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
```

## Authorization Policy

```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: myapp-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: myapp
  action: ALLOW
  rules:
    # Allow from specific service accounts
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend"
              - "cluster.local/ns/production/sa/api-gateway"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/*"]

    # Allow health checks from anywhere
    - to:
        - operation:
            methods: ["GET"]
            paths: ["/health", "/ready"]

    # Deny all other traffic (implicit deny when rules exist)
```

## Circuit Breaker

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp-circuit-breaker
  namespace: production
spec:
  host: myapp
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 50
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 100
      minHealthPercent: 0
```

## Fault Injection (Testing)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-fault
  namespace: production
spec:
  hosts:
    - myapp
  http:
    - match:
        - headers:
            x-test-fault:
              exact: "inject"
      fault:
        delay:
          percentage:
            value: 50
          fixedDelay: 5s
        abort:
          percentage:
            value: 10
          httpStatus: 503
      route:
        - destination:
            host: myapp
    - route:
        - destination:
            host: myapp
```

## Linkerd Installation

```bash
# Install Linkerd CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh
export PATH=$HOME/.linkerd2/bin:$PATH

# Validate cluster
linkerd check --pre

# Install CRDs
linkerd install --crds | kubectl apply -f -

# Install control plane
linkerd install | kubectl apply -f -

# Check installation
linkerd check

# Enable injection for namespace
kubectl annotate namespace production linkerd.io/inject=enabled

# Inject existing deployments
kubectl get deploy -n production -o yaml | linkerd inject - | kubectl apply -f -
```

## Linkerd Service Profile

```yaml
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: myapp.production.svc.cluster.local
  namespace: production
spec:
  routes:
    - name: GET /api/users
      condition:
        method: GET
        pathRegex: /api/users
      responseClasses:
        - condition:
            status:
              min: 500
              max: 599
          isFailure: true
      timeout: 5s

    - name: POST /api/orders
      condition:
        method: POST
        pathRegex: /api/orders
      isRetryable: true
      timeout: 10s

  retryBudget:
    retryRatio: 0.2
    minRetriesPerSecond: 10
    ttl: 10s
```

## Linkerd Traffic Split (Canary)

```yaml
apiVersion: split.smi-spec.io/v1alpha1
kind: TrafficSplit
metadata:
  name: myapp-canary
  namespace: production
spec:
  service: myapp
  backends:
    - service: myapp-v1
      weight: 900m    # 90%
    - service: myapp-v2
      weight: 100m    # 10%
```

## Multi-Cluster Mesh (Istio)

```yaml
# Primary cluster - create remote secret
istioctl x create-remote-secret \
  --context=cluster1 \
  --name=cluster1 | kubectl apply -f - --context=cluster2

# Enable endpoint discovery
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster1
      network: network1
```

## Kiali Dashboard

```bash
# Install Kiali
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/kiali.yaml

# Access dashboard
istioctl dashboard kiali
```

## Jaeger Tracing

```bash
# Install Jaeger
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.20/samples/addons/jaeger.yaml

# Access dashboard
istioctl dashboard jaeger
```

## Service Mesh Comparison

| Feature | Istio | Linkerd |
|---------|-------|---------|
| Sidecar | Envoy | linkerd2-proxy (Rust) |
| Resource usage | Higher | Lower |
| Features | More extensive | Focused/simpler |
| mTLS | Built-in | Built-in |
| Traffic management | Advanced | Basic (SMI) |
| Multi-cluster | Native support | Requires setup |
| Learning curve | Steeper | Gentler |

## Best Practices

1. **Start with permissive mTLS**, migrate to strict gradually
2. **Use circuit breakers** to prevent cascade failures
3. **Set reasonable timeouts** and retry budgets
4. **Enable distributed tracing** for observability
5. **Test with fault injection** before production
6. **Monitor sidecar resource usage** and tune accordingly
7. **Use traffic mirroring** to validate new versions safely
8. **Implement authorization policies** for zero-trust
9. **Keep service mesh version updated** for security patches
10. **Document traffic routing decisions** in VirtualServices
