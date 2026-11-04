# CLOUDPULSE: Production Troubleshooting Runbook

This runbook provides incident response steps and diagnostic commands for common failure modes across Docker, Kubernetes, AWS, and CI/CD.

---

## 🚨 Incident Triage Decision Matrix

| Symptom | Root Cause | Immediate Diagnostic Command | Remediation Action |
| :--- | :--- | :--- | :--- |
| **`ImagePullBackOff`** | Invalid tag, missing ECR credentials, or private repo access | `kubectl describe pod -n cloudpulse <pod-name>` | Verify ECR repo URI, check IRSA permissions, or ensure image was pushed |
| **`CrashLoopBackOff`** | Container unhandled exception or port conflict | `kubectl logs -n cloudpulse <pod-name> --previous` | Check startup error in logs, ensure configmap environment variables are set |
| **`503 Service Unavailable`** | Readiness probe failure due to memory/CPU overload | `curl -i http://<pod-ip>:8000/health?probe_type=readiness` | Check pod resource requests/limits; scale up deployment replicas |
| **HPA Target Unknown** | Kubernetes Metrics Server not running in cluster | `kubectl get apiservices \| grep metrics` | Deploy Metrics Server: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml` |
| **ALB Ingress 502 Bad Gateway** | Target group health check path misconfigured or timeout | `aws elbv2 describe-target-health --target-group-arn <arn>` | Ensure target group health check path is `/health` and port is 8000 |
| **OIDC AssumeRoleWithWebIdentity Error** | GitHub Actions branch or repository mismatch in trust policy | Review GitHub Actions step `Configure AWS Credentials` | Verify IAM Role Trust Relationship `aud` and `sub` claims match `repo:<org>/<repo>:ref:refs/heads/main` |

---

## Detailed Triage Procedures

### 1. Pod Fails Readiness Probe
If a pod is stuck in `Running` but `READY 0/1`:

```bash
# 1. Inspect recent events and failure reason
kubectl describe pod -n cloudpulse -l app.kubernetes.io/name=cloudpulse-api

# 2. Port-forward directly to the affected pod
kubectl port-forward -n cloudpulse pod/<pod-name> 8000:8000

# 3. Query the probe endpoint locally
curl -v http://localhost:8000/health?probe_type=readiness
```

**Common Causes:**
- Host memory utilization exceeded `MAX_MEMORY_PERCENT_THRESHOLD`.
- Slow application boot time exceeding `startupProbe` threshold. Increase `failureThreshold` in `k8s/03-deployment.yaml`.

---

### 2. Emergency Rollback of Failed Deployment
If a deployment exhibits regressions in production:

```bash
# Linux
./scripts/linux/rollback.sh

# Windows
.\scripts\windows\rollback.ps1
```

---

### 3. Diagnosing CloudWatch Logs Streaming Issues
If container logs are not appearing in `/aws/eks/cloudpulse/application`:

```bash
# 1. Check Fluent Bit pod logs in amazon-cloudwatch namespace
kubectl logs -n amazon-cloudwatch -l k8s-app=fluent-bit --tail=50

# 2. Verify IAM Role annotation on Fluent Bit service account
kubectl get sa fluent-bit -n amazon-cloudwatch -o yaml | grep eks.amazonaws.com/role-arn

# 3. Test CloudWatch Logs API directly using AWS CLI
aws logs describe-log-streams \
    --log-group-name "/aws/eks/cloudpulse/application" \
    --region us-east-1
```

