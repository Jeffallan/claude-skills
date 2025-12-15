# Kubernetes Troubleshooting

> Reference for: Kubernetes Specialist
> Load when: kubectl debug, logs, events, common issues

## Essential kubectl Commands

### Pod Inspection

```bash
# Get pods with details
kubectl get pods -n production -o wide
kubectl get pods --all-namespaces
kubectl get pods --field-selector status.phase=Running
kubectl get pods --selector app=web-app

# Describe pod (shows events)
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production

# Get pod logs
kubectl logs web-app-7d5c8b9f4-xk2pm -n production
kubectl logs web-app-7d5c8b9f4-xk2pm -n production --previous  # Previous container
kubectl logs web-app-7d5c8b9f4-xk2pm -n production -c init-container
kubectl logs -f web-app-7d5c8b9f4-xk2pm -n production  # Follow logs
kubectl logs --tail=100 web-app-7d5c8b9f4-xk2pm -n production
kubectl logs --since=1h web-app-7d5c8b9f4-xk2pm -n production

# Get all pod logs from deployment
kubectl logs deployment/web-app -n production --all-containers=true

# Execute commands in pod
kubectl exec -it web-app-7d5c8b9f4-xk2pm -n production -- /bin/sh
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- env
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- cat /etc/config/app.yaml

# Copy files to/from pod
kubectl cp web-app-7d5c8b9f4-xk2pm:/app/logs/app.log ./app.log -n production
kubectl cp ./config.yaml web-app-7d5c8b9f4-xk2pm:/tmp/config.yaml -n production

# Port forward
kubectl port-forward web-app-7d5c8b9f4-xk2pm 8080:8080 -n production
kubectl port-forward service/web-app 8080:80 -n production
```

### Deployment Debugging

```bash
# Check deployment status
kubectl get deployment web-app -n production
kubectl describe deployment web-app -n production
kubectl rollout status deployment/web-app -n production
kubectl rollout history deployment/web-app -n production

# Check replica sets
kubectl get rs -n production
kubectl describe rs web-app-7d5c8b9f4 -n production

# Scale deployment
kubectl scale deployment web-app --replicas=5 -n production

# Rollback deployment
kubectl rollout undo deployment/web-app -n production
kubectl rollout undo deployment/web-app --to-revision=2 -n production

# Restart deployment (recreate pods)
kubectl rollout restart deployment/web-app -n production
```

### Service and Network Debugging

```bash
# Get services
kubectl get svc -n production
kubectl describe svc web-app -n production

# Get endpoints
kubectl get endpoints web-app -n production
kubectl describe endpoints web-app -n production

# Get ingress
kubectl get ingress -n production
kubectl describe ingress web-app -n production

# Get network policies
kubectl get networkpolicy -n production
kubectl describe networkpolicy frontend-to-backend -n production
```

### Resource and Configuration

```bash
# Get ConfigMaps and Secrets
kubectl get configmap -n production
kubectl describe configmap app-config -n production
kubectl get configmap app-config -n production -o yaml

kubectl get secret -n production
kubectl describe secret app-secrets -n production
kubectl get secret app-secrets -n production -o jsonpath='{.data.password}' | base64 -d

# Get PVCs and PVs
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production
kubectl get pv

# Get events (sorted by timestamp)
kubectl get events -n production --sort-by='.lastTimestamp'
kubectl get events -n production --field-selector involvedObject.name=web-app-7d5c8b9f4-xk2pm
```

## Debug Pod

### Ephemeral Debug Container

```bash
# Attach debug container to running pod
kubectl debug -it web-app-7d5c8b9f4-xk2pm -n production \
  --image=busybox:latest \
  --target=web-app

# Create copy of pod with debug tools
kubectl debug web-app-7d5c8b9f4-xk2pm -n production \
  -it \
  --image=ubuntu:latest \
  --share-processes \
  --copy-to=web-app-debug

# Debug with different image
kubectl debug web-app-7d5c8b9f4-xk2pm -n production \
  -it \
  --image=nicolaka/netshoot:latest \
  --target=web-app
```

### Debug on Node

```bash
# Create privileged pod on specific node
kubectl debug node/node-01 -it --image=ubuntu:latest

# Access node filesystem
kubectl debug node/node-01 -it --image=ubuntu:latest -- chroot /host
```

## Common Issues and Solutions

### Issue 1: Pod in Pending State

```bash
# Check pod status and events
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production

# Common causes:
# 1. Insufficient resources
kubectl top nodes
kubectl describe nodes

# 2. PVC not bound
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production

# 3. ImagePullBackOff
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 Events

# 4. Node selector/affinity issues
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production -o yaml | grep -A 5 nodeSelector
```

### Issue 2: CrashLoopBackOff

```bash
# Check logs from crashed container
kubectl logs web-app-7d5c8b9f4-xk2pm -n production --previous

# Check if liveness probe is failing
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Liveness"

# Debug with different command
kubectl run debug-pod --image=myapp:latest -it --rm --restart=Never -- /bin/sh

# Check resource limits
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Limits"
```

### Issue 3: ImagePullBackOff

```bash
# Check image pull secret
kubectl get secret registry-credentials -n production -o yaml

# Test image pull manually
kubectl run test-pull --image=myregistry.io/myapp:v1.2.0 \
  --image-pull-policy=Always \
  --restart=Never \
  -n production

# Create/update image pull secret
kubectl create secret docker-registry registry-credentials \
  --docker-server=myregistry.io \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=user@example.com \
  -n production
```

### Issue 4: Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints web-app -n production
kubectl describe endpoints web-app -n production

# Verify pod labels match service selector
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production --show-labels
kubectl get service web-app -n production -o yaml | grep -A 3 selector

# Test service connectivity from debug pod
kubectl run debug --image=nicolaka/netshoot:latest -it --rm -n production -- bash
# Inside pod:
curl http://web-app.production.svc.cluster.local
nslookup web-app.production.svc.cluster.local
telnet web-app.production.svc.cluster.local 80
```

### Issue 5: DNS Resolution Issues

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns

# Test DNS resolution
kubectl run dnsutils --image=tutum/dnsutils -it --rm -- bash
# Inside pod:
nslookup kubernetes.default
nslookup web-app.production.svc.cluster.local
dig web-app.production.svc.cluster.local

# Check DNS config in pod
kubectl exec web-app-7d5c8b9f4-xk2pm -n production -- cat /etc/resolv.conf
```

### Issue 6: NetworkPolicy Blocking Traffic

```bash
# List network policies
kubectl get networkpolicy -n production
kubectl describe networkpolicy default-deny-all -n production

# Test connectivity
kubectl run test-connectivity --image=nicolaka/netshoot:latest -it --rm -n production -- bash
# Inside pod:
curl -v http://web-app:80
nc -zv web-app 80

# Temporarily allow all traffic (testing only)
kubectl delete networkpolicy --all -n production
```

### Issue 7: High Resource Usage

```bash
# Check resource usage
kubectl top nodes
kubectl top pods -n production
kubectl top pod web-app-7d5c8b9f4-xk2pm -n production --containers

# Check resource requests and limits
kubectl describe pod web-app-7d5c8b9f4-xk2pm -n production | grep -A 10 "Limits"

# Get pods sorted by CPU/memory usage
kubectl top pods -n production --sort-by=cpu
kubectl top pods -n production --sort-by=memory

# Check node capacity
kubectl describe node node-01 | grep -A 10 "Allocated resources"
```

### Issue 8: PersistentVolumeClaim Issues

```bash
# Check PVC status
kubectl get pvc -n production
kubectl describe pvc database-pvc -n production

# Check PV status
kubectl get pv
kubectl describe pv pvc-abc123

# Check storage class
kubectl get storageclass
kubectl describe storageclass fast-ssd

# Events related to PVC
kubectl get events -n production --field-selector involvedObject.name=database-pvc
```

## Advanced Debugging

### API Server Debugging

```bash
# Enable verbose output
kubectl get pods -n production -v=9

# Check API server logs (on master node)
journalctl -u kube-apiserver -f

# Check cluster info
kubectl cluster-info
kubectl cluster-info dump > cluster-dump.txt
```

### RBAC Debugging

```bash
# Check if ServiceAccount can perform action
kubectl auth can-i get pods --as=system:serviceaccount:production:web-app-sa -n production

# List permissions for ServiceAccount
kubectl describe sa web-app-sa -n production
kubectl describe role web-app-role -n production
kubectl describe rolebinding web-app-rolebinding -n production

# Check all permissions
kubectl auth can-i --list --as=system:serviceaccount:production:web-app-sa -n production
```

### Performance Debugging

```bash
# Get resource metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods

# Check pod overhead
kubectl get pod web-app-7d5c8b9f4-xk2pm -n production -o json | jq '.spec.overhead'

# Check priority classes
kubectl get priorityclasses
kubectl describe priorityclass high-priority
```

## Diagnostic Tools

### Network Tools Container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: netshoot
  namespace: production
spec:
  containers:
  - name: netshoot
    image: nicolaka/netshoot:latest
    command: ["/bin/sleep", "3600"]
  restartPolicy: Never
```

### Database Client Container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: postgres-client
  namespace: production
spec:
  containers:
  - name: postgres
    image: postgres:15-alpine
    command: ["/bin/sleep", "3600"]
    env:
    - name: PGHOST
      value: postgres-service
    - name: PGUSER
      value: myapp
    - name: PGPASSWORD
      valueFrom:
        secretKeyRef:
          name: postgres-secrets
          key: password
  restartPolicy: Never
```

## Quick Reference

### Pod States
- **Pending**: Waiting to be scheduled
- **ContainerCreating**: Pulling image / creating container
- **Running**: Pod is running
- **Succeeded**: All containers exited successfully
- **Failed**: At least one container failed
- **CrashLoopBackOff**: Container keeps crashing
- **ImagePullBackOff**: Cannot pull image
- **ErrImagePull**: Image pull error
- **Unknown**: Cannot get pod status

### Common Exit Codes
- **0**: Success
- **1**: General error
- **137**: SIGKILL (OOMKilled - out of memory)
- **139**: SIGSEGV (segmentation fault)
- **143**: SIGTERM (graceful termination)

## Best Practices

1. **Logs**: Always check logs first with `kubectl logs`
2. **Events**: Use `kubectl describe` to see events
3. **Labels**: Use consistent labels for easier debugging
4. **Resources**: Set appropriate requests and limits
5. **Health Checks**: Implement proper liveness and readiness probes
6. **Monitoring**: Set up comprehensive monitoring and alerting
7. **Debug Tools**: Keep debug containers ready
8. **Documentation**: Document common issues and solutions
