# S3 Bucket for apex domain redirect (tradequest.tech -> www.tradequest.tech)
resource "aws_s3_bucket" "apex_redirect" {
  count  = var.domain_name != "" ? 1 : 0
  bucket = var.domain_name

  tags = merge(local.common_tags, {
    Name = "${var.domain_name}-apex-redirect"
  })
}

# Configure bucket for website redirect
resource "aws_s3_bucket_website_configuration" "apex_redirect" {
  count  = var.domain_name != "" ? 1 : 0
  bucket = aws_s3_bucket.apex_redirect[0].id

  redirect_all_requests_to {
    host_name = "www.${var.domain_name}"
    protocol  = "https"
  }
}

# Block public access (we'll use CloudFront)
resource "aws_s3_bucket_public_access_block" "apex_redirect" {
  count  = var.domain_name != "" ? 1 : 0
  bucket = aws_s3_bucket.apex_redirect[0].id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Bucket policy for CloudFront access
resource "aws_s3_bucket_policy" "apex_redirect" {
  count  = var.domain_name != "" ? 1 : 0
  bucket = aws_s3_bucket.apex_redirect[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "PublicReadGetObject"
        Effect = "Allow"
        Principal = "*"
        Action = "s3:GetObject"
        Resource = "${aws_s3_bucket.apex_redirect[0].arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.apex_redirect]
}

# Route 53 A record for apex domain pointing to S3 website endpoint
resource "aws_route53_record" "apex_redirect" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_s3_bucket_website_configuration.apex_redirect[0].website_domain
    zone_id                = aws_s3_bucket.apex_redirect[0].hosted_zone_id
    evaluate_target_health = false
  }
}

