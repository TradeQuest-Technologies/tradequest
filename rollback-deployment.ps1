# TradeQuest Rollback Script

param(
    [Parameter(Mandatory=$false)]
    [string]$Service = "both", # backend, frontend, or both
    
    [Parameter(Mandatory=$false)]
    [int]$BackendRevision = 0,  # Set to 0 to list available revisions
    
    [Parameter(Mandatory=$false)]
    [string]$FrontendImageTag = ""  # Set to specific tag to rollback
)

$REGION = "us-east-1"
$ECS_CLUSTER = "tradequest-cluster"
$ECS_SERVICE = "tradequest-prod-backend"
$ACCOUNT_ID = "759316875712"

Write-Host "`n=== TradeQuest Rollback Tool ===" -ForegroundColor Cyan

if ($Service -eq "backend" -or $Service -eq "both") {
    Write-Host "`n[Backend Rollback]" -ForegroundColor Yellow
    
    if ($BackendRevision -eq 0) {
        Write-Host "Available task definitions:" -ForegroundColor Gray
        aws ecs list-task-definitions `
            --family-prefix tradequest-prod-backend `
            --region $REGION `
            --sort DESC `
            --max-items 10 `
            --query "taskDefinitionArns" `
            --output table
        
        Write-Host "`nTo rollback, run:" -ForegroundColor Yellow
        Write-Host "  .\rollback-deployment.ps1 -Service backend -BackendRevision <number>" -ForegroundColor Gray
    } else {
        Write-Host "Rolling back backend to revision $BackendRevision..." -ForegroundColor Yellow
        
        aws ecs update-service `
            --cluster $ECS_CLUSTER `
            --service $ECS_SERVICE `
            --task-definition "tradequest-prod-backend:$BackendRevision" `
            --region $REGION `
            --no-cli-pager
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Backend rollback initiated" -ForegroundColor Green
        } else {
            Write-Host "✗ Backend rollback failed" -ForegroundColor Red
        }
    }
}

if ($Service -eq "frontend" -or $Service -eq "both") {
    Write-Host "`n[Frontend Rollback]" -ForegroundColor Yellow
    
    if ([string]::IsNullOrWhiteSpace($FrontendImageTag)) {
        Write-Host "Available frontend images:" -ForegroundColor Gray
        aws ecr describe-images `
            --repository-name tradequest-prod-frontend `
            --region $REGION `
            --query "sort_by(imageDetails,& imagePushedAt)[*].[imageTags[0],imagePushedAt]" `
            --output table `
            | Select-Object -Last 20
        
        Write-Host "`nNOTE: AppRunner doesn't support direct image rollback." -ForegroundColor Yellow
        Write-Host "To rollback frontend:" -ForegroundColor Yellow
        Write-Host "  1. Pull the old image: docker pull $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend:<tag>" -ForegroundColor Gray
        Write-Host "  2. Re-tag as latest: docker tag <image> $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend:latest" -ForegroundColor Gray
        Write-Host "  3. Push: docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/tradequest-prod-frontend:latest" -ForegroundColor Gray
        Write-Host "  4. Trigger deployment: .\deploy-to-aws.ps1" -ForegroundColor Gray
    }
}

Write-Host ""

