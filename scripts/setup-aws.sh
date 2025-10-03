#!/bin/bash

# TradeQuest AWS Setup Script
# This script sets up the initial AWS environment for TradeQuest

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
    
    if ! command_exists jq; then
        missing_commands+=("jq")
    fi
    
    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        echo ""
        echo "Installation instructions:"
        echo "  AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo "  Terraform: https://learn.hashicorp.com/tutorials/terraform/install-cli"
        echo "  jq: https://stedolan.github.io/jq/download/"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Function to check AWS credentials
check_aws_credentials() {
    print_status "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured"
        echo ""
        echo "Please configure AWS credentials:"
        echo "  1. Run 'aws configure'"
        echo "  2. Enter your Access Key ID"
        echo "  3. Enter your Secret Access Key"
        echo "  4. Enter your preferred region (e.g., us-east-1)"
        echo "  5. Enter output format (json)"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local region=$(aws configure get region)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    print_success "AWS credentials configured"
    echo "  Account ID: $account_id"
    echo "  Region: $region"
    echo "  User: $user_arn"
}

# Function to create S3 bucket for Terraform state
create_terraform_state_bucket() {
    print_status "Creating S3 bucket for Terraform state..."
    
    local bucket_name="tradequest-terraform-state-$(date +%s)"
    local region=$(aws configure get region)
    
    # Create bucket
    if [ "$region" = "us-east-1" ]; then
        aws s3 mb s3://$bucket_name --region $region
    else
        aws s3 mb s3://$bucket_name --region $region
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket $bucket_name \
        --versioning-configuration Status=Enabled
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket $bucket_name \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    # Block public access
    aws s3api put-public-access-block \
        --bucket $bucket_name \
        --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
    
    print_success "Terraform state bucket created: $bucket_name"
    
    # Update terraform backend configuration
    cat > aws/terraform/backend.tf << EOF
terraform {
  backend "s3" {
    bucket = "$bucket_name"
    key    = "tradequest/terraform.tfstate"
    region = "$region"
  }
}
EOF
    
    print_success "Backend configuration updated"
}

# Function to initialize Terraform
initialize_terraform() {
    print_status "Initializing Terraform..."
    
    cd aws/terraform
    
    # Copy terraform.tfvars.example to terraform.tfvars if it doesn't exist
    if [ ! -f terraform.tfvars ]; then
        if [ -f terraform.tfvars.example ]; then
            cp terraform.tfvars.example terraform.tfvars
            print_warning "Created terraform.tfvars from example. Please review and update the values."
        else
            print_error "terraform.tfvars.example not found. Please create terraform.tfvars manually."
            exit 1
        fi
    fi
    
    terraform init
    
    cd ../..
    
    print_success "Terraform initialized"
}

# Function to create Route 53 hosted zone (optional)
create_hosted_zone() {
    local domain_name=$1
    
    if [ -z "$domain_name" ]; then
        print_warning "No domain name provided. Skipping Route 53 setup."
        return
    fi
    
    print_status "Creating Route 53 hosted zone for $domain_name..."
    
    # Check if hosted zone already exists
    local zone_id=$(aws route53 list-hosted-zones-by-name \
        --dns-name $domain_name \
        --query 'HostedZones[0].Id' \
        --output text 2>/dev/null || echo "None")
    
    if [ "$zone_id" != "None" ] && [ "$zone_id" != "null" ]; then
        print_warning "Hosted zone for $domain_name already exists"
        zone_id=$(echo $zone_id | sed 's|/hostedzone/||')
    else
        # Create hosted zone
        local zone_response=$(aws route53 create-hosted-zone \
            --name $domain_name \
            --caller-reference "tradequest-$(date +%s)")
        
        zone_id=$(echo $zone_response | jq -r '.HostedZone.Id' | sed 's|/hostedzone/||')
        print_success "Hosted zone created: $zone_id"
    fi
    
    # Get name servers
    local name_servers=$(aws route53 get-hosted-zone \
        --id $zone_id \
        --query 'DelegationSet.NameServers' \
        --output text)
    
    print_status "Name servers for $domain_name:"
    echo "$name_servers" | tr '\t' '\n' | sed 's/^/  /'
    
    print_warning "Please update your domain's name servers with the above values"
}

# Function to show next steps
show_next_steps() {
    print_success "AWS setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Review and update aws/terraform/terraform.tfvars"
    echo "2. If you have a domain, update the domain configuration"
    echo "3. Run './scripts/deploy.sh infrastructure' to deploy the infrastructure"
    echo "4. Run './scripts/deploy.sh full' for a complete deployment"
    echo ""
    echo "Configuration files:"
    echo "  - aws/terraform/terraform.tfvars (update with your values)"
    echo "  - aws/terraform/backend.tf (Terraform state configuration)"
    echo ""
}

# Main function
main() {
    local domain_name=${1:-""}
    
    print_status "Setting up AWS environment for TradeQuest..."
    echo ""
    
    check_prerequisites
    check_aws_credentials
    create_terraform_state_bucket
    initialize_terraform
    create_hosted_zone "$domain_name"
    show_next_steps
}

# Run main function with all arguments
main "$@"
