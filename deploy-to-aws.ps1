# TradeQuest Manual Deployment Script for AWS
# This script builds and deploys both frontend and backend

# Configuration
$ACCOUNT_ID = "759316875712"
$REGION = "us-east-1"
$PROJECT_ROOT = "C:\Users\Avi\ATQ_Ventures\Aggregator"
$BACKEND_REPO = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-backend"
$FRONTEND_REPO = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend"
$ECS_CLUSTER = "tradequest-cluster"
$ECS_SERVICE = "tradequest-prod-backend"

Write-Host "`n=== TradeQuest AWS Deployment ===" -ForegroundColor Cyan
Write-Host "Account: $ACCOUNT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION`n" -ForegroundColor Gray

# Step 1: Login to ECR
Write-Host "[Step 1/7] Logging in to AWS ECR..." -ForegroundColor Yellow
try {
    $loginCmd = aws ecr get-login-password --region $REGION
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to get ECR login password" -ForegroundColor Red
        exit 1
    }
    $loginCmd | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker login failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Successfully logged in to ECR`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Build Backend
Write-Host "[Step 2/7] Building backend Docker image..." -ForegroundColor Yellow
Push-Location $PROJECT_ROOT
try {
    docker build -t tradequest-backend ./backend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Backend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Backend image built successfully`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Step 3: Tag and Push Backend
Write-Host "[Step 3/7] Tagging and pushing backend image to ECR..." -ForegroundColor Yellow
try {
    docker tag tradequest-backend:latest "$BACKEND_REPO:latest"
    docker push "$BACKEND_REPO:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Backend push failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Backend image pushed to ECR`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Step 4: Update ECS Backend Service
Write-Host "[Step 4/7] Updating ECS backend service..." -ForegroundColor Yellow
try {
    aws ecs update-service `
        --cluster $ECS_CLUSTER `
        --service $ECS_SERVICE `
        --force-new-deployment `
        --region $REGION `
        --no-cli-pager
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: ECS service update failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] ECS backend service deployment initiated`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Build Frontend
Write-Host "[Step 5/7] Building frontend Docker image..." -ForegroundColor Yellow
Push-Location $PROJECT_ROOT
try {
    docker build -t tradequest-frontend ./frontend
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Frontend image built successfully`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Step 6: Tag and Push Frontend
Write-Host "[Step 6/7] Tagging and pushing frontend image to ECR..." -ForegroundColor Yellow
try {
    docker tag tradequest-frontend:latest "$FRONTEND_REPO:latest"
    docker push "$FRONTEND_REPO:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend push failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Frontend image pushed to ECR`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Step 7: Update AppRunner Frontend Service
Write-Host "[Step 7/7] Updating AppRunner frontend service..." -ForegroundColor Yellow
try {
    # Get AppRunner service ARN
    $serviceArn = aws apprunner list-services `
        --region $REGION `
        --query "ServiceSummaryList[?ServiceName=='tradequest-prod-frontend'].ServiceArn" `
        --output text
    
    if ([string]::IsNullOrWhiteSpace($serviceArn)) {
        Write-Host "ERROR: Could not find AppRunner service" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Found AppRunner service: $serviceArn" -ForegroundColor Gray
    
    # Trigger deployment
    aws apprunner start-deployment `
        --service-arn $serviceArn `
        --region $REGION `
        --no-cli-pager
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: AppRunner deployment failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] AppRunner frontend deployment initiated`n" -ForegroundColor Green
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}

# Final Summary
Write-Host "`n=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "[OK] Backend image pushed and ECS service updated" -ForegroundColor Green
Write-Host "[OK] Frontend image pushed and AppRunner service updated" -ForegroundColor Green
Write-Host "`nMonitor deployment status:" -ForegroundColor Yellow
Write-Host "  Backend:  aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $REGION" -ForegroundColor Gray
Write-Host "  Frontend: aws apprunner describe-service --service-arn [arn] --region $REGION" -ForegroundColor Gray
Write-Host "`nView logs:" -ForegroundColor Yellow
Write-Host "  Backend:  aws logs tail /ecs/tradequest-prod-backend --follow --region $REGION" -ForegroundColor Gray
Write-Host "  Frontend: aws logs tail /aws/apprunner/tradequest-prod-frontend --follow --region $REGION" -ForegroundColor Gray
Write-Host "`n[SUCCESS] Deployment script completed!`n" -ForegroundColor Green

