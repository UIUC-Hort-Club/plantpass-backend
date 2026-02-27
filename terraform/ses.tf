# -------------------------
# SES Email Configuration
# -------------------------

# Note: Email identities must be manually verified in AWS SES Console
# Terraform will not create/verify them to avoid permission issues

# IAM Policy for Lambda to send emails via SES
resource "aws_iam_role_policy" "lambda_ses_access" {
  name = "LambdaSESAccess"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Policy for AdminPassword Lambda to invoke Email Lambda
resource "aws_iam_role_policy" "lambda_invoke_email" {
  name = "LambdaInvokeEmailLambda"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.email_handler.arn
      }
    ]
  })
}
