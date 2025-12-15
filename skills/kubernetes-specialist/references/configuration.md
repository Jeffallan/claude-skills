# Kubernetes Configuration Management

> Reference for: Kubernetes Specialist
> Load when: ConfigMaps, Secrets, environment variables

## ConfigMap Patterns

### Basic ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  # Simple key-value pairs
  database.host: "postgres-service.database.svc.cluster.local"
  database.port: "5432"
  database.name: "appdb"

  # Multi-line configuration
  app.properties: |
    server.port=8080
    logging.level=INFO
    cache.enabled=true
    cache.ttl=3600

  # JSON configuration
  features.json: |
    {
      "featureA": true,
      "featureB": false,
      "maxConnections": 100
    }

  # YAML configuration
  config.yaml: |
    server:
      port: 8080
      timeout: 30s
    database:
      pool_size: 20
      max_connections: 100
```

### ConfigMap from Files

```bash
# Create from literal values
kubectl create configmap app-config \
  --from-literal=database.host=postgres \
  --from-literal=database.port=5432

# Create from file
kubectl create configmap nginx-config \
  --from-file=nginx.conf

# Create from directory
kubectl create configmap app-configs \
  --from-file=configs/
```

## Secret Patterns

### Opaque Secret (Generic)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
stringData:
  # Plain text (will be base64 encoded)
  db-password: "MySecurePassword123!"
  api-key: "sk-1234567890abcdef"
  jwt-secret: "super-secret-jwt-key"
data:
  # Already base64 encoded
  tls.crt: LS0tLS1CRUdJTi...
  tls.key: LS0tLS1CRUdJTi...
```

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: example-tls
  namespace: production
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    MIIDXTCCAkWgAwIBAgIJAKZ...
    -----END CERTIFICATE-----
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    MIIEvQIBADANBgkqhkiG9w0B...
    -----END PRIVATE KEY-----
```

### Docker Registry Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
  namespace: production
type: kubernetes.io/dockerconfigjson
stringData:
  .dockerconfigjson: |
    {
      "auths": {
        "myregistry.io": {
          "username": "myuser",
          "password": "mypassword",
          "email": "user@example.com",
          "auth": "bXl1c2VyOm15cGFzc3dvcmQ="
        }
      }
    }
```

### Basic Auth Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: basic-auth
  namespace: production
type: kubernetes.io/basic-auth
stringData:
  username: admin
  password: super-secret-password
```

### SSH Auth Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ssh-key
  namespace: production
type: kubernetes.io/ssh-auth
stringData:
  ssh-privatekey: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    b3BlbnNzaC1rZXktdjEAAAAABG5vbmUA...
    -----END OPENSSH PRIVATE KEY-----
```

## Using ConfigMaps and Secrets

### Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-pod
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    # Single value from ConfigMap
    - name: DATABASE_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host

    # Single value from Secret
    - name: DATABASE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password

    # All keys from ConfigMap as env vars
    envFrom:
    - configMapRef:
        name: app-config
      prefix: CONFIG_

    # All keys from Secret as env vars
    - secretRef:
        name: app-secrets
      prefix: SECRET_
```

### Volume Mounts

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
    # Mount entire ConfigMap as directory
    - name: config-volume
      mountPath: /etc/config
      readOnly: true

    # Mount specific key as file
    - name: app-properties
      mountPath: /etc/app/app.properties
      subPath: app.properties
      readOnly: true

    # Mount Secret as files
    - name: secrets-volume
      mountPath: /etc/secrets
      readOnly: true

    # Mount TLS certificates
    - name: tls-certs
      mountPath: /etc/tls
      readOnly: true

  volumes:
  - name: config-volume
    configMap:
      name: app-config

  - name: app-properties
    configMap:
      name: app-config
      items:
      - key: app.properties
        path: app.properties

  - name: secrets-volume
    secret:
      secretName: app-secrets
      defaultMode: 0400  # Read-only for owner

  - name: tls-certs
    secret:
      secretName: example-tls
```

## Immutable ConfigMaps and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: immutable-config
  namespace: production
immutable: true
data:
  key: value
---
apiVersion: v1
kind: Secret
metadata:
  name: immutable-secret
  namespace: production
type: Opaque
immutable: true
stringData:
  password: "MyPassword123"
```

## External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
  - secretKey: db-password
    remoteRef:
      key: prod/database/password
  - secretKey: api-key
    remoteRef:
      key: prod/api/key
---
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

## Sealed Secrets (GitOps)

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  encryptedData:
    db-password: AgBj8xK5...encrypted...base64
    api-key: AgCY9mL2...encrypted...base64
  template:
    metadata:
      name: app-secrets
      namespace: production
    type: Opaque
```

## Environment Variable Best Practices

### Structured Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:latest
    env:
    # Application settings
    - name: APP_NAME
      value: "my-application"
    - name: APP_ENV
      value: "production"
    - name: APP_VERSION
      value: "v1.2.0"

    # Database configuration
    - name: DB_HOST
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.host
    - name: DB_PORT
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.port
    - name: DB_NAME
      valueFrom:
        configMapKeyRef:
          name: app-config
          key: database.name
    - name: DB_USER
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password

    # Kubernetes metadata
    - name: POD_NAME
      valueFrom:
        fieldRef:
          fieldPath: metadata.name
    - name: POD_NAMESPACE
      valueFrom:
        fieldRef:
          fieldPath: metadata.namespace
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName

    # Resource limits
    - name: MEMORY_LIMIT
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: limits.memory
    - name: CPU_REQUEST
      valueFrom:
        resourceFieldRef:
          containerName: app
          resource: requests.cpu
```

## Dynamic Configuration Updates

```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    metadata:
      annotations:
        # Force pod restart on config change
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
    spec:
      containers:
      - name: app
        image: myapp:latest
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: app-config
```

## Best Practices

1. **Separation**: Use ConfigMaps for non-sensitive data, Secrets for credentials
2. **Immutability**: Mark production configs as immutable for safety
3. **Versioning**: Include version in ConfigMap/Secret names for updates
4. **Least Privilege**: Mount secrets as files with restrictive permissions (0400)
5. **External Secrets**: Use External Secrets Operator for cloud secret managers
6. **No Hardcoding**: Never hardcode secrets in container images
7. **Encryption**: Enable encryption at rest for Secrets in etcd
8. **GitOps**: Use Sealed Secrets for safe GitOps workflows
9. **Rotation**: Implement secret rotation strategies
10. **Validation**: Validate configuration before deployment
