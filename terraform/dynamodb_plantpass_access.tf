resource "aws_dynamodb_table" "plantpass_access" {
  name           = "PlantPass-Access"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "config_id"

  attribute {
    name = "config_id"
    type = "S"
  }

  tags = {
    Name        = "PlantPass-Access"
    Environment = "production"
  }
}
