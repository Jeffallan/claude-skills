# Multi-Cluster Management

> Reference for: Kubernetes Specialist
> Load when: multi-cluster, federation, Cluster API, cross-cluster networking, disaster recovery, cluster management

---

## Cluster API

### Installation

```bash
# Install clusterctl CLI
curl -L https://github.com/kubernetes-sigs/cluster-api/releases/download/v1.6.0/clusterctl-linux-amd64 -o clusterctl
chmod +x clusterctl && sudo mv clusterctl /usr/local/bin/

# Initialize management cluster with AWS provider
clusterctl init --infrastructure aws

# Initialize with multiple providers
clusterctl init \
  --infrastructure aws,azure \
  --control-plane kubeadm \
  --bootstrap kubeadm
```

### Cluster Definition

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: production-cluster
  namespace: clusters
spec:
  clusterNetwork:
    pods:
      cidrBlocks: ["192.168.0.0/16"]
    services:
      cidrBlocks: ["10.96.0.0/12"]
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: production-control-plane
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
    kind: AWSCluster
    name: production-cluster
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
kind: AWSCluster
metadata:
  name: production-cluster
  namespace: clusters
spec:
  region: us-west-2
  sshKeyName: production-key
  network:
    vpc:
      cidrBlock: 10.0.0.0/16
    subnets:
      - availabilityZone: us-west-2a
        cidrBlock: 10.0.1.0/24
        isPublic: true
      - availabilityZone: us-west-2b
        cidrBlock: 10.0.2.0/24
        isPublic: true
```

### Control Plane

```yaml
apiVersion: controlplane.cluster.x-k8s.io/v1beta1
kind: KubeadmControlPlane
metadata:
  name: production-control-plane
  namespace: clusters
spec:
  replicas: 3
  version: v1.28.0
  machineTemplate:
    infrastructureRef:
      apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
      kind: AWSMachineTemplate
      name: production-control-plane
  kubeadmConfigSpec:
    clusterConfiguration:
      apiServer:
        extraArgs:
          cloud-provider: aws
      controllerManager:
        extraArgs:
          cloud-provider: aws
    initConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          cloud-provider: aws
    joinConfiguration:
      nodeRegistration:
        kubeletExtraArgs:
          cloud-provider: aws
```

### Machine Deployment (Worker Nodes)

```yaml
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: production-workers
  namespace: clusters
spec:
  clusterName: production-cluster
  replicas: 5
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: production-cluster
  template:
    spec:
      clusterName: production-cluster
      version: v1.28.0
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: production-workers
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
        kind: AWSMachineTemplate
        name: production-workers
---
apiVersion: infrastructure.cluster.x-k8s.io/v1beta2
kind: AWSMachineTemplate
metadata:
  name: production-workers
  namespace: clusters
spec:
  template:
    spec:
      instanceType: m5.xlarge
      iamInstanceProfile: nodes.cluster-api-provider-aws.sigs.k8s.io
      sshKeyName: production-key
      rootVolume:
        size: 100
        type: gp3
```

## Cross-Cluster Networking

### Submariner Installation

```bash
# Install subctl
curl -Ls https://get.submariner.io | bash

# Join clusters to broker
subctl deploy-broker --kubeconfig kubeconfig-cluster1

# Join workload clusters
subctl join --kubeconfig kubeconfig-cluster1 broker-info.subm --clusterid cluster1
subctl join --kubeconfig kubeconfig-cluster2 broker-info.subm --clusterid cluster2

# Verify connectivity
subctl show all
```

### ServiceExport/ServiceImport

```yaml
# Export service from cluster1
apiVersion: multicluster.x-k8s.io/v1alpha1
kind: ServiceExport
metadata:
  name: myapp
  namespace: production
---
# Service is auto-imported to other clusters as:
# myapp.production.svc.clusterset.local
```

### Cilium Cluster Mesh

```bash
# Enable cluster mesh on both clusters
cilium clustermesh enable --context cluster1
cilium clustermesh enable --context cluster2

# Connect clusters
cilium clustermesh connect --context cluster1 --destination-context cluster2

# Verify
cilium clustermesh status --context cluster1
```

```yaml
# Global service accessible from all clusters
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: production
  annotations:
    service.cilium.io/global: "true"
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - port: 80
```

## Multi-Cluster DNS

### ExternalDNS with Route53

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  template:
    spec:
      containers:
        - name: external-dns
          image: k8s.gcr.io/external-dns/external-dns:v0.14.0
          args:
            - --source=service
            - --source=ingress
            - --provider=aws
            - --aws-zone-type=public
            - --registry=txt
            - --txt-owner-id=my-cluster
            - --domain-filter=example.com
```

### CoreDNS Federation

```yaml
# Forward queries for other clusters
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
        }
        # Forward to cluster2 DNS
        cluster2.local:53 {
            forward . 10.0.0.10
        }
        forward . /etc/resolv.conf
        cache 30
        loop
        reload
        loadbalance
    }
```

## Workload Distribution

### Kubernetes Federation v2

```yaml
apiVersion: types.kubefed.io/v1beta1
kind: FederatedDeployment
metadata:
  name: myapp
  namespace: production
spec:
  template:
    metadata:
      labels:
        app: myapp
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: myapp
      template:
        metadata:
          labels:
            app: myapp
        spec:
          containers:
            - name: myapp
              image: myregistry.io/myapp:v1.0.0
  placement:
    clusters:
      - name: cluster-us-west
      - name: cluster-us-east
      - name: cluster-eu-west
  overrides:
    - clusterName: cluster-us-west
      clusterOverrides:
        - path: "/spec/replicas"
          value: 5
    - clusterName: cluster-eu-west
      clusterOverrides:
        - path: "/spec/replicas"
          value: 3
```

### ArgoCD Multi-Cluster

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-global
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            environment: production
  template:
    metadata:
      name: 'myapp-{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/myapp-manifests.git
        targetRevision: main
        path: overlays/production
      destination:
        server: '{{server}}'
        namespace: production
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

## Disaster Recovery

### Velero Backup Configuration

```bash
# Install Velero with S3
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups \
  --backup-location-config region=us-west-2 \
  --snapshot-location-config region=us-west-2 \
  --secret-file ./credentials-velero
```

```yaml
# Scheduled backup
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
      - production
      - staging
    excludedResources:
      - events
    storageLocation: default
    volumeSnapshotLocations:
      - default
    ttl: 720h  # 30 days
---
# Restore to different cluster
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: restore-production
  namespace: velero
spec:
  backupName: daily-backup-20240115
  includedNamespaces:
    - production
  restorePVs: true
  preserveNodePorts: true
```

### Active-Passive Failover

```yaml
# Primary cluster ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
    external-dns.alpha.kubernetes.io/set-identifier: primary
    external-dns.alpha.kubernetes.io/aws-weight: "100"
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
---
# Secondary cluster ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.example.com
    external-dns.alpha.kubernetes.io/set-identifier: secondary
    external-dns.alpha.kubernetes.io/aws-weight: "0"
spec:
  rules:
    - host: myapp.example.com
      # ... same backend config
```

## Centralized Management Tools

### Rancher Setup

```bash
# Install Rancher with Helm
helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
helm install rancher rancher-stable/rancher \
  --namespace cattle-system \
  --create-namespace \
  --set hostname=rancher.example.com \
  --set bootstrapPassword=admin
```

### Kubeconfig Management

```yaml
# Merge multiple kubeconfigs
# ~/.kube/config
apiVersion: v1
kind: Config
clusters:
  - name: cluster-us-west
    cluster:
      server: https://cluster-us-west.example.com
      certificate-authority-data: ...
  - name: cluster-us-east
    cluster:
      server: https://cluster-us-east.example.com
      certificate-authority-data: ...
contexts:
  - name: us-west
    context:
      cluster: cluster-us-west
      user: admin-us-west
      namespace: default
  - name: us-east
    context:
      cluster: cluster-us-east
      user: admin-us-east
      namespace: default
users:
  - name: admin-us-west
    user:
      token: ...
  - name: admin-us-east
    user:
      token: ...
current-context: us-west
```

```bash
# Switch between clusters
kubectl config use-context us-west
kubectl config use-context us-east

# Run command against specific cluster
kubectl --context=us-west get pods
kubectl --context=us-east get pods

# Use kubectx for easier switching
kubectx us-west
```

## Best Practices

1. **Use Cluster API** for declarative cluster lifecycle management
2. **Implement service mesh** for secure cross-cluster communication
3. **Set up DNS-based routing** for global service discovery
4. **Configure automated backups** with Velero across clusters
5. **Use GitOps** (ArgoCD/Flux) for consistent multi-cluster deployments
6. **Implement network policies** consistently across clusters
7. **Centralize observability** with cross-cluster metrics and logs
8. **Test failover procedures** regularly
9. **Use namespaces consistently** across clusters
10. **Document cluster topology** and dependencies
11. **Implement RBAC** with cross-cluster access patterns
12. **Monitor cluster health** from centralized dashboard
