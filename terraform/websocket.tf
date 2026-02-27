# -------------------------
# WebSocket API Gateway for Real-time Updates
# -------------------------
resource "aws_apigatewayv2_api" "websocket_api" {
  name                       = "PlantPassWebSocket"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# WebSocket Stages
# -------------------------
resource "aws_apigatewayv2_stage" "websocket_stage" {
  api_id      = aws_apigatewayv2_api.websocket_api.id
  name        = "production"
  auto_deploy = true

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# WebSocket Lambda Integration
# -------------------------
resource "aws_apigatewayv2_integration" "websocket_connect" {
  api_id             = aws_apigatewayv2_api.websocket_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.websocket_handler.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "websocket_disconnect" {
  api_id             = aws_apigatewayv2_api.websocket_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.websocket_handler.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "websocket_default" {
  api_id             = aws_apigatewayv2_api.websocket_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.websocket_handler.invoke_arn
  integration_method = "POST"
}

# -------------------------
# WebSocket Routes
# -------------------------
resource "aws_apigatewayv2_route" "connect_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_disconnect.id}"
}

resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_default.id}"
}

# -------------------------
# Lambda Permission for WebSocket API
# -------------------------
resource "aws_lambda_permission" "websocket_apigw" {
  statement_id  = "AllowWebSocketAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/*"
}

# -------------------------
# WebSocket Lambda Function
# -------------------------
resource "aws_lambda_function" "websocket_handler" {
  function_name    = "WebSocketHandler"
  filename         = var.websocket_lambda_zip_path
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec.arn
  source_code_hash = filebase64sha256(var.websocket_lambda_zip_path)

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.websocket_connections.name
    }
  }

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# CloudWatch Log Group for WebSocket Lambda
# -------------------------
resource "aws_cloudwatch_log_group" "websocket_handler_logs" {
  name              = "/aws/lambda/WebSocketHandler"
  retention_in_days = 14

  tags = {
    application = "plantpass"
  }
}

# -------------------------
# IAM Policy for WebSocket Management
# -------------------------
resource "aws_iam_role_policy" "lambda_websocket_management" {
  name = "LambdaWebSocketManagement"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/*/@connections/*"
      }
    ]
  })
}

# -------------------------
# Outputs
# -------------------------
output "websocket_endpoint" {
  value       = "${aws_apigatewayv2_api.websocket_api.api_endpoint}/${aws_apigatewayv2_stage.websocket_stage.name}"
  description = "WebSocket endpoint for real-time updates"
}
