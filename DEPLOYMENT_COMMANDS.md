# 🚀 Manual Deployment Commands for Advanced AI Update

## Prerequisites
- AWS CLI configured
- Docker Desktop running
- Logged into AWS account 759316875712

---

## Step 1: Get ECR Repository URLs

```bash
# Get AWS region
aws configure get region

# Get ECR repo URLs (or use AWS Console)
ACCOUNT_ID=759316875712
REGION=us-east-1  # Replace with your region

BACKEND_REPO=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-backend
FRONTEND_REPO=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend
```

---

## Step 2: Login to ECR

```bash
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
```

---

## Step 3: Build and Push Backend (ECS)

```bash
# Navigate to project root
cd C:\Users\Avi\ATQ_Ventures\Aggregator

# Build backend image
docker build -t tradequest-backend ./backend

# Tag image
docker tag tradequest-backend:latest $BACKEND_REPO:latest

# Push to ECR
docker push $BACKEND_REPO:latest
```

---

## Step 4: Update ECS Backend Service

```bash
# Force new deployment (will pull latest image)
aws ecs update-service \
    --cluster tradequest-prod-cluster \
    --service tradequest-prod-backend \
    --force-new-deployment \
    --region $REGION

# Wait for deployment to stabilize (optional)
aws ecs wait services-stable \
    --cluster tradequest-prod-cluster \
    --services tradequest-prod-backend \
    --region $REGION
```

---

## Step 5: Build and Push Frontend (AppRunner)

```bash
# Build frontend image
docker build -t tradequest-frontend ./frontend

# Tag image
docker tag tradequest-frontend:latest $FRONTEND_REPO:latest

# Push to ECR
docker push $FRONTEND_REPO:latest
```

---

## Step 6: Update AppRunner Frontend Service

```bash
# Get AppRunner service ARN
aws apprunner list-services --region $REGION --query 'ServiceSummaryList[?ServiceName==`tradequest-prod-frontend`].ServiceArn' --output text

# Store ARN in variable
SERVICE_ARN=$(aws apprunner list-services --region $REGION --query 'ServiceSummaryList[?ServiceName==`tradequest-prod-frontend`].ServiceArn' --output text)

# Trigger new deployment
aws apprunner start-deployment --service-arn $SERVICE_ARN --region $REGION

# Check status
aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION --query 'Service.Status' --output text
```

---

## Step 7: Verify Deployment

```bash
# Check ECS service status
aws ecs describe-services \
    --cluster tradequest-prod-cluster \
    --services tradequest-prod-backend \
    --region $REGION \
    --query 'services[0].deployments[0]' \
    --output json

# Check AppRunner service status
aws apprunner describe-service \
    --service-arn $SERVICE_ARN \
    --region $REGION \
    --query 'Service.[Status,ServiceUrl]' \
    --output text
```

---

## Quick Copy-Paste Commands (PowerShell)

```powershell
# Set variables
$ACCOUNT_ID = "759316875712"
$REGION = "us-east-1"
$BACKEND_REPO = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-backend"
$FRONTEND_REPO = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Build and push backend
cd C:\Users\Avi\ATQ_Ventures\Aggregator
docker build -t tradequest-backend ./backend
docker tag tradequest-backend:latest "$BACKEND_REPO:latest"
docker push "$BACKEND_REPO:latest"

# Update ECS backend
aws ecs update-service --cluster tradequest-prod-cluster --service tradequest-prod-backend --force-new-deployment --region $REGION

# Build and push frontend
docker build -t tradequest-frontend ./frontend
docker tag tradequest-frontend:latest "$FRONTEND_REPO:latest"
docker push "$FRONTEND_REPO:latest"

# Get AppRunner ARN and update
$SERVICE_ARN = aws apprunner list-services --region $REGION --query 'ServiceSummaryList[?ServiceName==`tradequest-prod-frontend`].ServiceArn' --output text
aws apprunner start-deployment --service-arn $SERVICE_ARN --region $REGION
```

---

## Monitoring

### Backend (ECS) Logs
```bash
# Stream backend logs
aws logs tail /ecs/tradequest-prod-backend --follow --region $REGION
```

### Frontend (AppRunner) Logs
```bash
# Get log group name
aws apprunner describe-service --service-arn $SERVICE_ARN --region $REGION --query 'Service.ServiceName' --output text

# Stream logs
aws logs tail /aws/apprunner/tradequest-prod-frontend --follow --region $REGION
```

---

## Rollback (if needed)

### Backend
```bash
# List task definitions
aws ecs list-task-definitions --family-prefix tradequest-prod-backend --region $REGION

# Update service to previous task definition
aws ecs update-service \
    --cluster tradequest-prod-cluster \
    --service tradequest-prod-backend \
    --task-definition tradequest-prod-backend:PREVIOUS_REVISION \
    --region $REGION
```

### Frontend
```bash
# AppRunner auto-creates operation on failed deployment
# Check operation status
aws apprunner list-operations --service-arn $SERVICE_ARN --region $REGION
```

---

## ✅ Success Indicators

- ✅ Backend: `aws ecs describe-services` shows `runningCount` equals `desiredCount`
- ✅ Frontend: `aws apprunner describe-service` shows `Status: RUNNING`
- ✅ Health checks passing
- ✅ Can access https://api.tradequest.tech/health
- ✅ Can access frontend and use AI chat

---

## 🔥 Troubleshooting

### Backend won't start
```bash
# Check task status
aws ecs list-tasks --cluster tradequest-prod-cluster --service-name tradequest-prod-backend --region $REGION

# Get task ARN and describe
TASK_ARN=$(aws ecs list-tasks --cluster tradequest-prod-cluster --service-name tradequest-prod-backend --region $REGION --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster tradequest-prod-cluster --tasks $TASK_ARN --region $REGION
```

### Frontend won't start
```bash
# Check AppRunner operations
aws apprunner list-operations --service-arn $SERVICE_ARN --region $REGION

# Get operation details
OPERATION_ID=$(aws apprunner list-operations --service-arn $SERVICE_ARN --region $REGION --query 'OperationSummaryList[0].Id' --output text)
aws apprunner describe-operation --service-arn $SERVICE_ARN --operation-id $OPERATION_ID --region $REGION
```

### Image pull errors
```bash
# Verify image exists in ECR
aws ecr describe-images --repository-name tradequest-prod-backend --region $REGION
aws ecr describe-images --repository-name tradequest-prod-frontend --region $REGION
```

