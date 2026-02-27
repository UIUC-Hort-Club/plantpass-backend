# ---------------------------------------------------------
# ACM Certificate (must be in us-east-1 for CloudFront)
# ---------------------------------------------------------

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_acm_certificate" "cert" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = var.alternate_names

  tags = {
    application = "plantpass"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ---------------------------------------------------------
# DNS Validation Records (must be created manually in Cloudflare)
# ---------------------------------------------------------

# Output the validation records so you can add them to Cloudflare
output "acm_validation_records" {
  value = {
    for dvo in aws_acm_certificate.cert.domain_validation_options :
    dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
  description = "Add these CNAME records to Cloudflare DNS for certificate validation"
}

# Note: Certificate validation will complete automatically once you add
# the CNAME records to Cloudflare. The certificate will show as "Issued"
# in the AWS ACM console when validation is complete.
