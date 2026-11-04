# AWS EKS & ECR Production Deployment Runbook

This guide describes how to deploy **CloudPulse** to Amazon Elastic Kubernetes Service (EKS) and Amazon Elastic Container Registry (ECR) following AWS Well-Architected Framework guidelines.

> [!IMPORTANT]
> Local development does NOT require AWS credentials or cloud infrastructure. AWS deployment is completely optional and should only be provisioned when production verification is needed.

---

## 1. Prerequisites
- **AWS CLI v2** configured with necessary administrative permissions.
- **eksctl** installed (`v0.170.0+`).
- **kubectl** installed and matched to EKS Kubernetes version (`v1.29+`).
- **Helm v3** installed for controller installations.

---

## 2. Step-by-Step Provisioning

### Step 2.1: Create Amazon ECR Repository with Security Scanning
```bash
aws ecr create-repository \
    --repository-name cloudpulse-platform \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --region us-east-1
```

### Step 2.2: Provision Amazon EKS Cluster
Use `eksctl` with managed node groups across two Availability Zones:

```bash
eksctl create cluster \
    --name cloudpulse-eks-cluster \
    --region us-east-1 \
    --nodegroup-name standard-workers \
    --node-type t3.medium \
    --nodes 2 \
    --nodes-min 2 \
    --nodes-max 4 \
    --managed \
    --with-oidc
```

### Step 2.3: Configure IAM Roles for Service Accounts (IRSA)
Enable pods to assume IAM roles without long-lived credentials:

```bash
# 1. Create IAM Policy for CloudWatch Log & Metric Ingestion
aws iam create-policy \
    --policy-name CloudPulseAppPolicy \
    --policy-document file://monitoring/cloudwatch/amazon-cloudwatch-agent.json

# 2. Bind IAM Role to Kubernetes ServiceAccount
eksctl create iamserviceaccount \
    --name cloudpulse-serviceaccount \
    --namespace cloudpulse \
    --cluster cloudpulse-eks-cluster \
    --role-name CloudPulseEksAppRole \
    --attach-policy-arn arn:aws:iam::<YOUR_ACCOUNT_ID>:policy/CloudPulseAppPolicy \
    --approve
```

### Step 2.4: Install AWS Load Balancer Controller
```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system \
    --set clusterName=cloudpulse-eks-cluster \
    --set serviceAccount.create=false \
    --set serviceAccount.name=aws-load-balancer-controller
```

### Step 2.5: Deploy Application Manifests
```bash
# Deploy all manifests
./scripts/linux/deploy.sh
```

---

## 3. Cost-Optimization & Teardown

To avoid incurring AWS charges when testing concludes, run:

```bash
# 1. Delete Kubernetes Ingress & Service to decommission ALB
kubectl delete -f k8s/08-ingress.yaml
kubectl delete -f k8s/04-service.yaml

# 2. Delete EKS Cluster & Node Groups
eksctl delete cluster --name cloudpulse-eks-cluster --region us-east-1

# 3. Delete ECR Repository
aws ecr delete-repository --repository-name cloudpulse-platform --force --region us-east-1
```

