# DNS Validation Records for App Runner Custom Domain
# These are automatically created by App Runner for SSL certificate validation

# Validation record 1 (apex domain)
resource "aws_route53_record" "apprunner_validation_1" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "_df4d97b82ec52e8beb3c9d5fbafc68fb.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = ["_602ffbaaeb2cfb2ee23451a215934ef5.xlfgrmvvlj.acm-validations.aws."]
}

# Validation record 2 (www subdomain)
resource "aws_route53_record" "apprunner_validation_2" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "_181418a87be3811d29aaedd7335ba19c.www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = ["_cc19711a1c5aebc1a16245708475b777.xlfgrmvvlj.acm-validations.aws."]
}

# Validation record 3 (App Runner internal)
resource "aws_route53_record" "apprunner_validation_3" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "_c1b5eac642a3d4f2db2fc668780d21ae.2a57j78hsrstljvqlux8inqlkmoufug.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = ["_78205203eb64f38d59b9463012291769.xlfgrmvvlj.acm-validations.aws."]
}

# Point www subdomain to App Runner
# Note: Cannot use CNAME at apex (tradequest.tech) - use www.tradequest.tech instead
resource "aws_route53_record" "apprunner_www" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [aws_apprunner_service.frontend.service_url]
}

