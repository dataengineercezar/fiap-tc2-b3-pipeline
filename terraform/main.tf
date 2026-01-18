# Main Terraform configuration

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Dataset     = var.dataset_name
    ManagedBy   = "Terraform"
  }
}

# S3 Data Lake Module
module "s3" {
  source = "./modules/s3"

  bucket_name  = var.bucket_name
  environment  = var.environment
  dataset_name = var.dataset_name
  tags         = local.common_tags
}

# Modules will be added in subsequent stages
# module "iam" { ... }
# module "glue" { ... }
# module "lambda" { ... }
# module "athena" { ... }
