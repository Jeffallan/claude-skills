# Cost Optimization

> Reference for: Kubernetes Specialist
> Load when: cost optimization, resource right-sizing, VPA, spot instances, autoscaling tuning, quotas, resource management

---

## Resource Right-Sizing

### Analyze Current Usage

```bash
# View resource requests vs actual usage
kubectl top pods -n production

# Detailed resource metrics (requires metrics-server)
kubectl get pods -n production -o custom-columns=\
"NAME:.metadata.name,\
CPU_REQ:.spec.containers[*].resources.requests.cpu,\
CPU_LIM:.spec.containers[*].resources.limits.cpu,\
MEM_REQ:.spec.containers[*].resources.requests.memory,\
MEM_LIM:.spec.containers[*].resources.limits.memory"

# Get VPA recommendations (if VPA installed)
kubectl get vpa -n production -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{.status.recommendation.containerRecommendations[*]}{"\n\n"}{end}'
```

### Right-Sized Resource Spec

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
spec:
  template:
    spec:
      containers:
        - name: myapp
          resources:
            requests:
              # Set to average usage + 10-20% buffer
              cpu: 100m
              memory: 128Mi
            limits:
              # CPU: 2-4x requests for burst capacity
              # Memory: 1.5-2x requests (OOM prevention)
              cpu: 500m
              memory: 256Mi
```

## Vertical Pod Autoscaler (VPA)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    # Off - only provide recommendations
    # Initial - apply only on pod creation
    # Auto - apply on pod creation and during runtime (with restart)
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
      - containerName: myapp
        minAllowed:
          cpu: 50m
          memory: 64Mi
        maxAllowed:
          cpu: 2000m
          memory: 2Gi
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsAndLimits
```

### VPA Recommendation Only

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa-recommender
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Off"
```

## Horizontal Pod Autoscaler (HPA) Tuning

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 20
  metrics:
    # CPU-based scaling
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory-based scaling
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metrics (e.g., requests per second)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: 100

  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 2
          periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

## Spot/Preemptible Instances

### Node Pool with Spot Instances (GKE)

```yaml
apiVersion: container.google.com/v1
kind: NodePool
metadata:
  name: spot-pool
spec:
  config:
    machineType: e2-standard-4
    preemptible: true
    taints:
      - key: cloud.google.com/gke-spot
        value: "true"
        effect: NoSchedule
  autoscaling:
    enabled: true
    minNodeCount: 0
    maxNodeCount: 10
```

### Workload Tolerating Spot Nodes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-processor
  namespace: production
spec:
  template:
    spec:
      tolerations:
        - key: cloud.google.com/gke-spot
          operator: Equal
          value: "true"
          effect: NoSchedule
        - key: kubernetes.azure.com/scalesetpriority
          operator: Equal
          value: spot
          effect: NoSchedule
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              preference:
                matchExpressions:
                  - key: cloud.google.com/gke-spot
                    operator: In
                    values: ["true"]
      containers:
        - name: processor
          # ... container spec
```

### Pod Disruption Budget for Spot

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
  namespace: production
spec:
  minAvailable: 2
  # OR maxUnavailable: 1
  selector:
    matchLabels:
      app: myapp
```

## Namespace Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
    requests.storage: 500Gi
    pods: "50"
    services: "20"
    secrets: "50"
    configmaps: "50"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-object-counts
  namespace: production
spec:
  hard:
    count/deployments.apps: "20"
    count/statefulsets.apps: "5"
    count/jobs.batch: "10"
```

## LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
    # Default limits for containers
    - type: Container
      default:
        cpu: 500m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      min:
        cpu: 50m
        memory: 64Mi
      max:
        cpu: 4000m
        memory: 8Gi

    # Pod-level limits
    - type: Pod
      max:
        cpu: 8000m
        memory: 16Gi

    # PVC limits
    - type: PersistentVolumeClaim
      min:
        storage: 1Gi
      max:
        storage: 100Gi
```

## Cluster Autoscaler Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-config
  namespace: kube-system
data:
  config: |
    {
      "scaleDownDelayAfterAdd": "10m",
      "scaleDownDelayAfterDelete": "0s",
      "scaleDownDelayAfterFailure": "3m",
      "scaleDownUnneededTime": "10m",
      "scaleDownUnreadyTime": "20m",
      "scaleDownUtilizationThreshold": "0.5",
      "skipNodesWithLocalStorage": "false",
      "skipNodesWithSystemPods": "true",
      "balanceSimilarNodeGroups": "true",
      "expander": "least-waste"
    }
```

## Cost Monitoring

### Kubecost Deployment

```bash
# Install Kubecost
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace \
  --set kubecostToken="YOUR_TOKEN"
```

### Prometheus Cost Metrics

```yaml
# Pod cost label for attribution
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    cost-center: engineering
    team: platform
    environment: production
spec:
  template:
    metadata:
      labels:
        cost-center: engineering
        team: platform
```

## Scheduled Scaling

```yaml
# Scale down dev environments overnight
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-dev
  namespace: development
spec:
  schedule: "0 20 * * 1-5"  # 8 PM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler
          containers:
            - name: kubectl
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  kubectl scale deployment --all --replicas=0 -n development
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-dev
  namespace: development
spec:
  schedule: "0 8 * * 1-5"  # 8 AM Mon-Fri
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler
          containers:
            - name: kubectl
              image: bitnami/kubectl:latest
              command:
                - /bin/sh
                - -c
                - |
                  kubectl scale deployment frontend --replicas=2 -n development
                  kubectl scale deployment backend --replicas=2 -n development
          restartPolicy: OnFailure
```

## Priority Classes

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "Critical production workloads"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
preemptionPolicy: Never
description: "Batch jobs that can be preempted"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-job
spec:
  template:
    spec:
      priorityClassName: low-priority
      # ...
```

## Best Practices

1. **Set resource requests** on all containers (enables efficient scheduling)
2. **Use VPA recommendations** to right-size workloads
3. **Tune HPA stabilization** to prevent thrashing
4. **Leverage spot instances** for fault-tolerant workloads
5. **Implement PDBs** to maintain availability during disruptions
6. **Set namespace quotas** to prevent resource hogging
7. **Use LimitRanges** to enforce sensible defaults
8. **Label resources** for cost attribution
9. **Schedule dev environments** to scale down off-hours
10. **Monitor with Kubecost** or cloud cost tools
11. **Use priority classes** to ensure critical workloads run
12. **Review unused resources** regularly (idle deployments, orphaned PVCs)
