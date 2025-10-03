# Storage infrastructure for TradeQuest

# S3 Bucket for file storage
resource "aws_s3_bucket" "main" {
  bucket = "${local.name_prefix}-storage-${random_string.bucket_suffix.result}"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-storage"
  })
}

# Random string for bucket suffix to ensure uniqueness
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server-side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "delete_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "transition_to_ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]  # Configure this to your frontend domain in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# IAM Role for ECS tasks to access S3
resource "aws_iam_role" "ecs_task_s3" {
  name = "${local.name_prefix}-ecs-task-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for S3 access
resource "aws_iam_policy" "ecs_task_s3" {
  name        = "${local.name_prefix}-ecs-task-s3-policy"
  description = "Policy for ECS tasks to access S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

# Attach S3 policy to ECS task role
resource "aws_iam_role_policy_attachment" "ecs_task_s3" {
  role       = aws_iam_role.ecs_task_s3.name
  policy_arn = aws_iam_policy.ecs_task_s3.arn
}

# Store S3 bucket information in AWS Secrets Manager
resource "aws_secretsmanager_secret" "s3" {
  name        = "${local.name_prefix}/s3"
  description = "S3 bucket configuration for TradeQuest"

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "s3" {
  secret_id = aws_secretsmanager_secret.s3.id
  secret_string = jsonencode({
    bucket_name = aws_s3_bucket.main.bucket
    region      = var.aws_region
  })
}
