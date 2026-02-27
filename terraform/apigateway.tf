# -------------------------
# API Gateway for Frontend Application
# -------------------------
resource "aws_apigatewayv2_api" "frontend_api" {
  name          = "PlantPassAPI"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization"]
  }

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# Lambda Integrations
# -------------------------
resource "aws_apigatewayv2_integration" "transaction_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.transaction_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "admin_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.admin.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "products_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.products_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "discounts_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.discounts_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "payment_methods_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.payment_methods_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "lock_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.lock_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "feature_toggles_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.feature_toggles_handler.arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "plantpass_access_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.plantpass_access_handler.arn
  payload_format_version = "2.0"
}

# -------------------------
# API Gateway Stage
# -------------------------
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.frontend_api.id
  name        = "$default"
  auto_deploy = true

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# Transaction Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "create_transaction" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /transactions"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "read_transaction" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /transactions/{purchase_id}"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_transaction" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /transactions/{purchase_id}"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_transaction" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "DELETE /transactions/{purchase_id}"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "sales_analytics" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /transactions/sales-analytics"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "export_transactions" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /transactions/export-data"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "clear_transactions" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "DELETE /transactions/clear-all"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "recent_unpaid_transactions" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /transactions/recent-unpaid"
  target    = "integrations/${aws_apigatewayv2_integration.transaction_lambda_integration.id}"
}

# -------------------------
# Admin Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "admin_login_route" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /admin/login"
  target    = "integrations/${aws_apigatewayv2_integration.admin_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "admin_change_route" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /admin/change-password"
  target    = "integrations/${aws_apigatewayv2_integration.admin_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "admin_reset_route" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /admin/reset-password"
  target    = "integrations/${aws_apigatewayv2_integration.admin_lambda_integration.id}"
}

# -------------------------
# Products Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_products" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /products"
  target    = "integrations/${aws_apigatewayv2_integration.products_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "replace_all_products" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /products"
  target    = "integrations/${aws_apigatewayv2_integration.products_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "create_product" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /products"
  target    = "integrations/${aws_apigatewayv2_integration.products_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_product" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /products/{SKU}"
  target    = "integrations/${aws_apigatewayv2_integration.products_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_product" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "DELETE /products/{SKU}"
  target    = "integrations/${aws_apigatewayv2_integration.products_lambda_integration.id}"
}

# -------------------------
# Discounts Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_discounts" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /discounts"
  target    = "integrations/${aws_apigatewayv2_integration.discounts_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "replace_all_discounts" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /discounts"
  target    = "integrations/${aws_apigatewayv2_integration.discounts_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "create_discount" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /discounts"
  target    = "integrations/${aws_apigatewayv2_integration.discounts_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_discount" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /discounts/{name}"
  target    = "integrations/${aws_apigatewayv2_integration.discounts_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_discount" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "DELETE /discounts/{name}"
  target    = "integrations/${aws_apigatewayv2_integration.discounts_lambda_integration.id}"
}

# -------------------------
# Payment Methods Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_payment_methods" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /payment-methods"
  target    = "integrations/${aws_apigatewayv2_integration.payment_methods_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "replace_all_payment_methods" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /payment-methods"
  target    = "integrations/${aws_apigatewayv2_integration.payment_methods_lambda_integration.id}"
}

# -------------------------
# Lock Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_lock_state" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /lock/{resourceType}"
  target    = "integrations/${aws_apigatewayv2_integration.lock_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "set_lock_state" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /lock/{resourceType}"
  target    = "integrations/${aws_apigatewayv2_integration.lock_lambda_integration.id}"
}

# -------------------------
# Feature Toggles Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_feature_toggles" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /feature-toggles"
  target    = "integrations/${aws_apigatewayv2_integration.feature_toggles_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "set_feature_toggles" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /feature-toggles"
  target    = "integrations/${aws_apigatewayv2_integration.feature_toggles_lambda_integration.id}"
}

# -------------------------
# PlantPass Access Lambda Routes
# -------------------------
resource "aws_apigatewayv2_route" "get_plantpass_access" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "GET /plantpass-access"
  target    = "integrations/${aws_apigatewayv2_integration.plantpass_access_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "set_plantpass_access" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "PUT /plantpass-access"
  target    = "integrations/${aws_apigatewayv2_integration.plantpass_access_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "verify_plantpass_access" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /plantpass-access/verify"
  target    = "integrations/${aws_apigatewayv2_integration.plantpass_access_lambda_integration.id}"
}

# -------------------------
# Outputs
# -------------------------
output "api_endpoint" {
  value       = aws_apigatewayv2_stage.default.invoke_url
  description = "API Gateway endpoint for frontend and admin"
}

# -------------------------
# Email Routes
# -------------------------
resource "aws_apigatewayv2_route" "email_receipt" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /email/receipt"
  target    = "integrations/${aws_apigatewayv2_integration.email_lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "email_password_reset" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /email/password-reset"
  target    = "integrations/${aws_apigatewayv2_integration.email_lambda_integration.id}"
}

resource "aws_apigatewayv2_integration" "email_lambda_integration" {
  api_id                 = aws_apigatewayv2_api.frontend_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.email_handler.arn
  payload_format_version = "2.0"
}

# -------------------------
# Admin Forgot Password Route
# -------------------------
resource "aws_apigatewayv2_route" "admin_forgot_password" {
  api_id    = aws_apigatewayv2_api.frontend_api.id
  route_key = "POST /admin/forgot-password"
  target    = "integrations/${aws_apigatewayv2_integration.admin_lambda_integration.id}"
}
