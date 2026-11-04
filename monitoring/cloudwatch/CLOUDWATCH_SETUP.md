# AWS CloudWatch Enterprise Observability Integration Guide

This guide details how **CloudPulse** connects to **AWS CloudWatch** for enterprise telemetry, log aggregation, Prometheus metrics ingestion, and automated alerting.

---

## 🏛️ Observability Architecture

```
+---------------------------------------------------------------------------------+
|                                 AMAZON EKS / EC2                                |
|                                                                                 |
|   +--------------------------+           +----------------------------------+   |
|   |   CloudPulse FastAPI     |           |     AWS for Fluent Bit           |   |
|   |  - JSON Structured Logs  | --------> |  - Tunnels stdout container logs |   |
|   |  - Correlation ID        |           |  - Parses JSON timestamp & level |   |
|   |  - /metrics Endpoint     |           +-----------------+----------------+   |
|   +------------+-------------+                             |                    |
|                |                                           |                    |
|                v                                           v                    |
|   +--------------------------+              [AWS CloudWatch Logs Group]         |
|   | CloudWatch Agent / EMF   |              /aws/eks/cloudpulse/application     |
|   | - Scrapes /metrics       |                             |                    |
|   | - Emits CloudWatch EMF   |                             |                    |
|   +------------+-------------+                             |                    |
+----------------|-------------------------------------------|--------------------+
                 v                                           v
    [CloudWatch Custom Metrics]                 [CloudWatch Logs Insights]
    Namespace: CloudPulse/Application           Query by: correlation_id
                 |                                           |
                 +-------------------+-----------------------+
                                     |
                                     v
                        [CloudWatch Metric Alarms]
                        - High CPU (>80%)
                        - 5xx Error Spike (>5)
                        - Target Unhealthy Count (>=1)
                        - Pod Restarts (>2)
                                     |
                                     v
                         [Amazon SNS Notification]
                         DevOps On-Call (Slack / PagerDuty)
```

---

## 1. Amazon EKS Integration (Container Insights & Fluent Bit)

### Step 1: Enable CloudWatch Container Insights on EKS
Run the following AWS CLI command to enable automated performance metrics for your cluster:

```bash
aws eks update-cluster-config \
    --region us-east-1 \
    --name cloudpulse-eks-cluster \
    --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'
```

### Step 2: Deploy AWS for Fluent Bit DaemonSet
Deploy the provided ConfigMap and Fluent Bit DaemonSet to harvest application JSON logs:

```bash
# Create amazon-cloudwatch namespace if not existing
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest_legacy/k8s-deployment-manifest/cloudwatch-namespace.yaml

# Apply CloudPulse Fluent Bit parser configuration
kubectl apply -f monitoring/cloudwatch/fluent-bit-configmap.yaml
```

---

## 2. CloudWatch IAM Least-Privilege Policy

To adhere to AWS security best practices, the CloudWatch Agent / Fluent Bit ServiceAccount must be bound to an IAM Role using IRSA (`eks.amazonaws.com/role-arn`) with the following minimal policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogsIngestion",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams",
        "logs:DescribeLogGroups"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/aws/eks/cloudpulse/*"
    },
    {
      "Sid": "CloudWatchMetricsPublishing",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": [
            "CloudPulse/Application",
            "ContainerInsights"
          ]
        }
      }
    }
  ]
}
```

---

## 3. Provisioning CloudWatch Alarms

Use the AWS CLI or Terraform to deploy the pre-configured alarm definitions:

```bash
# Deploy alarms from configuration file
aws cloudwatch put-metric-alarm \
    --cli-input-json file://monitoring/cloudwatch/cloudwatch-alarms.json
```

---

## 4. CloudWatch Logs Insights Runbook Queries

### Trace Request by Correlation ID:
```sql
fields @timestamp, level, service, correlation_id, message, source
| filter correlation_id = "9e2b102b-a01c-4b5c-a5b6-c6eb3c042e6f"
| sort @timestamp asc
```

### Find All 5xx Errors and Exceptions:
```sql
fields @timestamp, extra_fields.status_code, message, correlation_id, exception
| filter extra_fields.status_code >= 500 or level = "ERROR"
| sort @timestamp desc
| limit 50
```

### Compute 95th Percentile Request Duration:
```sql
filter ispresent(extra_fields.duration_ms)
| stats pct(extra_fields.duration_ms, 95) as p95_latency_ms by bin(5m)
```

