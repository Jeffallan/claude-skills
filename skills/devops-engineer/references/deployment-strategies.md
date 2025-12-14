# Deployment Strategies

> Reference for: DevOps Engineer
> Load when: Deployment strategy, rollback, blue-green, canary releases

## Strategy Comparison

| Strategy | Use When | Rollback | Risk |
|----------|----------|----------|------|
| **Rolling** | Standard updates, can tolerate mixed versions | Automatic via health checks | Low |
| **Blue-Green** | Zero downtime, instant rollback needed | Switch traffic to old env | Medium |
| **Canary** | Risk mitigation, gradual rollout | Scale down canary | Low |
| **Recreate** | Stateful apps, breaking changes | Redeploy previous version | High |

## Rolling Deployment (Kubernetes)

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max pods above desired
      maxUnavailable: 25%  # Max pods unavailable
```

## Blue-Green with Ingress

```yaml
# Blue deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    version: blue
---
# Green deployment (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    version: green
---
# Service pointing to active version
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    version: blue  # Switch to 'green' for cutover
```

## Canary with Istio

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app
spec:
  hosts:
    - app
  http:
    - match:
        - headers:
            canary:
              exact: "true"
      route:
        - destination:
            host: app-canary
    - route:
        - destination:
            host: app-stable
          weight: 90
        - destination:
            host: app-canary
          weight: 10
```

## Rollback Procedures

### Kubernetes Rollback
```bash
# View rollout history
kubectl rollout history deployment/app

# Rollback to previous
kubectl rollout undo deployment/app

# Rollback to specific revision
kubectl rollout undo deployment/app --to-revision=2

# Check status
kubectl rollout status deployment/app
```

### ArgoCD Rollback
```bash
argocd app rollback app-prod --revision=123
```

### Terraform Rollback
```bash
# Identify previous state
terraform state list

# Import previous configuration
git checkout HEAD~1 -- main.tf
terraform apply
```

## Pre-deployment Checklist

- [ ] Database migrations are backward compatible
- [ ] Feature flags for new functionality
- [ ] Monitoring dashboards updated
- [ ] Alert thresholds reviewed
- [ ] Rollback procedure documented
- [ ] Staging tested and approved
- [ ] Team notified of deployment window

## Post-deployment Verification

```bash
# Check pod status
kubectl get pods -l app=app

# Check logs for errors
kubectl logs -l app=app --tail=100 | grep -i error

# Verify endpoints
curl -f https://app.example.com/health

# Check metrics
# - Error rate < 1%
# - Latency p99 < 500ms
# - No memory/CPU spikes
```
