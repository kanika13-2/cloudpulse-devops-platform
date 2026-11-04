# CLOUDPULSE: Senior DevOps & Cloud Engineer Interview Guide

This guide prepares engineers to present **CloudPulse** in technical interviews for Senior DevOps, Cloud Architect, and Site Reliability Engineer (SRE) roles.

---

## 🎯 Project Elevator Pitch (30-Second Summary)

> *"CloudPulse is an enterprise cloud infrastructure and intelligent DevOps automation platform. I built it to demonstrate end-to-end cloud-native engineering: a high-concurrency FastAPI microservice containerized with multi-stage non-root Docker builds, orchestrated on Kubernetes with Horizontal Pod Autoscaling and Pod Disruption Budgets, monitored via dual-plane observability using Prometheus/Grafana alongside AWS CloudWatch Container Insights, and delivered through an automated GitHub Actions CI/CD pipeline leveraging AWS OIDC federated authentication."*

---

## 🌟 STAR Method Architecture Deep Dive

### Situation:
In production environments, cloud applications frequently suffer from configuration drift, deployment downtime, hardcoded credentials, and fragmented observability where application logs cannot be correlated with infrastructure metrics or load spikes.

### Task:
Design and build an automated cloud platform that guarantees:
1. Zero-downtime rolling updates.
2. Least-privilege, keyless AWS authentication.
3. Automated horizontal autoscaling under simulated load.
4. Unified tracing and telemetry using distributed correlation IDs.
5. Seamless cross-platform compatibility across Windows and Linux.

### Action:
- **Application & Observability:** Implemented an asynchronous FastAPI microservice with custom Prometheus collectors and structured JSON logging. Injected correlation IDs via middleware to trace requests from ingress to CloudWatch Logs Insights.
- **Security & Hardening:** Designed a multi-stage Docker build running under an unprivileged user (`UID 10001`), dropping all Linux capabilities, and configured Docker health checks.
- **Orchestration:** Engineered Kubernetes manifests with 2 replicas, rolling update strategy (`maxSurge: 1`, `maxUnavailable: 0`), HPA v2 autoscaling (CPU & Memory), startup/liveness/readiness probes, and PodDisruptionBudgets.
- **CI/CD & IAM:** Created a GitHub Actions pipeline using AWS OIDC role assumption, building and scanning container images, linting Kubernetes schemas, and pushing to Amazon ECR.
- **Automation & Disaster Recovery:** Authored native Linux Bash and Windows PowerShell scripts providing automated health checks, synthetic traffic load generation, and one-command rollout rollbacks.

### Result:
Delivered a 100% test-covered cloud platform capable of handling automated traffic spikes, self-healing from pod crashes within seconds, rolling back bad revisions with zero downtime, and providing unified dashboards across Grafana and CloudWatch.

---

## 💡 Top 10 Technical Interview Questions & Answers

### 1. How do you guarantee zero-downtime rolling updates in Kubernetes?
**Answer:**
We configure the Deployment rolling update strategy with `maxSurge: 1` and `maxUnavailable: 0`. This ensures Kubernetes spins up and verifies a new replica before terminating an old one. Furthermore:
- We implement a **Readiness Probe** (`/health?probe_type=readiness`) so traffic is only routed after the container is fully initialized.
- We configure a **`preStop` lifecycle hook** (`sleep 5`) to give kube-proxy and AWS ALB ingress controllers time to deregister the endpoint before the container receives `SIGTERM`.

### 2. Why use AWS IAM Roles for Service Accounts (IRSA) instead of Node Instance Profiles or static AWS credentials?
**Answer:**
Node Instance Profiles grant permissions to every pod running on that EC2 worker node, violating the principle of least privilege. Static AWS Access Keys introduce credential leak risks and maintenance overhead.
**IRSA** uses OpenID Connect (OIDC) federation: Kubernetes projects a signed service account token into the pod volume. The AWS SDK exchanges this token with AWS STS for temporary credentials scoped strictly to that specific Pod's IAM role.

### 3. How does GitHub Actions authenticate to AWS ECR and EKS without stored secrets?
**Answer:**
We configure an AWS IAM OpenID Connect (OIDC) Identity Provider matching `token.actions.githubusercontent.com`. In GitHub Actions, we request an `id-token: write` permission. The `aws-actions/configure-aws-credentials` action exchanges GitHub's OIDC JWT token with AWS STS (`sts:AssumeRoleWithWebIdentity`), obtaining temporary 1-hour credentials. Zero access keys or static secrets exist in GitHub Secrets.

### 4. How did you design the observability stack between Prometheus and AWS CloudWatch?
**Answer:**
We adopted a dual-plane observability model:
- **In-Cluster Fast Metrics:** Prometheus scrapes the `/metrics` endpoint every 5s, feeding real-time Grafana dashboards for cluster-level diagnostics (p50/p95/p99 latency, request rates, memory RSS).
- **Enterprise AWS Centralization:** Container logs are streamed in JSON format by AWS for Fluent Bit to CloudWatch Logs Group `/aws/eks/cloudpulse/application`. CloudWatch Metric Alarms monitor high CPU (>80%), 5xx errors, and pod restarts, notifying on-call engineers via Amazon SNS.

### 5. What is the role of the Correlation ID in this platform?
**Answer:**
Distributed requests often fail across complex microservice boundaries. Our correlation ID middleware extracts `X-Correlation-ID` from incoming requests or generates a UUIDv4, binding it to Python's asynchronous `contextvars`. Every log entry emitted by the service includes this ID. In CloudWatch Logs Insights, an engineer can query a single correlation ID to view the full request lifecycle from ingress to error traceback.

### 6. What makes the Dockerfile production-ready and secure?
**Answer:**
1. **Multi-Stage Build:** Python packages are compiled in a `builder` image; only the runtime virtual environment is copied to `runner`, reducing image size and stripping build tools (compilers, git).
2. **Non-Root Execution:** A dedicated user `cloudpulse` with explicit UID/GID 10001 owns and runs the process.
3. **Security Directives:** In Kubernetes, `allowPrivilegeEscalation: false` and `capabilities.drop: ["ALL"]` are enforced.
4. **Health Check:** Native Docker `HEALTHCHECK` tests `/health` at 30-second intervals.

### 7. How does the Horizontal Pod Autoscaler (HPA) make scaling decisions?
**Answer:**
HPA v2 queries the Kubernetes Metrics Server. When average CPU utilization across pods exceeds 70% or memory exceeds 80%, HPA calculates:
$$\text{Desired Replicas} = \left\lceil \text{Current Replicas} \times \left( \frac{\text{Current Metric Value}}{\text{Target Metric Value}} \right) \right\rceil$$
We also implemented custom scale-down stabilization policies (`stabilizationWindowSeconds: 300`) to prevent rapid thrashing/flapping during variable workloads.

### 8. What is the significance of the Pod Disruption Budget (PDB)?
**Answer:**
When an EKS node is drained during node group updates, security patching, or cluster scaling, Kubernetes might evict pods. With `minAvailable: 1`, the Kubernetes eviction API refuses to evict a pod if doing so would cause active replicas to fall below 1, guaranteeing high availability during infrastructure maintenance.

### 9. How does the health check differentiate between liveness and readiness?
**Answer:**
- **Liveness (`/health?probe_type=liveness`):** Checks if the process is responsive and not deadlocked. Even under high load, liveness returns 200 OK so Kubernetes does not needlessly restart the container.
- **Readiness (`/health?probe_type=readiness`):** Checks if memory, CPU, or dependent resources exceed capacity. If overloaded, readiness returns HTTP 503, instructing Kubernetes to temporarily stop routing incoming traffic until resources normalize.

### 10. How did you validate that automated rollback works?
**Answer:**
We tested deploying an invalid image tag to the cluster. When `kubectl rollout status` timed out or detected failure, our automated rollback scripts (`scripts/linux/rollback.sh` and `scripts/windows/rollback.ps1`) executed `kubectl rollout undo deployment/cloudpulse-api -n cloudpulse`, restored the previous revision, and ran `/health` probes to verify 100% service recovery.

