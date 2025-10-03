# Google Workspace DNS Records for tradequest.tech

# MX Records for Gmail
resource "aws_route53_record" "mx" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = 3600

  records = [
    "1 ASPMX.L.GOOGLE.COM",
    "5 ALT1.ASPMX.L.GOOGLE.COM",
    "5 ALT2.ASPMX.L.GOOGLE.COM",
    "10 ALT3.ASPMX.L.GOOGLE.COM",
    "10 ALT4.ASPMX.L.GOOGLE.COM"
  ]
}

# SPF Record for Email Authentication
resource "aws_route53_record" "spf" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = 3600

  records = [
    "v=spf1 include:_spf.google.com ~all"
  ]
}

# CNAME Records for Google Services
resource "aws_route53_record" "mail_cname" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "mail.${var.domain_name}"
  type    = "CNAME"
  ttl     = 3600
  records = ["ghs.googlehosted.com"]
}

resource "aws_route53_record" "calendar_cname" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "calendar.${var.domain_name}"
  type    = "CNAME"
  ttl     = 3600
  records = ["ghs.googlehosted.com"]
}

resource "aws_route53_record" "drive_cname" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "drive.${var.domain_name}"
  type    = "CNAME"
  ttl     = 3600
  records = ["ghs.googlehosted.com"]
}

resource "aws_route53_record" "sites_cname" {
  count = var.domain_name != "" ? 1 : 0

  zone_id = var.route53_zone_id
  name    = "sites.${var.domain_name}"
  type    = "CNAME"
  ttl     = 3600
  records = ["ghs.googlehosted.com"]
}

