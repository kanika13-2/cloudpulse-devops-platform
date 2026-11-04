# CLOUDPULSE: System Architecture & Design Specification

## 1. Executive Architecture Summary

**CloudPulse** is an enterprise-grade cloud-native platform demonstrating production-hardened DevOps automation, resilience engineering, and hybrid cloud observability across AWS, Kubernetes, Docker, and Linux/Windows development environments.

```mermaid
flowchart TD
    subgraph Traffic_Ingress ["Edge & Traffic Ingress"]
        Client[External Clients / Mobile / Web]
        ALB["AWS Application Load Balancer (ALB) / Ingress Controller"]
        Client -->|HTTPS :443| ALB
    end

    subgraph EKS_Cluster ["Amazon EKS Cluster (Namespace: cloudpulse)"]
        K8s_Svc["K8s ClusterIP Service :80"]
        ALB -->|Forward Traffic| K8s_Svc

        subgraph Pods ["Application Pod Replicas (HPA 2..10)"]
            Pod1["Pod 1: CloudPulse API\n(Non-Root UID: 10001)"]
            Pod2["Pod 2: CloudPulse API\n(Non-Root UID: 10001)"]
            PodN["Pod N: Scaled Replicas..."]
        end

        K8s_Svc --> Pod1
        K8s_Svc --> Pod2
        K8s_Svc -.-> PodN

        subgraph Observability_In_Cluster ["Telemetry Ingestion"]
            Prom["Prometheus Server\n(Scrapes :8000/metrics)"]
            Graf["Grafana Dashboard :3000\n(Provisioned Analytics)"]
            FluentBit["AWS for Fluent Bit\n(DaemonSet JSON Harvester)"]
        end

        Prom -.->|Scrapes /metrics| Pod1
        Prom -.->|Scrapes /metrics| Pod2
        Graf -->|Queries PromQL| Prom
        FluentBit -.->|Streams Container stdout| Pod1
        FluentBit -.->|Streams Container stdout| Pod2
    end

    subgraph AWS_Cloud ["AWS Managed Services"]
        ECR["Amazon Elastic Container Registry (ECR)"]
        IAM_OIDC["IAM Identity Provider (OIDC / IRSA)"]
        CW_Logs["AWS CloudWatch Logs\n/aws/eks/cloudpulse/application"]
        CW_Metrics["AWS CloudWatch Metrics & Alarms"]
        SNS["Amazon SNS Alerts Topic"]

        FluentBit -->|Encrypted HTTPS| CW_Logs
        CW_Logs --> CW_Metrics
        CW_Metrics -->|Threshold Breached| SNS
    end

    subgraph CI_CD ["Automated CI/CD Pipeline (GitHub Actions)"]
        Dev[DevOps Engineer]
        GHA["GitHub Actions Workflow"]
        Dev -->|Git Push / PR| GHA
        GHA -->|1. Pytest Unit Tests| GHA
        GHA -->|2. Docker Multi-Stage Build| GHA
        GHA -->|3. K8s Manifest Linting| GHA
        GHA -->|4. Authenticate via OIDC| IAM_OIDC
        GHA -->|5. Push Image| ECR
        GHA -->|6. Rolling Update| EKS_Cluster
    end
```

---

## 2. Component Breakdown

### 2.1 Core Application Layer
- **Framework:** Python 3.12+ with FastAPI.
- **Asynchronous Architecture:** Native ASGI with Uvicorn.
- **Correlation ID Middleware:** Automatically attaches or propagates `X-Correlation-ID` across every HTTP request and context thread, ensuring distributed traceability.
- **Structured JSON Logging:** Outputs machine-parseable JSON logs in production, designed for direct consumption by CloudWatch Logs Insights.

### 2.2 Containerization & Security Hardening
- **Base Image:** Minimal `python:3.12-slim`.
- **Multi-Stage Build:** Dependencies compiled in builder stage; runtime image contains zero build compilers, slashing image size by 70%.
- **Unprivileged User:** Execution locked to user `cloudpulse` (UID 10001, GID 10001) with `readOnlyRootFilesystem` and all Linux capabilities dropped (`drop: ["ALL"]`).
- **Health Checks:** Native Docker `HEALTHCHECK` probing `/health`.

### 2.3 Kubernetes Orchestration & Resiliency
- **High Availability:** Minimum 2 replicas managed by a Deployment with `maxSurge: 1` and `maxUnavailable: 0` for zero-downtime rolling upgrades.
- **Probes:**
  - **Startup Probe:** Accommodates initial cold starts.
  - **Liveness Probe:** Detects process hangs or internal deadlocks.
  - **Readiness Probe:** Validates host CPU and memory before admitting traffic.
- **Auto-Scaling:** Horizontal Pod Autoscaler (HPA v2) scaling up to 10 replicas when average CPU exceeds 70% or memory exceeds 80%.
- **Pod Disruption Budget:** Enforces `minAvailable: 1` to withstand cluster node draining and AWS EKS upgrades.

### 2.4 AWS IAM & OpenID Connect (IRSA)
- Zero permanent AWS Access Keys stored in repositories or cluster secrets.
- **GitHub Actions:** Assumes IAM role via OpenID Connect (OIDC) token exchange.
- **Pod ServiceAccount:** Leverages AWS IAM Roles for Service Accounts (IRSA) to grant least-privilege permissions to write to CloudWatch.

