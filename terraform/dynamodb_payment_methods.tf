resource "aws_dynamodb_table" "payment_methods" {
  name         = "payment_methods"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "name"

  attribute {
    name = "name"
    type = "S"
  }

  tags = {
    application = "plantpass"
  }
}
