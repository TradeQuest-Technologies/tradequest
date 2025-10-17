# TradeQuest Deployment Monitoring Script

$REGION = "us-east-1"
$ECS_CLUSTER = "tradequest-cluster"
$ECS_SERVICE = "tradequest-prod-backend"

Write-Host "`n=== TradeQuest Deployment Monitor ===" -ForegroundColor Cyan

# Monitor Backend (ECS)
Write-Host "`n[Backend - ECS Service Status]" -ForegroundColor Yellow
aws ecs describe-services `
    --cluster $ECS_CLUSTER `
    --services $ECS_SERVICE `
    --region $REGION `
    --query "services[0].[serviceName,status,runningCount,desiredCount,deployments[0].status]" `
    --output table

# Get Backend Task Status
Write-Host "`n[Backend - Recent Tasks]" -ForegroundColor Yellow
$taskArns = aws ecs list-tasks `
    --cluster $ECS_CLUSTER `
    --service-name $ECS_SERVICE `
    --region $REGION `
    --query "taskArns" `
    --output json | ConvertFrom-Json

if ($taskArns.Count -gt 0) {
    aws ecs describe-tasks `
        --cluster $ECS_CLUSTER `
        --tasks $taskArns[0] `
        --region $REGION `
        --query "tasks[0].[taskArn,lastStatus,healthStatus,containers[0].healthStatus]" `
        --output table
} else {
    Write-Host "No running tasks found" -ForegroundColor Red
}

# Monitor Frontend (AppRunner)
Write-Host "`n[Frontend - AppRunner Service Status]" -ForegroundColor Yellow
$serviceArn = aws apprunner list-services `
    --region $REGION `
    --query "ServiceSummaryList[?ServiceName=='tradequest-prod-frontend'].ServiceArn" `
    --output text

if (![string]::IsNullOrWhiteSpace($serviceArn)) {
    aws apprunner describe-service `
        --service-arn $serviceArn `
        --region $REGION `
        --query "Service.[ServiceName,Status,ServiceUrl]" `
        --output table
    
    # Get recent operations
    Write-Host "`n[Frontend - Recent Operations]" -ForegroundColor Yellow
    aws apprunner list-operations `
        --service-arn $serviceArn `
        --region $REGION `
        --max-results 5 `
        --query "OperationSummaryList[*].[Type,Status,StartedAt,EndedAt]" `
        --output table
} else {
    Write-Host "AppRunner service not found" -ForegroundColor Red
}

# Health Checks
Write-Host "`n[Health Checks]" -ForegroundColor Yellow
Write-Host "Testing backend health endpoint..." -ForegroundColor Gray
try {
    $backendHealth = Invoke-WebRequest -Uri "https://api.tradequest.tech/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Backend is healthy (Status: $($backendHealth.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend health check failed: $_" -ForegroundColor Red
}

Write-Host "`nTesting frontend..." -ForegroundColor Gray
try {
    $frontendHealth = Invoke-WebRequest -Uri "https://tradequest.tech" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Frontend is reachable (Status: $($frontendHealth.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend check failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Quick Commands ===" -ForegroundColor Cyan
Write-Host "Backend logs:  aws logs tail /ecs/tradequest-prod-backend --follow --region $REGION" -ForegroundColor Gray
Write-Host "Frontend logs: aws logs tail /aws/apprunner/tradequest-prod-frontend --follow --region $REGION" -ForegroundColor Gray
Write-Host ""

