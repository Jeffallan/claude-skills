# Infrastructure Chaos Engineering

> Reference for: Chaos Engineer
> Load when: Server failures, network chaos, zone outages, infrastructure testing

## Network Latency Injection

```python
# Using toxiproxy for network chaos
import requests
from typing import Literal

class ToxiproxyClient:
    def __init__(self, host: str = "localhost:8474"):
        self.base_url = f"http://{host}"

    def create_proxy(self, name: str, listen: str, upstream: str):
        """Create proxy to inject failures."""
        response = requests.post(f"{self.base_url}/proxies", json={
            "name": name,
            "listen": listen,
            "upstream": upstream,
            "enabled": True
        })
        return response.json()

    def add_latency(self, proxy: str, latency_ms: int, jitter_ms: int = 0):
        """Add latency toxic."""
        return requests.post(
            f"{self.base_url}/proxies/{proxy}/toxics",
            json={
                "name": "latency",
                "type": "latency",
                "attributes": {
                    "latency": latency_ms,
                    "jitter": jitter_ms
                }
            }
        )

    def add_bandwidth_limit(self, proxy: str, rate_kb: int):
        """Limit bandwidth."""
        return requests.post(
            f"{self.base_url}/proxies/{proxy}/toxics",
            json={
                "name": "bandwidth",
                "type": "bandwidth",
                "attributes": {"rate": rate_kb}
            }
        )

    def add_timeout(self, proxy: str, timeout_ms: int):
        """Add connection timeout."""
        return requests.post(
            f"{self.base_url}/proxies/{proxy}/toxics",
            json={
                "name": "timeout",
                "type": "timeout",
                "attributes": {"timeout": timeout_ms}
            }
        )

# Example usage
toxiproxy = ToxiproxyClient()

# Create proxy to database
toxiproxy.create_proxy(
    name="postgres",
    listen="0.0.0.0:5433",
    upstream="postgres:5432"
)

# Inject 200ms latency with 50ms jitter
toxiproxy.add_latency("postgres", latency_ms=200, jitter_ms=50)
```

## AWS Zone Failure Simulation

```python
import boto3
from datetime import datetime, timedelta

class AWSChaosSimulator:
    def __init__(self, region: str):
        self.ec2 = boto3.client('ec2', region_name=region)
        self.asg = boto3.client('autoscaling', region_name=region)
        self.elb = boto3.client('elbv2', region_name=region)

    def simulate_az_failure(
        self,
        availability_zone: str,
        asg_name: str,
        duration_minutes: int = 10
    ):
        """
        Simulate AZ failure by terminating instances in specific AZ.
        Auto Scaling Group will launch replacements in other AZs.
        """
        # Find instances in target AZ
        instances = self.ec2.describe_instances(Filters=[
            {'Name': 'tag:aws:autoscaling:groupName', 'Values': [asg_name]},
            {'Name': 'availability-zone', 'Values': [availability_zone]},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ])

        instance_ids = [
            i['InstanceId']
            for r in instances['Reservations']
            for i in r['Instances']
        ]

        if not instance_ids:
            return {"status": "no_instances", "instances": []}

        # Suspend AZ-specific scaling activities
        self.asg.suspend_processes(
            AutoScalingGroupName=asg_name,
            ScalingProcesses=['AZRebalance']
        )

        # Terminate instances to simulate AZ failure
        self.ec2.terminate_instances(InstanceIds=instance_ids)

        return {
            "status": "simulated",
            "availability_zone": availability_zone,
            "terminated_instances": instance_ids,
            "recovery_time": datetime.now() + timedelta(minutes=duration_minutes)
        }

    def drain_az_from_load_balancer(
        self,
        target_group_arn: str,
        availability_zone: str
    ):
        """Remove AZ from load balancer to simulate zone failure."""
        # Get current target health
        health = self.elb.describe_target_health(
            TargetGroupArn=target_group_arn
        )

        # Find targets in AZ
        targets_to_deregister = []
        for target in health['TargetHealthDescriptions']:
            # Get instance details
            instance = self.ec2.describe_instances(
                InstanceIds=[target['Target']['Id']]
            )
            if instance['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone'] == availability_zone:
                targets_to_deregister.append(target['Target'])

        # Deregister targets
        if targets_to_deregister:
            self.elb.deregister_targets(
                TargetGroupArn=target_group_arn,
                Targets=targets_to_deregister
            )

        return {
            "deregistered_targets": len(targets_to_deregister),
            "availability_zone": availability_zone
        }
```

## Server Resource Exhaustion

```bash
#!/bin/bash
# CPU stress test using stress-ng

# Install stress-ng
sudo apt-get install -y stress-ng

# Stress CPU - use 80% of available cores for 5 minutes
stress-ng --cpu $(nproc --all) --cpu-load 80 --timeout 5m

# Memory stress - consume 70% of available memory
TOTAL_MEM_MB=$(free -m | awk 'NR==2{print $2}')
STRESS_MEM_MB=$((TOTAL_MEM_MB * 70 / 100))
stress-ng --vm 1 --vm-bytes ${STRESS_MEM_MB}M --timeout 5m

# Disk I/O stress - 4 workers doing sequential writes
stress-ng --hdd 4 --hdd-bytes 1G --timeout 5m

# Network bandwidth saturation
# Using iperf3 to saturate network
iperf3 -c target-server -t 300 -P 10  # 10 parallel streams for 5 minutes
```

## Docker Container Chaos with Pumba

```bash
#!/bin/bash
# Pumba - chaos testing for Docker

# Kill random container every 30 seconds
pumba --interval 30s kill --signal SIGKILL "re2:^myapp"

# Pause container for 15 seconds, then resume
pumba pause --duration 15s myapp-container

# Add network delay to container
pumba netem \
  --duration 5m \
  --interface eth0 \
  delay \
    --time 300 \
    --jitter 50 \
  myapp-container

# Packet loss - drop 20% of packets
pumba netem \
  --duration 5m \
  loss \
    --percent 20 \
  myapp-container

# Limit bandwidth to 1Mbps
pumba netem \
  --duration 5m \
  rate \
    --rate 1mbit \
  myapp-container

# Stop all containers matching pattern for 2 minutes
pumba stop --duration 2m "re2:^production-.*"
```

## DNS Failure Simulation

```python
# Using dnsmasq or editing /etc/hosts for DNS chaos

import subprocess
import time
from contextlib import contextmanager

class DNSChaos:
    @staticmethod
    @contextmanager
    def block_domain(domain: str, duration_seconds: int = 60):
        """Block DNS resolution for domain by pointing to localhost."""
        try:
            # Add entry to /etc/hosts
            subprocess.run([
                'sudo', 'sh', '-c',
                f'echo "127.0.0.1 {domain}" >> /etc/hosts'
            ], check=True)

            print(f"Blocked DNS for {domain}")
            yield

        finally:
            # Wait for duration
            time.sleep(duration_seconds)

            # Remove entry from /etc/hosts
            subprocess.run([
                'sudo', 'sed', '-i',
                f'/127.0.0.1 {domain}/d',
                '/etc/hosts'
            ], check=True)

            print(f"Restored DNS for {domain}")

    @staticmethod
    def add_dns_latency(domain: str, latency_ms: int):
        """Add latency to DNS queries using dnsmasq."""
        config = f"""
        # Add to /etc/dnsmasq.conf
        address=/{domain}/127.0.0.1
        min-cache-ttl=0

        # Restart dnsmasq with delay
        """
        return config

# Usage
with DNSChaos.block_domain('api.external-service.com', duration_seconds=120):
    # Run tests while DNS is blocked
    print("DNS blocked - testing fallback behavior")
```

## Certificate Expiry Simulation

```python
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def create_expired_certificate(
    common_name: str,
    expired_days_ago: int = 1
) -> tuple[bytes, bytes]:
    """
    Create an expired TLS certificate for chaos testing.
    Returns (certificate_pem, private_key_pem)
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Certificate valid from 365 days ago to `expired_days_ago` ago
    not_valid_before = datetime.utcnow() - timedelta(days=365)
    not_valid_after = datetime.utcnow() - timedelta(days=expired_days_ago)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name)
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        not_valid_before
    ).not_valid_after(
        not_valid_after
    ).sign(private_key, hashes.SHA256())

    # Serialize to PEM
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return cert_pem, key_pem
```

## Quick Reference

| Failure Type | Tool | Command/Method |
|--------------|------|----------------|
| Network latency | toxiproxy | `add_latency(proxy, ms)` |
| Packet loss | toxiproxy/pumba | `loss --percent 20` |
| AZ failure | AWS API | `simulate_az_failure(az, asg)` |
| CPU stress | stress-ng | `--cpu N --cpu-load 80` |
| Memory exhaustion | stress-ng | `--vm 1 --vm-bytes XG` |
| Container kill | pumba | `kill --signal SIGKILL` |
| DNS failure | /etc/hosts | Block domain resolution |
| Cert expiry | cryptography | Generate expired cert |
