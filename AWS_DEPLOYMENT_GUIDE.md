# 🚀 TradeQuest AWS Deployment Guide

This guide will walk you through deploying TradeQuest to AWS using modern cloud infrastructure.

## 📋 Prerequisites

Before starting, ensure you have the following installed:

- **AWS CLI** - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Terraform** - [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- **Docker** - [Installation Guide](https://docs.docker.com/get-docker/)
- **jq** - [Installation Guide](https://stedolan.github.io/jq/download/)

## 🔧 AWS Account Setup

### 1. Configure AWS Credentials

```bash
aws configure
```

Enter your:
- Access Key ID
- Secret Access Key  
- Default region (e.g., `us-east-1`)
- Output format (`json`)

### 2. Verify Setup

```bash
aws sts get-caller-identity
```

You should see your account information.

## 🏗️ Infrastructure Deployment

### Quick Setup (Recommended)

```bash
# Run the automated setup script
./scripts/setup-aws.sh

# Or with a custom domain
./scripts/setup-aws.sh yourdomain.com
```

### Manual Setup

1. **Create Terraform State Bucket**
```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://your-terraform-state-bucket
```

2. **Configure Terraform**
```bash
cd aws/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

3. **Initialize and Deploy**
```bash
terraform init
terraform plan
terraform apply
```

## 🔐 Configuration

### Required Environment Variables

Create a `terraform.tfvars` file with your configuration:

```hcl
# Basic Configuration
aws_region = "us-east-1"
environment = "prod"
project_name = "tradequest"

# Domain (optional)
domain_name = "yourdomain.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."

# Database
db_instance_class = "db.t3.micro"
db_allocated_storage = 20

# Scaling
min_capacity = 1
max_capacity = 10
```

### Secrets Configuration

The following secrets will be stored in AWS Secrets Manager:

```bash
# Set secrets via Terraform variables or AWS CLI
aws secretsmanager update-secret \
  --secret-id tradequest-prod/app \
  --secret-string '{
    "OPENAI_API_KEY": "your-openai-key",
    "STRIPE_SECRET_KEY": "sk_live_...",
    "SMTP_USERNAME": "your-smtp-username",
    "SMTP_PASSWORD": "your-smtp-password"
  }'
```

## 🚀 Deployment Options

### Full Deployment
```bash
./scripts/deploy.sh full
```

### Infrastructure Only
```bash
./scripts/deploy.sh infrastructure
```

### Docker Images Only
```bash
./scripts/deploy.sh images
```

### Update Services Only
```bash
./scripts/deploy.sh services
```

## 🏗️ Infrastructure Overview

The deployment creates the following AWS resources:

### Networking
- **VPC** with public/private subnets
- **Internet Gateway** and **NAT Gateways**
- **Security Groups** for each service
- **Application Load Balancer**

### Compute
- **ECS Fargate Cluster**
- **Auto Scaling** for both frontend and backend
- **ECR Repositories** for Docker images

### Database
- **RDS PostgreSQL** instance
- **ElastiCache Redis** cluster
- **Automated backups** and monitoring

### Storage
- **S3 Bucket** for file storage
- **Lifecycle policies** for cost optimization
- **Encryption** at rest

### Security
- **Secrets Manager** for sensitive data
- **IAM Roles** with least privilege
- **VPC Endpoints** for secure communication

## 📊 Monitoring

### CloudWatch Dashboards
- Application metrics
- Database performance
- Load balancer metrics
- ECS service health

### Logging
- Centralized logging via CloudWatch
- Log retention policies
- Structured logging with JSON

### Alerts
- High CPU utilization
- Database connection issues
- Failed health checks
- Error rate thresholds

## 🔄 CI/CD Pipeline

GitHub Actions workflow automatically:
1. **Tests** the application
2. **Builds** Docker images
3. **Pushes** to ECR
4. **Deploys** to ECS
5. **Verifies** deployment

### Required GitHub Secrets
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 💰 Cost Optimization

### Development Environment
- Use `db.t3.micro` for RDS
- Use `cache.t3.micro` for Redis
- Set `min_capacity = 1`
- Use single AZ deployment

### Production Environment
- Use `db.t3.small` or larger
- Enable **Reserved Instances** for predictable workloads
- Use **Spot Instances** for non-critical workloads
- Implement **Auto Scaling** policies

### Monitoring Costs
```bash
# Check current costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost
```

## 🔒 Security Best Practices

### Network Security
- Private subnets for databases
- Security groups with minimal access
- VPC endpoints for AWS services

### Application Security
- Secrets stored in Secrets Manager
- IAM roles with least privilege
- Regular security updates

### Data Security
- Encryption at rest and in transit
- Automated backups
- Access logging

## 🛠️ Troubleshooting

### Common Issues

1. **ECS Tasks Failing**
```bash
# Check task logs
aws logs describe-log-streams \
  --log-group-name /ecs/tradequest-prod-backend

# Check service events
aws ecs describe-services \
  --cluster tradequest-cluster \
  --services tradequest-prod-backend
```

2. **Database Connection Issues**
```bash
# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier tradequest-prod-postgres

# Check security groups
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxxx
```

3. **Load Balancer Health Checks Failing**
```bash
# Check target group health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# Check ALB logs
aws logs describe-log-groups \
  --log-group-name-prefix /aws/elasticloadbalancing
```

### Debugging Commands

```bash
# Get all resources
terraform show

# Check ECS service status
aws ecs describe-services \
  --cluster tradequest-cluster \
  --services tradequest-prod-backend tradequest-prod-frontend

# Check load balancer DNS
aws elbv2 describe-load-balancers \
  --names tradequest-prod-alb
```

## 📞 Support

For issues with this deployment:

1. Check the troubleshooting section above
2. Review CloudWatch logs
3. Check AWS service status pages
4. Open an issue in the repository

## 🔄 Updates and Maintenance

### Regular Maintenance
- Update Docker base images monthly
- Rotate secrets quarterly
- Review and update security groups
- Monitor and optimize costs

### Scaling
- Adjust ECS service desired count
- Modify auto-scaling policies
- Upgrade RDS instance classes
- Add/remove availability zones

---

## 🎉 Success!

Once deployed, your TradeQuest application will be available at:
- **Load Balancer URL**: `http://your-alb-dns-name`
- **Custom Domain**: `https://yourdomain.com`

Monitor your deployment in the AWS Console and enjoy your scalable, production-ready trading platform! 🚀
