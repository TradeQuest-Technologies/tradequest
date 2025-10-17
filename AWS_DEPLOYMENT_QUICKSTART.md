# 🚀 TradeQuest AWS Deployment Quick Start

## 📦 What You Have

- **Backend**: ECS Fargate on `tradequest-cluster`
- **Frontend**: AWS App Runner
- **ECR Repos**: `tradequest-prod-backend` and `tradequest-prod-frontend`
- **Region**: us-east-1
- **Account**: 759316875712

---

## 🎯 Quick Deployment (Fixed Auth Token Issue)

### Deploy Everything
```powershell
.\deploy-to-aws.ps1
```

This script will:
1. ✅ Login to AWS ECR
2. ✅ Build backend Docker image
3. ✅ Push backend to ECR
4. ✅ Update ECS backend service
5. ✅ Build frontend Docker image
6. ✅ Push frontend to ECR
7. ✅ Update AppRunner frontend service

**Estimated Time**: 5-10 minutes

---

## 📊 Monitor Deployment

### Check Status
```powershell
.\monitor-deployment.ps1
```

Shows:
- Backend ECS service status
- Frontend AppRunner status
- Health check results
- Recent operations

### View Logs (Real-time)

**Backend logs:**
```powershell
aws logs tail /ecs/tradequest-prod-backend --follow --region us-east-1
```

**Frontend logs:**
```powershell
aws logs tail /aws/apprunner/tradequest-prod-frontend --follow --region us-east-1
```

---

## 🔄 Rollback (If Needed)

### List Available Versions
```powershell
.\rollback-deployment.ps1
```

### Rollback Backend
```powershell
.\rollback-deployment.ps1 -Service backend -BackendRevision 5
```

### Rollback Frontend
Follow the instructions shown by the rollback script (AppRunner requires re-pushing old image as latest)

---

## ✅ Verify Deployment

1. **Backend Health**: https://api.tradequest.tech/health
2. **Frontend**: https://tradequest.tech
3. **Login and test**: The auth token fix is now deployed! 🎉

---

## 🐛 Troubleshooting

### Backend won't start
```powershell
# Check task status
aws ecs list-tasks --cluster tradequest-cluster --service-name tradequest-prod-backend --region us-east-1

# View task details
aws ecs describe-tasks --cluster tradequest-cluster --tasks <task-arn> --region us-east-1

# Check logs
aws logs tail /ecs/tradequest-prod-backend --since 30m --region us-east-1
```

### Frontend won't start
```powershell
# Get service ARN
$arn = aws apprunner list-services --region us-east-1 --query "ServiceSummaryList[?ServiceName=='tradequest-prod-frontend'].ServiceArn" --output text

# Check operations
aws apprunner list-operations --service-arn $arn --region us-east-1

# View logs
aws logs tail /aws/apprunner/tradequest-prod-frontend --since 30m --region us-east-1
```

### Image push fails
```powershell
# Re-login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 759316875712.dkr.ecr.us-east-1.amazonaws.com
```

---

## 📝 What Was Fixed

**Issue**: 401 Unauthorized errors on broker connections page

**Root Cause**: Frontend was looking for token in `localStorage.getItem('access_token')` but auth flow stores it as `localStorage.getItem('tq_session')`

**Files Changed**:
- ✅ `frontend/app/brokers/page.tsx` - 5 instances fixed
- ✅ `frontend/app/integrations/page.tsx` - 4 instances fixed
- ✅ `frontend/app/market/page.tsx` - 3 instances fixed
- ✅ `frontend/app/onboarding/page.tsx` - 2 instances fixed
- ✅ `frontend/components/AppShell.tsx` - 1 instance fixed
- ✅ `frontend/app/chat/page.tsx` - 1 instance fixed

**Solution**: All token lookups now use:
```typescript
const token = localStorage.getItem('tq_session') || sessionStorage.getItem('tq_session')
```

---

## 🎉 After Deployment

1. Clear browser cache / hard refresh
2. Log in to TradeQuest
3. Navigate to `/brokers` page
4. Broker connections should now load without 401 errors!

---

## 🔐 Security Notes

- ✅ API keys encrypted with Fernet (AES-GCM)
- ✅ Credentials stored in AWS Secrets Manager
- ✅ JWT tokens stored in localStorage/sessionStorage
- ✅ HTTPS enforced on production domains

---

## 📞 Quick Commands Reference

```powershell
# Deploy everything
.\deploy-to-aws.ps1

# Monitor status
.\monitor-deployment.ps1

# View backend logs
aws logs tail /ecs/tradequest-prod-backend --follow --region us-east-1

# View frontend logs
aws logs tail /aws/apprunner/tradequest-prod-frontend --follow --region us-east-1

# Restart backend (force new deployment)
aws ecs update-service --cluster tradequest-cluster --service tradequest-prod-backend --force-new-deployment --region us-east-1

# Check ECS service
aws ecs describe-services --cluster tradequest-cluster --services tradequest-prod-backend --region us-east-1

# Get AppRunner service URL
aws apprunner list-services --region us-east-1 --query "ServiceSummaryList[?ServiceName=='tradequest-prod-frontend'].ServiceUrl" --output text
```

---

**Ready to deploy? Run:** `.\deploy-to-aws.ps1` 🚀

