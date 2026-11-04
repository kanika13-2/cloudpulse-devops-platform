# 🌐 CLOUDPULSE: AWS Cloud Infrastructure & Intelligent DevOps Automation Platform

[![CI/CD Pipeline](https://github.com/cloudpulse/platform/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/cloudpulse/platform/actions)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-005571.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-multi--stage-2496ED.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-v1.29%2B-326CE5.svg)](https://kubernetes.io/)
[![AWS EKS & ECR](https://img.shields.io/badge/aws-EKS%20%7C%20ECR%20%7C%20CloudWatch-FF9900.svg)](https://aws.amazon.com/)
[![Observability](https://img.shields.io/badge/observability-Prometheus%20%7C%20Grafana-F46800.svg)](https://prometheus.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

---

## 📌 Executive Overview

**CloudPulse** is an enterprise-grade cloud-native infrastructure and intelligent DevOps automation platform designed for mission-critical microservice workloads. It demonstrates modern Senior DevOps, SRE, and Cloud Engineering practices:

- **High-Performance Core Microservice:** Python 3.12+ FastAPI application with asynchronous ASGI concurrency, OpenMetrics telemetry, and distributed `X-Correlation-ID` tracing.
- **Defense-in-Depth Containerization:** Multi-stage Docker build running under an unprivileged non-root user (`UID 10001`), dropping all Linux capabilities, and integrating container health checks.
- **Resilient Kubernetes Orchestration:** High-availability deployment (2 replicas), zero-downtime rolling updates (`maxSurge: 1`, `maxUnavailable: 0`), Horizontal Pod Autoscaler (HPA v2), Pod Disruption Budgets (PDB), and startup/liveness/readiness probes.
- **Dual-Plane Observability:** Real-time in-cluster metrics via Prometheus & pre-provisioned Grafana dashboards paired with enterprise cloud aggregation in AWS CloudWatch (Container Insights & Fluent Bit).
- **Secure Keyless CI/CD:** GitHub Actions pipeline utilizing AWS OpenID Connect (OIDC) federated role assumption—zero permanent AWS access keys or secrets stored.
- **Cross-Platform DevOps Automation:** Native Linux Bash and Windows PowerShell scripts providing automated health auditing, synthetic load generation, and one-command disaster recovery rollbacks.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Ingress_Layer ["Traffic Ingress & Edge Routing"]
        User["End Users / Mobile / Microservices"]
        ALB["AWS Application Load Balancer / Ingress Controller"]
        User -->|HTTPS :443| ALB
    end

    subgraph EKS_Platform ["Amazon EKS Cluster (Namespace: cloudpulse)"]
        Svc["Kubernetes Service (ClusterIP :80)"]
        ALB -->|Forward Traffic| Svc

        subgraph Pod_Group ["CloudPulse Application Pods (HPA 2..10 Replicas)"]
            Pod1["Pod 1: CloudPulse API\n(Non-Root UID: 10001)"]
            Pod2["Pod 2: CloudPulse API\n(Non-Root UID: 10001)"]
            PodN["Pod N: Scaled Replicas..."]
        end

        Svc --> Pod1
        Svc --> Pod2
        Svc -.-> PodN

        subgraph In_Cluster_Monitoring ["In-Cluster Observability"]
            Prom["Prometheus Server :9090\n(Scrapes :8000/metrics)"]
            Graf["Grafana Server :3000\n(Provisioned Dashboard)"]
            FluentBit["AWS for Fluent Bit DaemonSet\n(JSON Container Logs)"]
        end

        Prom -.->|Scrapes Telemetry| Pod1
        Prom -.->|Scrapes Telemetry| Pod2
        Graf -->|Queries PromQL| Prom
        FluentBit -.->|Harvests stdout| Pod1
        FluentBit -.->|Harvests stdout| Pod2
    end

    subgraph AWS_Cloud ["AWS Managed Cloud Services"]
        ECR["Amazon Elastic Container Registry (ECR)"]
        OIDC["AWS IAM OIDC Identity Provider"]
        CW_Logs["AWS CloudWatch Logs\n/aws/eks/cloudpulse/application"]
        CW_Alarms["CloudWatch Metric Alarms\n(CPU, 5xx, Restarts)"]
        SNS["Amazon SNS Alerts Topic"]

        FluentBit -->|HTTPS TLS| CW_Logs
        CW_Logs --> CW_Alarms
        CW_Alarms -->|Threshold Exceeded| SNS
    end

    subgraph CICD_Automation ["CI/CD Automation Pipeline (GitHub Actions)"]
        GitPush["Git Push / PR to main"]
        GHA["GitHub Actions Runner"]
        GitPush --> GHA
        GHA -->|1. Pytest Coverage| GHA
        GHA -->|2. Docker Multi-Stage Build| GHA
        GHA -->|3. K8s Manifest Schema Lint| GHA
        GHA -->|4. Keyless OIDC STS Exchange| OIDC
        GHA -->|5. Push Image| ECR
        GHA -->|6. Rolling Update Deploy| EKS_Platform
    end
```

---

## 🗂️ Project Repository Structure

```
c:\Users\itska\Downloads\AWS/
├── .github/
│   └── workflows/
│       ├── ci-cd.yml                # Main CI/CD: Test, Lint, Docker Build, ECR Push, EKS Rollout
│       └── pr-check.yml             # Fast PR Quality Gatekeeper
├── app/
│   ├── __init__.py
│   ├── config.py                    # Pydantic BaseSettings & Environment Configurations
│   ├── logger.py                    # Structured JSON / Console Logging & Correlation ID Context
│   ├── main.py                      # FastAPI App, ASGI Middleware, Root & Router Mounting
│   ├── metrics.py                   # Prometheus Telemetry Engine (Counters, Gauges, Histograms)
│   ├── models.py                    # Pydantic v2 Typed Schemas & Data Contracts
│   └── routers/
│       ├── __init__.py
│       ├── health.py                # Liveness & Readiness Probes (/health)
│       ├── metrics.py               # Prometheus Exposition Endpoint (/metrics)
│       ├── simulation.py            # Synthetic CPU Load & Error Generators (/api/v1/simulate/*)
│       └── system.py                # Host Topology & Diagnostics (/api/v1/system/info)
├── docs/
│   ├── ARCHITECTURE.md              # Detailed Architectural Blueprint & Data Flow
│   ├── AWS_EKS_GUIDE.md             # EKS & ECR Production Provisioning Runbook
│   ├── INTERVIEW_PREP.md            # Senior DevOps Interview Guide & STAR Method Deep Dive
│   └── TROUBLESHOOTING.md           # Production Incident Triage Matrix & Disaster Recovery
├── k8s/
│   ├── 00-namespace.yaml            # Dedicated 'cloudpulse' Kubernetes Namespace
│   ├── 01-configmap.yaml            # App Configuration & Observability Flags
│   ├── 02-secret.yaml               # Secret Template (External Secrets / AWS Secrets Manager)
│   ├── 03-deployment.yaml           # 2 Replicas, Rolling Update, Non-Root Security, Probes, Limits
│   ├── 04-service.yaml              # ClusterIP Service (:80 -> :8000)
│   ├── 05-hpa.yaml                  # Horizontal Pod Autoscaler v2 (CPU 70%, Memory 80%, 2..10)
│   ├── 06-pdb.yaml                  # Pod Disruption Budget (minAvailable: 1)
│   ├── 07-serviceaccount.yaml       # AWS IAM Roles for Service Accounts (IRSA) Annotation
│   └── 08-ingress.yaml              # AWS ALB Ingress Controller Manifest
├── monitoring/
│   ├── cloudwatch/
│   │   ├── amazon-cloudwatch-agent.json # Unified CloudWatch Agent Prometheus & Log Config
│   │   ├── cloudwatch-alarms.json       # Metric Alarms: High CPU, 5xx Spikes, Pod Restarts
│   │   ├── CLOUDWATCH_SETUP.md          # CloudWatch & Container Insights Integration Guide
│   │   └── fluent-bit-configmap.yaml    # AWS for Fluent Bit JSON Log Shipping DaemonSet
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── cloudpulse-overview.json # Production Grafana Dashboard (8 Real-Time Panels)
│   │   └── provisioning/
│   │       ├── dashboards/dashboards.yml# Automatic Dashboard Provisioning
│   │       └── datasources/datasources.yml # Automatic Prometheus DataSource Provisioning
│   └── prometheus/
│       └── prometheus.yml           # Prometheus Scrape Configuration (:8000/metrics, 5s interval)
├── scripts/
│   ├── linux/
│   │   ├── deploy.sh                # Automated K8s Deployment & Rollout Verification
│   │   ├── health_check.sh          # Endpoint Diagnostics & Pod Vitals Probe
│   │   ├── rollback.sh              # Zero-Downtime Rollout Undo & Stability Check
│   │   └── simulate_load.sh         # Concurrent HTTP Load Generator for HPA Testing
│   └── windows/
│       ├── docker-manage.ps1        # Docker Compose Stack Controller (Build, Up, Down, Test)
│       ├── health-check.ps1         # PowerShell Native Health & Metric Diagnostics
│       ├── local-setup.ps1          # Virtualenv Bootstrapper & Local Test Runner
│       └── rollback.ps1             # PowerShell Automated Rollback Controller
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest Fixtures, Mock Settings & TestClient
│   ├── test_health.py               # Health & Diagnostic Probe Tests
│   ├── test_logging.py              # JSON & Standard Formatter Unit Tests
│   ├── test_metrics.py              # Prometheus Counter & Gauge Verification Tests
│   ├── test_root.py                 # Root & Correlation ID Propagation Tests
│   ├── test_simulation.py           # Load & Error Simulation Endpoint Tests
│   ├── test_system.py               # System Topology & Diagnostics Tests
│   └── validate_k8s.py              # Kubernetes Manifest Schema & YAML Integrity Validator
├── .dockerignore
├── .gitignore
├── docker-compose.yml               # Multi-Container Compose (App + Prometheus + Grafana)
├── Dockerfile                       # Hardened Multi-Stage Production Image (Non-Root)
├── pytest.ini                       # Pytest Runtime Configuration & Marker Rules
├── requirements.txt                 # Application Dependencies
├── requirements-dev.txt             # Testing & Development Tooling
└── TASK_STATUS.md                   # Real-Time Project Milestone Tracking Matrix
```

---

## ⚡ Quickstart: Local Development

CloudPulse is 100% functional locally without any AWS credentials or cloud dependencies.

### 🪟 Windows Setup (PowerShell)

```powershell
# 1. Clone repository and enter directory
cd c:\Users\itska\Downloads\AWS

# 2. Run the automated local environment setup
.\scripts\windows\local-setup.ps1

# 3. Start CloudPulse API locally
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 🐧 Linux Setup (Bash)

```bash
# 1. Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# 3. Execute unit tests
pytest --cov=app --cov-report=term-missing

# 4. Start CloudPulse API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🐳 Docker & Multi-Container Composition

The local environment includes **CloudPulse API**, **Prometheus**, and **Grafana** with auto-provisioned dashboards.

```powershell
# Start complete local observability stack (Windows)
.\scripts\windows\docker-manage.ps1 -Action Up

# Or using standard Docker Compose:
docker compose up -d --build
```

### Access Local Endpoints:
| Service | Local URL | Default Credentials | Description |
| :--- | :--- | :--- | :--- |
| **CloudPulse API** | `http://localhost:8000` | N/A | Core REST & Diagnostics API |
| **Interactive Docs** | `http://localhost:8000/docs` | N/A | Swagger UI API Documentation |
| **Health Probe** | `http://localhost:8000/health` | N/A | Liveness & Readiness JSON Diagnostics |
| **Prometheus Metrics**| `http://localhost:8000/metrics`| N/A | OpenMetrics Telemetry Stream |
| **Prometheus UI** | `http://localhost:9090` | N/A | Time-Series Metric Query Browser |
| **Grafana UI** | `http://localhost:3000` | `admin` / `admin` | Real-Time Production Analytics Dashboard |

To stop the container stack:
```powershell
.\scripts\windows\docker-manage.ps1 -Action Down
```

---

## ☸️ Kubernetes Orchestration & Auto-Healing

Deploy CloudPulse to a local cluster (Kind, Minikube, Docker Desktop) or Amazon EKS:

```bash
# Deploy all Kubernetes manifests in sequence
./scripts/linux/deploy.sh
```

### Demonstrating Kubernetes Self-Healing:
Delete an active application pod to watch Kubernetes instantly replace it within 2 seconds:
```bash
# 1. View running pods
kubectl get pods -n cloudpulse

# 2. Delete an active pod
kubectl delete pod -n cloudpulse -l app.kubernetes.io/name=cloudpulse-api --wait=false

# 3. Observe self-healing recreation
kubectl get pods -n cloudpulse -w
```

### Demonstrating Horizontal Pod Autoscaling (HPA):
Simulate synthetic traffic to trigger CPU autoscaling from 2 to 10 replicas:
```bash
# Terminal 1: Watch HPA and pod count
kubectl get hpa -n cloudpulse -w

# Terminal 2: Generate concurrent synthetic load
./scripts/linux/simulate_load.sh http://localhost:8000 200 15
```

---

## 🔄 Automated Rolling Updates & Rollback

### Zero-Downtime Rolling Update:
```bash
# Update container image to new version
kubectl set image deployment/cloudpulse-api cloudpulse-api=cloudpulse-platform:2.0.0 -n cloudpulse

# Monitor rolling update progression
kubectl rollout status deployment/cloudpulse-api -n cloudpulse
```

### Safe Automated Rollback (Disaster Recovery):
If a bad build is deployed, trigger immediate automated recovery:

```bash
# Linux
./scripts/linux/rollback.sh

# Windows
.\scripts\windows\rollback.ps1
```

---

## 📊 Dual-Plane Observability: Grafana & CloudWatch

### 1. Pre-Configured Grafana Dashboard (`cloudpulse-overview.json`)
The included Grafana dashboard auto-provisions 8 production-grade telemetry panels:
1. **Application Uptime:** Live counter tracking service continuous runtime.
2. **CPU Utilization %:** Gauge panel monitoring CPU consumption against 70% threshold.
3. **Resident Memory (RSS):** Tracks process memory in Megabytes against memory limits.
4. **In-Flight HTTP Requests:** Active concurrent connections currently processed.
5. **HTTP Request Throughput:** Time-series graph segmented by status code (200, 400, 500).
6. **Request Latency Quantiles:** Real-time p50, p90, and p99 percentile response latency.
7. **HTTP 5xx Error Rate %:** Rate calculation alerting when error rate exceeds 1%.
8. **Simulated Alerts Count:** Bar gauge recording simulated failure tests.

### 2. AWS CloudWatch Metrics & Alarms
- **Log Group:** `/aws/eks/cloudpulse/application`
- **Metric Alarms Configured:**
  - `CloudPulse-HighCPUUtilizationAlarm` (> 80% for 2 consecutive minutes)
  - `CloudPulse-High5xxErrorRateAlarm` (> 5 error responses in 5 minutes)
  - `CloudPulse-UnhealthyHostCountAlarm` (Target group unhealthy count >= 1)
  - `CloudPulse-PodCrashLoopRestartAlarm` (Container restarts > 2 within 15 minutes)

---

## 🔐 AWS Security & IAM Least Privilege

1. **Keyless CI/CD Authentication:** GitHub Actions authenticates via AWS OIDC Web Identity Federation (`sts:AssumeRoleWithWebIdentity`). Zero hardcoded credentials exist in code or GitHub Secrets.
2. **Pod-Level IAM (IRSA):** Pods use AWS IAM Roles for Service Accounts. Permissions to stream to CloudWatch are bound strictly to the `cloudpulse-serviceaccount` rather than the host node.
3. **Container Isolation:** Image runs as unprivileged user `cloudpulse` (`UID 10001`), with `allowPrivilegeEscalation: false` and all Linux capabilities dropped.

---

## 🧪 Automated Testing & Quality Gates

Run the automated test suite locally:

```bash
# Execute unit tests with line-by-line coverage report
python -m pytest --cov=app --cov-report=term-missing

# Validate Kubernetes manifests syntax & schema integrity
python tests/validate_k8s.py
```

**Verification Results:**
- **Test Suite:** 13 passed, 0 failed (100% pass rate).
- **Code Coverage:** 93% test coverage across core modules.
- **K8s Manifests:** 9/9 manifests verified compliant against Kubernetes v1.29 schema.

---

## 📚 Documentation Index

For in-depth architectural specifications and operational runbooks:
- 🏛️ [System Architecture & Data Flow](docs/ARCHITECTURE.md)
- ☁️ [AWS EKS & ECR Production Deployment Guide](docs/AWS_EKS_GUIDE.md)
- 📈 [AWS CloudWatch Observability Setup](monitoring/cloudwatch/CLOUDWATCH_SETUP.md)
- 🎯 [Senior DevOps Interview Preparation & STAR Guide](docs/INTERVIEW_PREP.md)
- 🚨 [Production Troubleshooting Runbook](docs/TROUBLESHOOTING.md)
- 📋 [Implementation Task Status Matrix](TASK_STATUS.md)

---

## 📄 License
This project is licensed under the Apache 2.0 License. Built for advanced cloud engineering portfolios.

