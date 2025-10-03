# TradeQuest AWS Deployment Guide

## 🎯 Current Deployment Status

### ✅ Fully Operational
- **Backend API**: `https://tradequest.tech/api/v1/*`
- **Database**: AWS RDS PostgreSQL (db.t3.small)
- **Cache**: AWS ElastiCache Redis (cache.t3.micro)
- **Storage**: AWS S3 bucket with lifecycle policies
- **Infrastructure**: Fully provisioned via Terraform
- **CI/CD**: GitHub Actions configured with TA-Lib support

### ⚠️ In Progress
- **Frontend**: Next.js standalone deployment experiencing initialization hang in ECS Fargate
- **Root Cause**: DNS/hostname resolution issue causing `node server.js` to block silently
- **Status**: Image works perfectly locally, investigating AWS-specific environment constraints

---

## 📋 Architecture Overview

```
Internet
    ↓
Route 53 (tradequest.tech)
    ↓
Application Load Balancer (HTTPS/443, HTTP/80)
    ↓
    ├─→ Backend Target Group (port 8000)
    │   └─→ ECS Fargate Tasks (FastAPI)
    │       ├─→ RDS PostgreSQL
    │       ├─→ ElastiCache Redis
    │       └─→ S3 Bucket
    │
    └─→ Frontend Target Group (port 3000)
        └─→ ECS Fargate Tasks (Next.js) [TROUBLESHOOTING]
```

### AWS Resources

| Resource | Configuration | Status |
|----------|--------------|---------|
| **VPC** | `vpc-075a381a1bc3de919` | ✅ Active |
| **Subnets** | 2 public, 2 private, 2 database | ✅ Active |
| **NAT Gateway** | 2 (high availability) | ✅ Active |
| **Load Balancer** | Application LB | ✅ Active |
| **RDS** | PostgreSQL 15.14, db.t3.small | ✅ Active |
| **ElastiCache** | Redis 7.1, cache.t3.micro | ✅ Active |
| **S3** | Versioned, encrypted | ✅ Active |
| **ECS Cluster** | `tradequest-cluster` | ✅ Active |
| **Backend Service** | 1 task, 512 CPU / 1024 MB | ✅ Healthy |
| **Frontend Service** | 1 task, 512 CPU / 1024 MB | ⚠️ Unhealthy |

---

## 🚀 Deployment Process

### Prerequisites
1. **AWS CLI** installed and configured
2. **Terraform** installed (v1.0+)
3. **Docker** installed and running
4. **AWS Account** with appropriate permissions
5. **Domain** configured in Route 53 (tradequest.tech)

### Initial Setup

```bash
# 1. Configure AWS credentials
aws configure
# Use your AWS Access Key ID and Secret Access Key

# 2. Initialize Terraform
cd aws/terraform
terraform init

# 3. Review and customize terraform.tfvars
# Update values as needed for your environment

# 4. Create infrastructure
terraform plan
terraform apply

# 5. Configure secrets in AWS Secrets Manager
# Backend secrets, database credentials, API keys, etc.
```

### Building and Pushing Docker Images

#### Backend Image
```bash
# Build backend
cd backend
docker build -t tradequest-backend .

# Tag for ECR
docker tag tradequest-backend:latest \
  759316875712.dkr.ecr.us-east-1.amazonaws.com/tradequest-prod-backend:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  759316875712.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 759316875712.dkr.ecr.us-east-1.amazonaws.com/tradequest-prod-backend:latest
```

#### Frontend Image
```bash
# Build frontend (standalone mode)
cd frontend
docker build -t tradequest-frontend .

# Tag for ECR
docker tag tradequest-frontend:latest \
  759316875712.dkr.ecr.us-east-1.amazonaws.com/tradequest-prod-frontend:latest

# Push to ECR
docker push 759316875712.dkr.ecr.us-east-1.amazonaws.com/tradequest-prod-frontend:latest
```

### Deploying Updates

```bash
# Force new deployment of backend
aws ecs update-service \
  --cluster tradequest-cluster \
  --service tradequest-prod-backend \
  --force-new-deployment \
  --region us-east-1

# Force new deployment of frontend
aws ecs update-service \
  --cluster tradequest-cluster \
  --service tradequest-prod-frontend \
  --force-new-deployment \
  --region us-east-1
```

---

## 🔍 Monitoring and Debugging

### Viewing Logs

```bash
# Backend logs
aws logs tail /ecs/tradequest-prod-backend \
  --follow \
  --region us-east-1

# Frontend logs
aws logs tail /ecs/tradequest-prod-frontend \
  --follow \
  --region us-east-1

# Filter for errors
aws logs tail /ecs/tradequest-prod-backend \
  --since 10m \
  --filter-pattern "ERROR" \
  --region us-east-1
```

### Checking Service Status

```bash
# List running tasks
aws ecs list-tasks \
  --cluster tradequest-cluster \
  --service-name tradequest-prod-backend \
  --region us-east-1

# Describe service
aws ecs describe-services \
  --cluster tradequest-cluster \
  --services tradequest-prod-backend tradequest-prod-frontend \
  --region us-east-1

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:759316875712:targetgroup/tradequest-prod-backend-tg/7ae04c06ad7fc325 \
  --region us-east-1
```

### ECS Task Debugging

```bash
# Get task details
aws ecs describe-tasks \
  --cluster tradequest-cluster \
  --tasks <task-id> \
  --region us-east-1

# Check task events
aws ecs describe-services \
  --cluster tradequest-cluster \
  --services tradequest-prod-backend \
  --region us-east-1 \
  --query 'services[0].events[0:10]'
```

---

## 🐛 Current Issue: Frontend Deployment

### Problem Description

The Next.js standalone server starts successfully in local Docker but hangs during initialization in AWS ECS Fargate without producing logs or error messages.

### Technical Details

**Symptoms**:
- Container status: `RUNNING`
- Last log: `Running: node server.js`
- No subsequent output (no "Ready" message)
- Load balancer health checks: `Target.Timeout`
- Process doesn't crash, just hangs indefinitely

**Environment Comparison**:

| Aspect | Local (✅ Works) | ECS Fargate (❌ Hangs) |
|--------|-----------------|------------------------|
| Output | `✓ Ready in 42ms` | [No output after start] |
| Health Check | Responds immediately | Times out |
| DNS | Host DNS resolver | VPC DNS (169.254.169.253) |
| Hostname | Container ID | ECS-generated hostname |
| Network Mode | Bridge | awsvpc (dedicated ENI) |

**Root Cause Analysis**:

Next.js standalone server (`node server.js`) is making a **blocking network call** during initialization, likely:

1. **DNS Lookup**: Attempting to resolve `localhost` or container hostname
2. **Server Binding**: `server.listen(3000, 'localhost')` blocks on hostname resolution
3. **Silent Timeout**: No error thrown, just infinite wait

**Evidence**:
```javascript
// Next.js likely does this:
const hostname = process.env.HOSTNAME || 'localhost'
server.listen(port, hostname, () => {
  console.log(`Ready on http://${hostname}:${port}`) // Never reached
})
```

If `localhost` doesn't resolve properly in Fargate's DNS environment, the callback never fires.

### Attempted Solutions

1. ✅ **Increased Resources**: 256→512 CPU, 512→1024 MB memory
2. ✅ **Removed Container Health Check**: Rely only on ALB health checks
3. ✅ **Added NODE_ENV=production**: Ensure production mode
4. ✅ **Standalone Output Mode**: Configured `output: 'standalone'` in next.config.js
5. ✅ **Optimized Dockerfile**: Multi-stage build with proper file copies
6. ⏳ **Testing HOSTNAME=0.0.0.0**: Bind to all interfaces (pending)

### Proposed Fixes

**Option 1: Set HOSTNAME Environment Variable** (Recommended)
```hcl
# In aws/terraform/ecs.tf
environment = [
  {
    name  = "HOSTNAME"
    value = "0.0.0.0"  # Bind to all interfaces
  }
]
```

**Option 2: Modify Next.js Start Command**
```dockerfile
# In frontend/Dockerfile
CMD ["node", "server.js", "--hostname", "0.0.0.0"]
```

**Option 3: Use IPv6 Binding**
```dockerfile
ENV HOSTNAME=::
```

**Option 4: Debug with Strace**
```dockerfile
# Temporary debug Dockerfile
RUN apk add --no-cache strace
CMD ["strace", "-f", "node", "server.js"]
```

### Testing Locally vs AWS

**Local Test (Always Works)**:
```bash
docker run -p 3000:3000 tradequest-frontend
# Output: ✓ Ready in 42ms
# curl http://localhost:3000 → 200 OK
```

**AWS Test (Currently Fails)**:
```bash
# Deploy to ECS
aws ecs update-service --cluster tradequest-cluster \
  --service tradequest-prod-frontend --force-new-deployment

# Wait 2 minutes
# Check logs: Only shows "Running: node server.js", nothing after
# Health check: Target.Timeout
```

---

## 📦 GitHub Actions CI/CD

### Workflow: `.github/workflows/deploy.yml`

**Triggers**:
- Push to `main` branch
- Pull request to `main` branch

**Jobs**:
1. **Test**: Run backend/frontend tests
2. **Deploy**: Build Docker images, push to ECR, update ECS services

**Special Configuration**:
```yaml
# TA-Lib Installation (Required for Backend)
- name: Install TA-Lib
  run: |
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr
    make
    sudo make install
```

**Secrets Required**:
- `AWS_ACCESS_KEY_ID`: AWS credentials for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS credentials for deployment

---

## 🔐 Security Configuration

### Secrets Manager

**Backend Secrets** (`tradequest-prod/app`):
```json
{
  "SECRET_KEY": "...",
  "JWT_SECRET_KEY": "...",
  "OPENAI_API_KEY": "...",
  "STRIPE_SECRET_KEY": "...",
  "STRIPE_WEBHOOK_SECRET": "..."
}
```

**Database Secrets** (`tradequest-prod/database`):
```json
{
  "username": "tradequest_admin",
  "password": "...",
  "database": "tradequest",
  "host": "...",
  "port": "5432",
  "database_url": "postgresql://..."
}
```

**Redis Secrets** (`tradequest-prod/redis`):
```json
{
  "host": "...",
  "port": "6379",
  "password": "..."
}
```

### Security Groups

**ALB Security Group**:
- Ingress: 80 (HTTP), 443 (HTTPS) from 0.0.0.0/0
- Egress: All traffic

**ECS Security Group**:
- Ingress: 8000 (backend), 3000 (frontend) from ALB SG
- Egress: All traffic

**RDS Security Group**:
- Ingress: 5432 from ECS SG
- Egress: None

**Redis Security Group**:
- Ingress: 6379 from ECS SG
- Egress: None

---

## 💰 Cost Breakdown (Monthly Estimate)

| Service | Configuration | Est. Cost |
|---------|--------------|-----------|
| EC2 (NAT Gateway) | 2 x 0.045/hr + data | ~$67 |
| ECS Fargate | 2 tasks (0.5 vCPU, 1GB) | ~$30 |
| RDS PostgreSQL | db.t3.small (2vCPU, 2GB) | ~$35 |
| ElastiCache Redis | cache.t3.micro | ~$12 |
| Application Load Balancer | 1 ALB | ~$22 |
| S3 Storage | 50GB + requests | ~$3 |
| CloudWatch Logs | 5GB logs | ~$3 |
| Route 53 | Hosted zone + queries | ~$1 |
| **Total** | | **~$173/month** |

**Cost Optimization Tips**:
1. Use single NAT Gateway instead of 2 (HA tradeoff): Save ~$35/month
2. Reduce RDS to db.t3.micro: Save ~$20/month
3. Enable S3 lifecycle policies for old data
4. Set CloudWatch log retention to 7 days

---

## 🔄 Update Workflow

### Code Changes

```bash
# 1. Make changes locally
git checkout -b feature/my-feature

# 2. Test locally
docker-compose up

# 3. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature

# 4. Create PR → GitHub Actions runs tests

# 5. Merge to main → Auto-deploys to AWS
```

### Infrastructure Changes

```bash
# 1. Update Terraform files
cd aws/terraform
vim ecs.tf  # Make changes

# 2. Plan changes
terraform plan

# 3. Apply changes
terraform apply

# 4. Verify deployment
aws ecs describe-services ...
```

### Database Migrations

```bash
# 1. SSH into ECS task (or run locally against RDS)
aws ecs execute-command \
  --cluster tradequest-cluster \
  --task <task-id> \
  --container backend \
  --interactive \
  --command "/bin/sh"

# 2. Run Alembic migrations
alembic upgrade head

# 3. Verify
alembic current
```

---

## 🆘 Troubleshooting

### Backend Not Responding

```bash
# Check if tasks are running
aws ecs list-tasks --cluster tradequest-cluster --service-name tradequest-prod-backend

# Check logs for errors
aws logs tail /ecs/tradequest-prod-backend --follow

# Check target health
aws elbv2 describe-target-health --target-group-arn <backend-tg-arn>

# Common issues:
# - Database connection failure → Check RDS security group
# - Missing secrets → Verify Secrets Manager
# - Out of memory → Increase task memory in terraform.tfvars
```

### Frontend Hanging (Current Issue)

```bash
# Check task status
aws ecs describe-tasks --cluster tradequest-cluster --tasks <task-id>

# View initialization logs
aws logs tail /ecs/tradequest-prod-frontend --since 5m

# Look for:
# - "Running: node server.js" → Confirms container started
# - No "Ready" message → Confirms hang
# - No error messages → Confirms silent failure

# Next steps:
# 1. Try HOSTNAME=0.0.0.0 environment variable
# 2. Use strace to debug blocking call
# 3. Consider alternative deployment (App Runner, Lambda)
```

### Database Connection Issues

```bash
# Test connection from ECS task
aws ecs execute-command \
  --cluster tradequest-cluster \
  --task <task-id> \
  --container backend \
  --command "psql $DATABASE_URL -c 'SELECT 1'"

# Check security groups
aws ec2 describe-security-groups --group-ids <rds-sg-id>

# Verify secrets
aws secretsmanager get-secret-value --secret-id tradequest-prod/database
```

### High Costs

```bash
# Check NAT Gateway data transfer
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --start-time 2025-10-01T00:00:00Z \
  --end-time 2025-10-03T23:59:59Z \
  --period 86400 \
  --statistics Sum

# Check ECS task CPU/memory usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterName,Value=tradequest-cluster

# Identify optimization opportunities
```

---

## 📚 Additional Resources

- [Next.js Standalone Output](https://nextjs.org/docs/app/api-reference/next-config-js/output)
- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/intro.html)
- [Fargate Troubleshooting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

---

## ✅ Quick Health Check

```bash
# Backend
curl https://tradequest.tech/api/v1/health
# Expected: {"status":"healthy"}

# Frontend (when fixed)
curl https://tradequest.tech
# Expected: HTML with TradeQuest content

# Database
aws rds describe-db-instances --db-instance-identifier tradequest-prod-postgres
# Expected: Status = "available"

# Redis
aws elasticache describe-replication-groups --replication-group-id tradequest-prod-redis
# Expected: Status = "available"
```

---

**Last Updated**: October 3, 2025  
**Deployment Version**: Backend v1.0 (Stable), Frontend v1.0 (Troubleshooting)  
**Next Steps**: Resolve frontend initialization hang with HOSTNAME environment variable

