# ---------------------------------------------------------
# DNS is managed in Cloudflare (domain registered with Cloudflare)
# ---------------------------------------------------------

# Instructions for Cloudflare DNS setup:
# 1. Add ACM validation CNAME records (see acm_validation_records output)
# 2. Once certificate validates, add these CNAME records:
#    - Name: @ (or hortclubplantpass.org)
#    - Target: <cloudfront_domain_name from output>
#    - Proxy status: DNS only (grey cloud, not orange)
#
#    - Name: www
#    - Target: <cloudfront_domain_name from output>
#    - Proxy status: DNS only (grey cloud, not orange)
#
# Note: Cloudflare will automatically flatten the root CNAME to work properly
