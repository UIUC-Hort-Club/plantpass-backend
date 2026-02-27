resource "aws_dynamodb_table" "discounts" {
  name         = "discounts"
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

resource "aws_dynamodb_table" "products" {
  name         = "products"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "SKU"

  attribute {
    name = "SKU"
    type = "S"
  }

  tags = {
    application = "plantpass"
  }
}

resource "aws_dynamodb_table" "transactions" {
  name         = "transactions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "purchase_id"

  attribute {
    name = "purchase_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  attribute {
    name = "payment_status"
    type = "S"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  # New GSI for efficient unpaid transactions query
  global_secondary_index {
    name            = "payment-status-timestamp-index"
    hash_key        = "payment_status"
    range_key       = "timestamp"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    application = "plantpass"
  }
}
