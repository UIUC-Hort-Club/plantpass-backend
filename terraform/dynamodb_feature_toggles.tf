resource "aws_dynamodb_table" "feature_toggles" {
  name         = "PlantPass-FeatureToggles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "config_id"

  attribute {
    name = "config_id"
    type = "S"
  }

  tags = {
    application = "plantpass"
    purpose     = "feature-toggles"
  }
}
