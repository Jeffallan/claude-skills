# Chaos Engineering Tools & Automation

> Reference for: Chaos Engineer
> Load when: Tool selection, automation, CI/CD integration, chaos platforms

## Chaos Monkey (Netflix)

```python
# Chaos Monkey configuration for Spinnaker
{
  "enabled": true,
  "schedule": {
    "enabled": true,
    "frequency": 1,  # Run once per day
    "frequencyUnit": "DAYS",
    "start": "09:00",
    "end": "15:00",
    "timezone": "America/Los_Angeles"
  },
  "grouping": "cluster",
  "regionsAreIndependent": true,
  "exceptions": [
    {
      "type": "Opt-In",
      "account": "production",
      "stack": "*",
      "detail": "*"
    }
  ],
  "minTimeBetweenKillsInWorkDays": 2,
  "maxAppsPerDay": 5,
  "clusters": [
    {
      "app": "myapp",
      "stack": "production",
      "enabled": true,
      "regions": ["us-east-1", "us-west-2"],
      "meanTimeBetweenKillsInWorkDays": 2,
      "minTimeBetweenKillsInWorkDays": 1,
      "maxTerminationsPerDay": 1
    }
  ]
}
```

```bash
#!/bin/bash
# Simpl Chaos Monkey implementation

INSTANCE_COUNT=5
KILL_PERCENTAGE=20

# Get running instances from ASG
INSTANCES=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names my-asg \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text)

# Calculate number to terminate
TOTAL=$(echo "$INSTANCES" | wc -w)
TO_KILL=$(( TOTAL * KILL_PERCENTAGE / 100 ))

if [ $TO_KILL -eq 0 ]; then
  TO_KILL=1
fi

# Randomly select and terminate instances
echo "$INSTANCES" | tr ' ' '\n' | shuf | head -n $TO_KILL | while read instance; do
  echo "Terminating instance: $instance"
  aws ec2 terminate-instances --instance-ids "$instance"
  sleep 30  # Wait between terminations
done
```

## Gremlin Integration

```python
import requests
from typing import Literal

class GremlinClient:
    def __init__(self, api_key: str, team_id: str):
        self.api_key = api_key
        self.team_id = team_id
        self.base_url = "https://api.gremlin.com/v1"
        self.headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json"
        }

    def create_cpu_attack(
        self,
        targets: list[str],
        length: int = 60,
        cores: int = 1,
        percent: int = 50
    ):
        """Launch CPU resource attack."""
        payload = {
            "command": {
                "type": "cpu",
                "args": [
                    "-l", str(length),
                    "-c", str(cores),
                    "-p", str(percent)
                ]
            },
            "target": {
                "type": "Exact",
                "exact": targets
            }
        }

        response = requests.post(
            f"{self.base_url}/attacks/new",
            headers=self.headers,
            json=payload
        )
        return response.json()

    def create_network_attack(
        self,
        targets: list[str],
        attack_type: Literal["latency", "packet_loss", "blackhole"],
        length: int = 60,
        **kwargs
    ):
        """Launch network attack."""
        args = ["-l", str(length)]

        if attack_type == "latency":
            # kwargs: delay_ms, jitter_ms
            args.extend(["-m", str(kwargs.get('delay_ms', 100))])
            if 'jitter_ms' in kwargs:
                args.extend(["-j", str(kwargs['jitter_ms'])])

        elif attack_type == "packet_loss":
            # kwargs: percent
            args.extend(["-p", str(kwargs.get('percent', 10))])

        elif attack_type == "blackhole":
            # kwargs: port, protocol
            if 'port' in kwargs:
                args.extend(["--port", str(kwargs['port'])])
            if 'protocol' in kwargs:
                args.extend(["--protocol", kwargs['protocol']])

        payload = {
            "command": {
                "type": attack_type,
                "args": args
            },
            "target": {
                "type": "Exact",
                "exact": targets
            }
        }

        response = requests.post(
            f"{self.base_url}/attacks/new",
            headers=self.headers,
            json=payload
        )
        return response.json()

    def halt_attack(self, attack_id: str):
        """Stop running attack."""
        response = requests.delete(
            f"{self.base_url}/attacks/{attack_id}",
            headers=self.headers
        )
        return response.status_code == 200

    def create_scenario(self, name: str, attacks: list[dict]):
        """Create reusable attack scenario."""
        payload = {
            "name": name,
            "description": f"Chaos scenario: {name}",
            "graph": {
                "nodes": attacks
            }
        }

        response = requests.post(
            f"{self.base_url}/scenarios",
            headers=self.headers,
            json=payload
        )
        return response.json()

# Example usage
gremlin = GremlinClient(api_key="...", team_id="...")

# CPU attack on specific containers
gremlin.create_cpu_attack(
    targets=["container-id-123", "container-id-456"],
    length=300,  # 5 minutes
    cores=2,
    percent=80
)

# Network latency attack
gremlin.create_network_attack(
    targets=["host-abc"],
    attack_type="latency",
    length=180,
    delay_ms=500,
    jitter_ms=100
)
```

## CI/CD Integration

```yaml
# GitHub Actions workflow for chaos testing
name: Chaos Engineering Tests

on:
  schedule:
    - cron: '0 10 * * 1-5'  # Weekdays at 10 AM
  workflow_dispatch:  # Manual trigger

jobs:
  chaos-tests:
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name staging-cluster --region us-east-1

      - name: Install Litmus
        run: |
          kubectl apply -f https://litmuschaos.github.io/litmus/litmus-operator-v2.14.0.yaml
          kubectl wait --for=condition=Ready pods -l app.kubernetes.io/component=operator --timeout=300s

      - name: Run pod-delete chaos experiment
        run: |
          kubectl apply -f .github/chaos/pod-delete-experiment.yaml
          kubectl wait --for=condition=Complete chaosengine/pod-delete-chaos --timeout=600s

      - name: Verify system recovery
        run: |
          # Check all pods are running
          kubectl wait --for=condition=Ready pods -l app=myapp --timeout=300s

          # Verify no error rate spike
          ERROR_RATE=$(curl -s "http://prometheus/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1]')

          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE"
            exit 1
          fi

      - name: Cleanup chaos resources
        if: always()
        run: |
          kubectl delete chaosengine --all
          kubectl delete chaosexperiments --all

      - name: Report results to Slack
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Chaos test failed in staging",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Chaos engineering test failed. System did not recover properly."
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Jenkins Pipeline

```groovy
// Jenkinsfile for chaos testing
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging'],
            description: 'Target environment'
        )
        choice(
            name: 'CHAOS_TYPE',
            choices: ['pod-delete', 'network-latency', 'cpu-stress'],
            description: 'Type of chaos experiment'
        )
        string(
            name: 'DURATION',
            defaultValue: '300',
            description: 'Chaos duration in seconds'
        )
    }

    stages {
        stage('Pre-flight Check') {
            steps {
                script {
                    // Verify steady state before chaos
                    def errorRate = sh(
                        script: '''
                            curl -s "http://prometheus/api/v1/query?query=rate(http_requests_total{status=~\\"5..\\"}[5m])" | jq -r '.data.result[0].value[1]'
                        ''',
                        returnStdout: true
                    ).trim()

                    if (errorRate.toFloat() > 0.01) {
                        error("System not in steady state. Error rate: ${errorRate}")
                    }
                }
            }
        }

        stage('Run Chaos Experiment') {
            steps {
                script {
                    def chaosManifest = """
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: jenkins-chaos-${env.BUILD_NUMBER}
  namespace: ${params.ENVIRONMENT}
spec:
  appinfo:
    appns: '${params.ENVIRONMENT}'
    applabel: 'app=myapp'
    appkind: 'deployment'
  chaosServiceAccount: litmus-admin
  experiments:
    - name: ${params.CHAOS_TYPE}
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: '${params.DURATION}'
"""

                    writeFile file: 'chaos-manifest.yaml', text: chaosManifest

                    sh '''
                        kubectl apply -f chaos-manifest.yaml
                        kubectl wait --for=condition=Complete chaosengine/jenkins-chaos-${BUILD_NUMBER} --timeout=900s
                    '''
                }
            }
        }

        stage('Verify Recovery') {
            steps {
                sh '''
                    # Wait for system to stabilize
                    sleep 60

                    # Check pod status
                    kubectl get pods -n ${ENVIRONMENT} -l app=myapp

                    # Verify all pods running
                    READY_PODS=$(kubectl get pods -n ${ENVIRONMENT} -l app=myapp -o json | jq '[.items[] | select(.status.phase=="Running")] | length')
                    TOTAL_PODS=$(kubectl get pods -n ${ENVIRONMENT} -l app=myapp -o json | jq '.items | length')

                    if [ "$READY_PODS" -ne "$TOTAL_PODS" ]; then
                        echo "Not all pods recovered: $READY_PODS/$TOTAL_PODS ready"
                        exit 1
                    fi
                '''
            }
        }

        stage('Extract Learnings') {
            steps {
                script {
                    // Get chaos result
                    def chaosResult = sh(
                        script: "kubectl get chaosresult -n ${params.ENVIRONMENT} -o json",
                        returnStdout: true
                    )

                    // Parse and store results
                    writeFile file: "chaos-result-${env.BUILD_NUMBER}.json", text: chaosResult

                    // Archive results
                    archiveArtifacts artifacts: "chaos-result-${env.BUILD_NUMBER}.json"
                }
            }
        }
    }

    post {
        always {
            // Cleanup
            sh '''
                kubectl delete chaosengine jenkins-chaos-${BUILD_NUMBER} -n ${ENVIRONMENT} || true
            '''
        }

        failure {
            // Notify team
            slackSend(
                color: 'danger',
                message: "Chaos test failed: ${params.CHAOS_TYPE} in ${params.ENVIRONMENT}"
            )
        }

        success {
            slackSend(
                color: 'good',
                message: "Chaos test passed: ${params.CHAOS_TYPE} in ${params.ENVIRONMENT}. System recovered successfully."
            )
        }
    }
}
```

## Continuous Chaos Dashboard

```python
# Flask app for chaos monitoring dashboard
from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

class ChaosDashboard:
    def __init__(self, prometheus_url: str):
        self.prometheus = prometheus_url

    def get_experiment_metrics(self, hours: int = 24):
        """Get chaos experiment results from last N hours."""
        end = datetime.now()
        start = end - timedelta(hours=hours)

        query = f'''
            sum by (experiment, verdict) (
                increase(litmuschaos_experiment_verdict[{hours}h])
            )
        '''

        response = requests.get(
            f"{self.prometheus}/api/v1/query",
            params={"query": query}
        )

        return response.json()

    def get_mttr_trend(self):
        """Get MTTR trend over time."""
        query = '''
            avg_over_time(
                avg(
                    time() - timestamp(
                        kube_pod_status_phase{phase="Running"} == 1
                    )
                )[7d:]
            )
        '''

        response = requests.get(
            f"{self.prometheus}/api/v1/query",
            params={"query": query}
        )

        return response.json()

@app.route('/api/chaos-summary')
def chaos_summary():
    dashboard = ChaosDashboard(prometheus_url="http://prometheus:9090")

    return jsonify({
        "experiments": dashboard.get_experiment_metrics(hours=24),
        "mttr_trend": dashboard.get_mttr_trend(),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Quick Reference

| Tool | Use Case | Integration |
|------|----------|-------------|
| Chaos Monkey | Random instance termination | Spinnaker/AWS ASG |
| Gremlin | SaaS chaos platform | API/Web UI |
| Litmus | Kubernetes chaos | Kubectl/Helm |
| Chaos Mesh | Advanced K8s chaos | CRDs/Dashboard |
| Toxiproxy | Network proxy chaos | Docker/API |
| Pumba | Container chaos | Docker CLI |
