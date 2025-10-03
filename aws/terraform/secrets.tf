# Secrets Manager configuration for TradeQuest

# Main application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  name        = "${local.name_prefix}/app"
  description = "Application secrets for TradeQuest"

  tags = local.common_tags
}

# Store application secrets
resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    # JWT Configuration
    JWT_SECRET = random_password.jwt_secret.result
    
    # External API Keys
    OPENAI_API_KEY     = var.openai_api_key
    STRIPE_SECRET_KEY  = var.stripe_secret_key
    STRIPE_WEBHOOK_SECRET = var.stripe_webhook_secret
    
    # Email Configuration
    SMTP_USERNAME = var.smtp_username
    SMTP_PASSWORD = var.smtp_password
    
    # SMS Configuration
    TWILIO_ACCOUNT_SID = var.twilio_account_sid
    TWILIO_AUTH_TOKEN  = var.twilio_auth_token
    TWILIO_PHONE_NUMBER = var.twilio_phone_number
    
    # Google OAuth
    GOOGLE_CLIENT_ID     = var.google_client_id
    GOOGLE_CLIENT_SECRET = var.google_client_secret
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = var.telegram_bot_token
    
    # Market Data APIs
    ALPHA_VANTAGE_API_KEY = var.alpha_vantage_api_key
    POLYGON_API_KEY       = var.polygon_api_key
    POLYGON_S3_ACCESS_KEY = var.polygon_s3_access_key
    POLYGON_S3_SECRET_KEY = var.polygon_s3_secret_key
    
    # Frontend URL
    FRONTEND_URL = var.domain_name != "" ? "https://${var.domain_name}" : "http://localhost:3000"
  })
}

# Random password for JWT secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

# Variables for secrets (these should be set via environment variables or terraform.tfvars)
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "smtp_username" {
  description = "SMTP username for email"
  type        = string
  default     = ""
  sensitive   = true
}

variable "smtp_password" {
  description = "SMTP password for email"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_account_sid" {
  description = "Twilio account SID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_auth_token" {
  description = "Twilio auth token"
  type        = string
  default     = ""
  sensitive   = true
}

variable "twilio_phone_number" {
  description = "Twilio phone number"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Telegram bot token"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "polygon_api_key" {
  description = "Polygon API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "polygon_s3_access_key" {
  description = "Polygon S3 access key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "polygon_s3_secret_key" {
  description = "Polygon S3 secret key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
  default     = ""
}
