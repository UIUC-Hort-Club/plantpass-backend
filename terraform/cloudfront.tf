# -------------------------
# CloudFront OAI
# -------------------------
resource "aws_cloudfront_origin_access_identity" "oai" {
  comment = "OAI for PlantPass frontend"
}

# -------------------------
# CloudFront Distribution
# -------------------------
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  comment             = "PlantPass React frontend"

  # -------------------------
  # Custom domains (only add after certificate is validated)
  # -------------------------
  aliases = var.enable_custom_domain ? concat([var.domain_name], var.alternate_names) : []

  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3-PlantPass"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oai.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-PlantPass"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      cookies {
        forward = "none"
      }
    }
  }

  # -------------------------
  # Custom error response for SPA routing
  # -------------------------
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # -------------------------
  # Use ACM certificate for custom domain (or default CloudFront cert)
  # -------------------------
  viewer_certificate {
    acm_certificate_arn      = var.enable_custom_domain ? aws_acm_certificate.cert.arn : null
    ssl_support_method       = var.enable_custom_domain ? "sni-only" : null
    minimum_protocol_version = var.enable_custom_domain ? "TLSv1.2_2021" : "TLSv1"
    cloudfront_default_certificate = !var.enable_custom_domain
  }

  tags = {
    application = "plantpass"
  }
}

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "The CloudFront distribution domain name"
}

output "cloudfront_distribution_id" {
  value       = aws_cloudfront_distribution.frontend.id
  description = "The CloudFront distribution ID"
}
