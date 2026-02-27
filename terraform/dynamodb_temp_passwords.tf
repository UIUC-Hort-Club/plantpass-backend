# -------------------------
# DynamoDB Table for Temporary Passwords
# -------------------------

resource "aws_dynamodb_table" "temp_passwords" {
  name         = "temp_passwords"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    attribute_name = "expiration"
    enabled        = true
  }

  tags = {
    application = "plantpass"
  }
}
