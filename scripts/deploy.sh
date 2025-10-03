#!/bin/bash

# TradeQuest Deployment Script
# This script deploys the application to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_commands=()
    
    if ! command_exists aws; then
        missing_commands+=("aws-cli")
    fi
    
    if ! command_exists terraform; then
        missing_commands+=("terraform")
    fi
    
    if ! command_exists docker; then
        missing_commands+=("docker")
    fi
    
    if ! command_exists jq; then
        missing_commands+=("jq")
    fi
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        print_error "Please install the missing commands and try again."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid"
        print_error "Please run 'aws configure' to set up your credentials"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region)
    
    print_success "AWS credentials configured for account: $account_id in region: $region"
}

# Function to build and push Docker images
build_and_push_images() {
    print_status "Building and pushing Docker images..."
    
    local aws_account_id=$(aws sts get-caller-identity --query Account --output text)
    local aws_region=$(aws configure get region)
    
    # Get ECR repository URLs from Terraform outputs
    local backend_repo=$(cd aws/terraform && terraform output -raw ecr_backend_repository_url 2>/dev/null || echo "")
    local frontend_repo=$(cd aws/terraform && terraform output -raw ecr_frontend_repository_url 2>/dev/null || echo "")
    
    if [ -z "$backend_repo" ] || [ -z "$frontend_repo" ]; then
        print_error "ECR repositories not found. Please run 'terraform apply' first."
        exit 1
    fi
    
    # Login to ECR
    print_status "Logging in to ECR..."
    aws ecr get-login-password --region $aws_region | docker login --username AWS --password-stdin $backend_repo
    
    # Build and push backend image
    print_status "Building backend image..."
    docker build -t tradequest-backend ./backend
    docker tag tradequest-backend:latest $backend_repo:latest
    docker push $backend_repo:latest
    
    # Build and push frontend image
    print_status "Building frontend image..."
    docker build -t tradequest-frontend ./frontend
    docker tag tradequest-frontend:latest $frontend_repo:latest
    docker push $frontend_repo:latest
    
    print_success "Docker images built and pushed successfully"
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    cd aws/terraform
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Plan the deployment
    print_status "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply the plan
    print_status "Applying Terraform plan..."
    terraform apply tfplan
    
    cd ../..
    
    print_success "Infrastructure deployed successfully"
}

# Function to update ECS services
update_ecs_services() {
    print_status "Updating ECS services..."
    
    local cluster_name=$(cd aws/terraform && terraform output -raw ecs_cluster_name)
    
    # Force new deployment of backend service
    print_status "Updating backend service..."
    aws ecs update-service \
        --cluster $cluster_name \
        --service tradequest-prod-backend \
        --force-new-deployment \
        --no-cli-pager
    
    # Force new deployment of frontend service
    print_status "Updating frontend service..."
    aws ecs update-service \
        --cluster $cluster_name \
        --service tradequest-prod-frontend \
        --force-new-deployment \
        --no-cli-pager
    
    print_success "ECS services updated successfully"
}

# Function to wait for deployment
wait_for_deployment() {
    print_status "Waiting for deployment to complete..."
    
    local cluster_name=$(cd aws/terraform && terraform output -raw ecs_cluster_name)
    
    # Wait for backend service
    print_status "Waiting for backend service to stabilize..."
    aws ecs wait services-stable \
        --cluster $cluster_name \
        --services tradequest-prod-backend
    
    # Wait for frontend service
    print_status "Waiting for frontend service to stabilize..."
    aws ecs wait services-stable \
        --cluster $cluster_name \
        --services tradequest-prod-frontend
    
    print_success "Deployment completed successfully"
}

# Function to show deployment info
show_deployment_info() {
    print_status "Deployment Information:"
    
    local app_url=$(cd aws/terraform && terraform output -raw application_url)
    local lb_dns=$(cd aws/terraform && terraform output -raw load_balancer_dns_name)
    
    echo ""
    echo "🚀 Application URL: $app_url"
    echo "🌐 Load Balancer DNS: $lb_dns"
    echo ""
    echo "📊 Monitor your deployment:"
    echo "   - AWS Console: https://console.aws.amazon.com/ecs/home"
    echo "   - CloudWatch: https://console.aws.amazon.com/cloudwatch/home"
    echo ""
}

# Main deployment function
main() {
    local action=${1:-"full"}
    
    case $action in
        "infrastructure")
            check_prerequisites
            check_aws_credentials
            deploy_infrastructure
            ;;
        "images")
            check_prerequisites
            check_aws_credentials
            build_and_push_images
            ;;
        "services")
            check_prerequisites
            check_aws_credentials
            update_ecs_services
            wait_for_deployment
            ;;
        "full")
            check_prerequisites
            check_aws_credentials
            deploy_infrastructure
            build_and_push_images
            update_ecs_services
            wait_for_deployment
            show_deployment_info
            ;;
        *)
            echo "Usage: $0 [infrastructure|images|services|full]"
            echo ""
            echo "Commands:"
            echo "  infrastructure  - Deploy only the AWS infrastructure"
            echo "  images         - Build and push only the Docker images"
            echo "  services       - Update only the ECS services"
            echo "  full           - Complete deployment (default)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
