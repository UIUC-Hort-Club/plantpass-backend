terraform {
  backend "s3" {
    bucket = "plantpass-terraform-state"
    key    = "frontend/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
