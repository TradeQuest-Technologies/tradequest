# IAM Role for App Runner to access ECR
resource "aws_iam_role" "apprunner_ecr" {
  name = "${local.name_prefix}-apprunner-ecr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_ecr.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# App Runner Service for Frontend
resource "aws_apprunner_service" "frontend" {
  service_name = "${local.name_prefix}-frontend"

  source_configuration {
    image_repository {
      image_configuration {
        port = "3000"
        
        runtime_environment_variables = {
          NODE_ENV            = "production"
          NEXT_PUBLIC_API_URL = var.domain_name != "" ? "https://${var.domain_name}" : "http://localhost:8000"
          PORT                = "3000"
          HOSTNAME            = "0.0.0.0"
        }
      }
      
      image_identifier      = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${aws_ecr_repository.frontend.name}:latest"
      image_repository_type = "ECR"
    }
    
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr.arn
    }

    auto_deployments_enabled = true
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 3
  }

  instance_configuration {
    cpu    = "1 vCPU"
    memory = "2 GB"
  }

  tags = local.common_tags
}

# Custom Domain Association for App Runner
resource "aws_apprunner_custom_domain_association" "frontend" {
  count = var.domain_name != "" ? 1 : 0

  domain_name          = var.domain_name
  enable_www_subdomain = true
  service_arn          = aws_apprunner_service.frontend.arn
}

# Output the App Runner URL
output "apprunner_frontend_url" {
  description = "App Runner service URL for frontend"
  value       = aws_apprunner_service.frontend.service_url
}

output "apprunner_custom_domain_records" {
  description = "DNS records to configure for custom domain"
  value       = var.domain_name != "" && var.certificate_arn != "" ? aws_apprunner_custom_domain_association.frontend[0].dns_target : null
}

