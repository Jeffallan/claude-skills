# Kubernetes Storage

> Reference for: Kubernetes Specialist
> Load when: PV, PVC, StorageClasses, CSI drivers

## StorageClass Definitions

### AWS EBS (gp3)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/..."
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### GCE Persistent Disk (SSD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd-gce
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### Azure Disk (Premium SSD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd-azure
provisioner: disk.csi.azure.com
parameters:
  storageaccounttype: Premium_LRS
  kind: Managed
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

### NFS Storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-storage
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports/kubernetes
volumeBindingMode: Immediate
reclaimPolicy: Retain
```

## PersistentVolume (Static Provisioning)

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: legacy-database-pv
  labels:
    type: local
    app: legacy-db
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /mnt/data/legacy-db
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node-01
```

## PersistentVolumeClaim Patterns

### Basic PVC (Dynamic Provisioning)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
  namespace: production
  labels:
    app: postgres
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi
```

### Shared Storage (ReadWriteMany)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-assets
  namespace: production
spec:
  accessModes:
  - ReadWriteMany
  storageClassName: nfs-storage
  resources:
    requests:
      storage: 100Gi
```

### Block Volume

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: block-storage
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce
  volumeMode: Block
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
```

## Using PVCs in Pods

### Single PVC Mount

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database-pod
spec:
  containers:
  - name: postgres
    image: postgres:15
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: database-pvc
```

### Multiple PVCs

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: data
      mountPath: /data
    - name: logs
      mountPath: /var/log/app
    - name: shared
      mountPath: /shared
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-data-pvc
  - name: logs
    persistentVolumeClaim:
      claimName: app-logs-pvc
  - name: shared
    persistentVolumeClaim:
      claimName: shared-assets
```

## StatefulSet with VolumeClaimTemplates

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
  namespace: database
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        - name: config
          mountPath: /etc/postgresql
      volumes:
      - name: config
        configMap:
          name: postgres-config
  volumeClaimTemplates:
  - metadata:
      name: data
      labels:
        app: postgres
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

## Volume Snapshots

### VolumeSnapshotClass

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
parameters:
  encrypted: "true"
```

### VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: database-snapshot-20231214
  namespace: production
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-pvc
```

### Restore from Snapshot

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-restored
  namespace: production
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  dataSource:
    name: database-snapshot-20231214
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  resources:
    requests:
      storage: 50Gi
```

## Volume Expansion

```yaml
# 1. Ensure StorageClass allows expansion
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
allowVolumeExpansion: true
# ... rest of config

---
# 2. Expand PVC by updating size
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi  # Increased from 50Gi
```

## EmptyDir Volumes

### Memory-Backed EmptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cache-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: cache
      mountPath: /cache
  volumes:
  - name: cache
    emptyDir:
      medium: Memory
      sizeLimit: 1Gi
```

### Disk-Backed EmptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-pod
spec:
  containers:
  - name: worker
    image: worker:latest
    volumeMounts:
    - name: scratch
      mountPath: /tmp/scratch
  volumes:
  - name: scratch
    emptyDir:
      sizeLimit: 10Gi
```

## ConfigMap and Secret Volumes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: config
      mountPath: /etc/config
      readOnly: true
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: app.yaml
        path: config.yaml
        mode: 0644
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400
      items:
      - key: db-password
        path: database/password
```

## Projected Volumes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: combined
      mountPath: /combined
      readOnly: true
  volumes:
  - name: combined
    projected:
      sources:
      - secret:
          name: app-secrets
          items:
          - key: password
            path: secrets/password
      - configMap:
          name: app-config
          items:
          - key: config.yaml
            path: config/app.yaml
      - downwardAPI:
          items:
          - path: pod/labels
            fieldRef:
              fieldPath: metadata.labels
          - path: pod/annotations
            fieldRef:
              fieldPath: metadata.annotations
```

## CSI Driver Examples

### AWS EBS CSI Driver

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    csi:
      driver: ebs.csi.aws.com
      volumeAttributes:
        type: gp3
        iops: "3000"
        encrypted: "true"
```

### Secrets Store CSI Driver

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secrets-pod
spec:
  serviceAccountName: app-sa
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: secrets-store
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
```

## HostPath Volumes (Use with Caution)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    volumeMounts:
    - name: host-data
      mountPath: /host-data
    securityContext:
      privileged: true
  volumes:
  - name: host-data
    hostPath:
      path: /data
      type: DirectoryOrCreate
```

## Best Practices

1. **Dynamic Provisioning**: Prefer dynamic provisioning with StorageClasses
2. **Access Modes**: Use correct access mode (RWO for single node, RWX for multi-node)
3. **Reclaim Policy**: Use Retain for critical data, Delete for temporary
4. **Backup**: Regular snapshots and offsite backups
5. **Monitoring**: Monitor disk usage and performance metrics
6. **Expansion**: Enable volume expansion in StorageClass
7. **Performance**: Choose appropriate storage type for workload
8. **Security**: Encrypt volumes at rest and in transit
9. **Limits**: Set size limits on emptyDir volumes
10. **Labels**: Label PVCs for organization and backup policies
