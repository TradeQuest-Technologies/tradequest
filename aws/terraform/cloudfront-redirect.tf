# CloudFront distribution for apex domain HTTPS redirect
# This allows https://tradequest.tech to redirect to https://www.tradequest.tech

# Request ACM certificate for apex domain
resource "aws_acm_certificate" "apex_redirect" {
  count             = var.domain_name != "" ? 1 : 0
  provider          = aws.us_east_1  # CloudFront requires certificates in us-east-1
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.domain_name}-apex-redirect-cert"
  })
}

# DNS validation for apex certificate
resource "aws_route53_record" "apex_cert_validation" {
  for_each = var.domain_name != "" ? {
    for dvo in aws_acm_certificate.apex_redirect[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  } : {}

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# Wait for certificate validation
resource "aws_acm_certificate_validation" "apex_redirect" {
  count                   = var.domain_name != "" ? 1 : 0
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.apex_redirect[0].arn
  validation_record_fqdns = [for record in aws_route53_record.apex_cert_validation : record.fqdn]
}

# CloudFront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "apex_redirect" {
  count   = var.domain_name != "" ? 1 : 0
  comment = "OAI for ${var.domain_name} apex redirect"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "apex_redirect" {
  count   = var.domain_name != "" ? 1 : 0
  enabled = true
  aliases = [var.domain_name]

  origin {
    domain_name = aws_s3_bucket_website_configuration.apex_redirect[0].website_endpoint
    origin_id   = "S3-${var.domain_name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${var.domain_name}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.apex_redirect[0].arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = merge(local.common_tags, {
    Name = "${var.domain_name}-apex-redirect-cf"
  })

  depends_on = [aws_acm_certificate_validation.apex_redirect]
}

# Update Route 53 A record to point to CloudFront instead of S3
resource "aws_route53_record" "apex_cloudfront" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.apex_redirect[0].domain_name
    zone_id                = aws_cloudfront_distribution.apex_redirect[0].hosted_zone_id
    evaluate_target_health = false
  }
}
