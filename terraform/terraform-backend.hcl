profile = "amc_dev"
bucket  = "amc-terraform-state-dev"
key     = "convoy/terraform.tfstate"
region  = "us-east-1"
dynamodb_table = "amc-terraform-locks-dev"
encrypt = true
