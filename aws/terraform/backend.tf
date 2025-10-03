terraform {
  backend "s3" {
    bucket = "tradequest-terraform-state-20251002"
    key    = "tradequest/terraform.tfstate"
    region = "us-east-1"
  }
}
