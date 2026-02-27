resource "aws_dynamodb_table" "locks" {
  name         = "PlantPass-Locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "resource_type"

  attribute {
    name = "resource_type"
    type = "S"
  }

  tags = {
    application = "plantpass"
    purpose     = "resource-locking"
  }
}
