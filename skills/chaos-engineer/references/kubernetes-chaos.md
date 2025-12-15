# Kubernetes Chaos Engineering

> Reference for: Chaos Engineer
> Load when: K8s chaos, Litmus experiments, pod failures, node chaos

## Litmus Chaos - ChaosEngine

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: nginx-chaos
  namespace: default
spec:
  # Application information
  appinfo:
    appns: 'default'
    applabel: 'app=nginx'
    appkind: 'deployment'

  # Chaos service account
  chaosServiceAccount: litmus-admin

  # Experiments to run
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            # Total chaos duration
            - name: TOTAL_CHAOS_DURATION
              value: '60'

            # Chaos interval (delete pod every X seconds)
            - name: CHAOS_INTERVAL
              value: '10'

            # Force delete pods
            - name: FORCE
              value: 'true'

            # Number of pods to delete
            - name: PODS_AFFECTED_PERC
              value: '50'

    - name: pod-network-latency
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: '60'
            - name: NETWORK_LATENCY
              value: '2000'  # 2 second latency
            - name: JITTER
              value: '200'   # 200ms jitter
            - name: CONTAINER_RUNTIME
              value: 'containerd'

    - name: pod-cpu-hog
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: '60'
            - name: CPU_CORES
              value: '2'
            - name: PODS_AFFECTED_PERC
              value: '50'

  # Monitor application during chaos
  monitoring: true

  # Job cleanup policy
  jobCleanUpPolicy: 'delete'
```

## Chaos Mesh Experiments

```yaml
# Network partition between services
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: partition-frontend-backend
  namespace: chaos-testing
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      'app': 'frontend'
  direction: to
  target:
    mode: all
    selector:
      namespaces:
        - production
      labelSelectors:
        'app': 'backend'
  duration: '5m'

---
# Pod failure - kill random pods
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure
  namespace: chaos-testing
spec:
  action: pod-failure
  mode: one  # one, all, fixed, fixed-percent, random-max-percent
  duration: '30s'
  selector:
    namespaces:
      - production
    labelSelectors:
      'app': 'payment-service'
  scheduler:
    cron: '@every 10m'  # Run every 10 minutes

---
# Network bandwidth limitation
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: bandwidth-limit
spec:
  action: bandwidth
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      'tier': 'backend'
  bandwidth:
    rate: '1mbps'
    limit: 20000
    buffer: 10000
  duration: '5m'

---
# Disk I/O stress
apiVersion: chaos-mesh.org/v1alpha1
kind: IOChaos
metadata:
  name: io-latency
spec:
  action: latency
  mode: one
  selector:
    namespaces:
      - production
    labelSelectors:
      'app': 'database'
  volumePath: /var/lib/postgresql/data
  path: /var/lib/postgresql/data/**/*
  delay: '100ms'
  percent: 50  # 50% of I/O operations affected
  duration: '5m'

---
# DNS chaos - random DNS errors
apiVersion: chaos-mesh.org/v1alpha1
kind: DNSChaos
metadata:
  name: dns-random-error
spec:
  action: random
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      'app': 'api-gateway'
  patterns:
    - external-api.example.com
    - *.third-party-service.com
  duration: '3m'
```

## Node Drain Simulation

```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time

class K8sNodeChaos:
    def __init__(self):
        config.load_kube_config()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def cordon_node(self, node_name: str):
        """Mark node as unschedulable."""
        body = {
            "spec": {
                "unschedulable": True
            }
        }
        try:
            self.core_v1.patch_node(node_name, body)
            print(f"Node {node_name} cordoned")
        except ApiException as e:
            print(f"Failed to cordon node: {e}")

    def drain_node(
        self,
        node_name: str,
        grace_period_seconds: int = 30,
        delete_local_data: bool = True
    ):
        """
        Drain node by evicting all pods.
        Simulates node failure or maintenance.
        """
        # First, cordon the node
        self.cordon_node(node_name)

        # Get all pods on the node
        field_selector = f"spec.nodeName={node_name}"
        pods = self.core_v1.list_pod_for_all_namespaces(
            field_selector=field_selector
        )

        # Evict each pod
        for pod in pods.items:
            # Skip DaemonSet pods and mirror pods
            if pod.metadata.owner_references:
                for owner in pod.metadata.owner_references:
                    if owner.kind in ['DaemonSet', 'Node']:
                        continue

            # Create eviction
            eviction = client.V1Eviction(
                metadata=client.V1ObjectMeta(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace
                ),
                delete_options=client.V1DeleteOptions(
                    grace_period_seconds=grace_period_seconds
                )
            )

            try:
                self.core_v1.create_namespaced_pod_eviction(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    body=eviction
                )
                print(f"Evicted pod {pod.metadata.name}")
            except ApiException as e:
                if e.status == 429:  # Too many requests
                    print(f"Pod {pod.metadata.name} protected by PDB")
                else:
                    print(f"Failed to evict {pod.metadata.name}: {e}")

        return {"node": node_name, "status": "drained"}

    def uncordon_node(self, node_name: str):
        """Mark node as schedulable again."""
        body = {
            "spec": {
                "unschedulable": False
            }
        }
        self.core_v1.patch_node(node_name, body)
        print(f"Node {node_name} uncordoned")

    def simulate_node_failure(
        self,
        node_name: str,
        duration_seconds: int = 300
    ):
        """
        Simulate complete node failure.
        Drain node, wait, then restore.
        """
        print(f"Simulating failure of node {node_name}")

        # Drain the node
        self.drain_node(node_name)

        # Wait for duration
        print(f"Node failed for {duration_seconds} seconds")
        time.sleep(duration_seconds)

        # Restore node
        self.uncordon_node(node_name)
        print("Node restored")
```

## Pod Autoscaling Chaos

```yaml
# Test HPA behavior under load
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: stress-hpa-trigger
spec:
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      'app': 'web-server'
  stressors:
    cpu:
      workers: 2
      load: 80  # 80% CPU load
  duration: '10m'

---
# Verify HPA scaling response
apiVersion: v1
kind: Pod
metadata:
  name: chaos-verification
spec:
  containers:
  - name: verifier
    image: bitnami/kubectl:latest
    command:
      - /bin/bash
      - -c
      - |
        # Monitor HPA scaling
        while true; do
          echo "=== HPA Status ==="
          kubectl get hpa web-server -o json | \
            jq '.status | {current: .currentReplicas, desired: .desiredReplicas, cpu: .currentCPUUtilizationPercentage}'

          echo "=== Pod Count ==="
          kubectl get pods -l app=web-server --no-headers | wc -l

          sleep 10
        done
```

## Custom Resource Chaos

```python
# Python script to test custom CRD resilience
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import random
import time

def chaos_delete_custom_resources(
    group: str,
    version: str,
    plural: str,
    namespace: str,
    percentage: int = 30
):
    """
    Randomly delete custom resources to test operator resilience.

    Args:
        group: API group (e.g., 'app.example.com')
        version: API version (e.g., 'v1')
        plural: Resource plural name (e.g., 'myapps')
        namespace: Namespace to target
        percentage: Percentage of resources to delete (0-100)
    """
    config.load_kube_config()
    custom_api = client.CustomObjectsApi()

    try:
        # List all custom resources
        resources = custom_api.list_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural
        )

        items = resources.get('items', [])
        if not items:
            print("No resources found")
            return

        # Calculate number to delete
        count_to_delete = max(1, int(len(items) * percentage / 100))

        # Randomly select resources
        to_delete = random.sample(items, count_to_delete)

        print(f"Deleting {count_to_delete} of {len(items)} {plural}")

        # Delete selected resources
        for resource in to_delete:
            name = resource['metadata']['name']
            try:
                custom_api.delete_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    name=name,
                    body=client.V1DeleteOptions()
                )
                print(f"Deleted {plural}/{name}")
                time.sleep(1)  # Rate limit deletions
            except ApiException as e:
                print(f"Failed to delete {name}: {e}")

    except ApiException as e:
        print(f"Error listing resources: {e}")

# Example: Delete 30% of MyApp custom resources
chaos_delete_custom_resources(
    group='app.example.com',
    version='v1',
    plural='myapps',
    namespace='production',
    percentage=30
)
```

## Quick Reference

| Chaos Type | Tool | YAML/Command |
|------------|------|--------------|
| Pod delete | Litmus | `pod-delete` experiment |
| Network latency | Chaos Mesh | `NetworkChaos` with action: delay |
| Node drain | kubectl/API | `kubectl drain <node>` |
| CPU stress | Chaos Mesh | `StressChaos` with cpu stressor |
| DNS failure | Chaos Mesh | `DNSChaos` random/error action |
| I/O latency | Chaos Mesh | `IOChaos` with latency action |
| Network partition | Chaos Mesh | `NetworkChaos` partition |
| Pod failure | Chaos Mesh | `PodChaos` pod-failure |
