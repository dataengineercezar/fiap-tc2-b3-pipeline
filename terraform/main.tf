# Main Terraform configuration

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Dataset     = var.dataset_name
  }
}

# Modules will be added in subsequent stages
# module "s3" { ... }
# module "iam" { ... }
# module "glue" { ... }
# module "lambda" { ... }
# module "athena" { ... }
