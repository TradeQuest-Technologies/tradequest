# 📚 TradeQuest AWS Operations Guide

Complete guide for managing, updating, monitoring, and troubleshooting your AWS deployment.

## 🚀 Pushing Updates to AWS

### Quick Update Process

```bash
# 1. Make your code changes
# 2. Commit your changes
git add .
git commit -m "Your update description"
git push origin main

# 3. Deploy the changes
./scripts/deploy.sh full
```

### Step-by-Step Update Process

#### 1. **Code Changes Only** (No Infrastructure Changes)

```bash
# Navigate to your project
cd /path/to/Aggregator

# Make your changes to backend or frontend code
# ...

# Build and push new Docker images
./scripts/deploy.sh images

# Update running services
./scripts/deploy.sh services
```

#### 2. **Database Schema Changes**

```bash
# Create a database migration
cd backend
alembic revision -m "Add new column to users table"

# Edit the migration file in backend/alembic/versions/
# Then deploy
cd ..
./scripts/deploy.sh services

# SSH into ECS task to run migration (or use ECS Exec)
aws ecs execute-command \
    --cluster tradequest-cluster \
    --task <task-id> \
    --container backend \
    --command "alembic upgrade head" \
    --interactive
```

#### 3. **Infrastructure Changes** (Terraform)

```bash
# Update Terraform files in aws/terraform/
# Then deploy infrastructure changes
cd aws/terraform

# Preview changes
terraform plan

# Apply changes
terraform apply

# If needed, rebuild and redeploy services
cd ../..
./scripts/deploy.sh full
```

#### 4. **Secrets/Environment Variables**

```bash
# Update secrets in AWS Secrets Manager
aws secretsmanager update-secret \
    --secret-id tradequest-prod/app \
    --secret-string '{
        "OPENAI_API_KEY": "new-key-value",
        "STRIPE_SECRET_KEY": "sk_live_..."
    }'

# Restart services to pick up new secrets
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --force-new-deployment
```

---

## 📊 Watching Logs

### CloudWatch Logs

#### View Backend Logs
```bash
# Get latest logs
aws logs tail /ecs/tradequest-prod-backend --follow

# Filter for errors
aws logs tail /ecs/tradequest-prod-backend --follow --filter-pattern "ERROR"

# Search for specific text
aws logs tail /ecs/tradequest-prod-backend --follow --filter-pattern "database"

# View logs from specific time
aws logs tail /ecs/tradequest-prod-backend --since 1h
```

#### View Frontend Logs
```bash
# Get latest logs
aws logs tail /ecs/tradequest-prod-frontend --follow

# Filter for errors
aws logs tail /ecs/tradequest-prod-frontend --follow --filter-pattern "error"
```

#### View Load Balancer Logs
```bash
# Enable ALB access logs first (one time setup)
aws elbv2 modify-load-balancer-attributes \
    --load-balancer-arn <your-alb-arn> \
    --attributes Key=access_logs.s3.enabled,Value=true \
              Key=access_logs.s3.bucket,Value=your-alb-logs-bucket
```

### CloudWatch Logs Insights

```bash
# Open CloudWatch Logs Insights in browser
echo "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights"
```

Example queries:

**Find Errors in Last Hour**
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**Find Slow API Requests**
```
fields @timestamp, @message
| filter @message like /duration/
| parse @message "duration=*ms" as duration
| filter duration > 1000
| sort duration desc
```

**Count Requests by Endpoint**
```
fields @timestamp, request_path
| stats count() by request_path
| sort count desc
```

### Real-Time Monitoring

#### Watch ECS Service Status
```bash
# Watch service status
watch -n 5 'aws ecs describe-services \
    --cluster tradequest-cluster \
    --services tradequest-prod-backend tradequest-prod-frontend \
    --query "services[*].[serviceName,status,runningCount,desiredCount]" \
    --output table'
```

#### Watch Task Health
```bash
# List running tasks
aws ecs list-tasks \
    --cluster tradequest-cluster \
    --service-name tradequest-prod-backend

# Describe a specific task
aws ecs describe-tasks \
    --cluster tradequest-cluster \
    --tasks <task-arn>
```

---

## 🔍 Monitoring & Alerts

### CloudWatch Dashboards

#### Create Custom Dashboard
```bash
# Create dashboard via AWS Console
# https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:

# Or use AWS CLI
aws cloudwatch put-dashboard \
    --dashboard-name TradeQuest-Production \
    --dashboard-body file://cloudwatch-dashboard.json
```

### Key Metrics to Monitor

1. **ECS Metrics**
   - CPU Utilization
   - Memory Utilization
   - Task count
   - Deployment status

2. **RDS Metrics**
   - Database connections
   - Read/Write IOPS
   - CPU utilization
   - Storage space

3. **Redis Metrics**
   - Cache hit rate
   - Evictions
   - Connections

4. **Load Balancer Metrics**
   - Request count
   - Target response time
   - HTTP 5xx errors
   - Healthy/Unhealthy targets

### Set Up Alerts

```bash
# Create SNS topic for alerts
aws sns create-topic --name tradequest-alerts

# Subscribe to topic (email)
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:123456789012:tradequest-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com

# Create CloudWatch alarm for high CPU
aws cloudwatch put-metric-alarm \
    --alarm-name tradequest-backend-high-cpu \
    --alarm-description "Alert when backend CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/ECS \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:123456789012:tradequest-alerts
```

---

## 🐛 Debugging Issues

### Common Issues & Solutions

#### 1. **Tasks Keep Restarting**

```bash
# Check task logs
aws logs tail /ecs/tradequest-prod-backend --since 30m

# Check task health
aws ecs describe-tasks \
    --cluster tradequest-cluster \
    --tasks <task-arn> \
    --query 'tasks[0].containers[0].healthStatus'

# Common causes:
# - Health check failing (check /health endpoint)
# - Out of memory (increase memory in task definition)
# - Database connection issues (check RDS connectivity)
```

#### 2. **Database Connection Errors**

```bash
# Check RDS status
aws rds describe-db-instances \
    --db-instance-identifier tradequest-prod-postgres

# Check security groups
aws ec2 describe-security-groups \
    --group-ids <rds-security-group-id>

# Test connection from ECS task
aws ecs execute-command \
    --cluster tradequest-cluster \
    --task <task-id> \
    --container backend \
    --command "nc -zv <rds-endpoint> 5432" \
    --interactive
```

#### 3. **High Load / Performance Issues**

```bash
# Check current scaling
aws ecs describe-services \
    --cluster tradequest-cluster \
    --services tradequest-prod-backend

# Manually scale up
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --desired-count 5

# Check slow queries in RDS
# Enable Performance Insights in RDS console
```

#### 4. **Storage Issues (S3)**

```bash
# Check S3 bucket
aws s3 ls s3://your-bucket-name/

# Check bucket size
aws s3 ls s3://your-bucket-name/ --recursive --summarize

# Test S3 access from ECS task
aws ecs execute-command \
    --cluster tradequest-cluster \
    --task <task-id> \
    --container backend \
    --command "python -c 'from app.services.storage_service import storage_service; print(storage_service.s3_bucket)'" \
    --interactive
```

---

## 🔧 Advanced Operations

### SSH into Running Container (ECS Exec)

```bash
# Enable ECS Exec (one time setup)
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --enable-execute-command

# Get task ID
TASK_ID=$(aws ecs list-tasks \
    --cluster tradequest-cluster \
    --service-name tradequest-prod-backend \
    --query 'taskArns[0]' --output text)

# Connect to container
aws ecs execute-command \
    --cluster tradequest-cluster \
    --task $TASK_ID \
    --container backend \
    --command "/bin/bash" \
    --interactive
```

### Database Operations

#### Run Database Migrations
```bash
# From ECS task
aws ecs execute-command \
    --cluster tradequest-cluster \
    --task <task-id> \
    --container backend \
    --command "alembic upgrade head" \
    --interactive

# Or create a one-off task
aws ecs run-task \
    --cluster tradequest-cluster \
    --task-definition tradequest-prod-backend \
    --launch-type FARGATE \
    --overrides '{
        "containerOverrides": [{
            "name": "backend",
            "command": ["alembic", "upgrade", "head"]
        }]
    }'
```

#### Database Backup
```bash
# Create manual snapshot
aws rds create-db-snapshot \
    --db-instance-identifier tradequest-prod-postgres \
    --db-snapshot-identifier manual-backup-$(date +%Y%m%d-%H%M%S)

# List snapshots
aws rds describe-db-snapshots \
    --db-instance-identifier tradequest-prod-postgres
```

#### Restore from Backup
```bash
# Restore to new instance
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier tradequest-restored \
    --db-snapshot-identifier <snapshot-id>
```

### Rollback Deployment

```bash
# List recent ECR images
aws ecr describe-images \
    --repository-name tradequest-prod-backend \
    --query 'sort_by(imageDetails,& imagePushedAt)[*].[imageTags[0],imagePushedAt]' \
    --output table

# Update service to use previous image
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --task-definition tradequest-prod-backend:<previous-revision>
```

### Scaling Operations

#### Auto Scaling
```bash
# Check current scaling policy
aws application-autoscaling describe-scaling-policies \
    --service-namespace ecs \
    --resource-id service/tradequest-cluster/tradequest-prod-backend

# Update scaling policy
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/tradequest-cluster/tradequest-prod-backend \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-scaling \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

#### Manual Scaling
```bash
# Scale up
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --desired-count 5

# Scale down
aws ecs update-service \
    --cluster tradequest-cluster \
    --service tradequest-prod-backend \
    --desired-count 1
```

---

## 💡 Best Practices

### Development Workflow

1. **Make changes locally**
   ```bash
   # Test with Docker Compose
   docker-compose up
   ```

2. **Test thoroughly**
   ```bash
   # Run tests
   cd backend && pytest
   cd ../frontend && npm test
   ```

3. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin main
   ```

4. **Deploy to AWS**
   ```bash
   ./scripts/deploy.sh full
   ```

5. **Monitor deployment**
   ```bash
   aws logs tail /ecs/tradequest-prod-backend --follow
   ```

### Code Guidelines for AWS Compatibility

#### ✅ **Always Use Storage Service for Files**
```python
# Good
from app.services.storage_service import storage_service

# Upload file
file_path = storage_service.upload_file(file_obj, "uploads/image.png")

# Download file
content = storage_service.download_file("uploads/image.png")

# Bad - hardcoded local path
with open("uploads/image.png", "wb") as f:
    f.write(data)
```

#### ✅ **Use Database Utils for JSON Columns**
```python
# Good
from app.core.database_utils import create_json_column

class MyModel(Base):
    data = create_json_column()  # Works with both PostgreSQL and SQLite

# Bad
from sqlalchemy import JSON
class MyModel(Base):
    data = Column(JSON)  # Won't use JSONB on PostgreSQL
```

#### ✅ **Use Secrets Service for Configuration**
```python
# Good
from app.services.secrets_service import get_config_value

api_key = get_config_value("OPENAI_API_KEY")

# Bad
import os
api_key = os.getenv("OPENAI_API_KEY")  # Won't check Secrets Manager
```

#### ✅ **Use settings.get_database_url()**
```python
# Good
from app.core.config import settings

database_url = settings.get_database_url()

# Bad
database_url = settings.DATABASE_URL  # Won't build from components
```

---

## 📞 Quick Reference Commands

```bash
# Deploy everything
./scripts/deploy.sh full

# View logs
aws logs tail /ecs/tradequest-prod-backend --follow

# Check service status
aws ecs describe-services --cluster tradequest-cluster --services tradequest-prod-backend

# Scale service
aws ecs update-service --cluster tradequest-cluster --service tradequest-prod-backend --desired-count 3

# Update secrets
aws secretsmanager update-secret --secret-id tradequest-prod/app --secret-string '{...}'

# SSH into container
aws ecs execute-command --cluster tradequest-cluster --task <task-id> --container backend --command "/bin/bash" --interactive

# Create database backup
aws rds create-db-snapshot --db-instance-identifier tradequest-prod-postgres --db-snapshot-identifier backup-$(date +%Y%m%d)

# Rollback deployment
aws ecs update-service --cluster tradequest-cluster --service tradequest-prod-backend --task-definition tradequest-prod-backend:<previous-revision>
```

---

## 🎓 Learning Resources

- **AWS ECS Documentation**: https://docs.aws.amazon.com/ecs/
- **CloudWatch Logs Insights**: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html
- **RDS Best Practices**: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

---

**Remember**: Always test changes locally first, monitor deployments, and have a rollback plan! 🚀
