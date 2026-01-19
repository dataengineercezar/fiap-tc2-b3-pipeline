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

# IAM Roles for Lambda Functions
module "iam" {
  source = "./modules/iam"

  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
  tags          = local.common_tags
}

# Lambda Functions (Scraping + Trigger Glue)
module "lambda" {
  source = "./modules/lambda"

  project_name                 = var.project_name
  environment                  = var.environment
  s3_bucket_name               = var.bucket_name
  lambda_scraping_role_arn     = module.iam.lambda_scraping_role_arn
  lambda_trigger_glue_role_arn = module.iam.lambda_trigger_glue_role_arn
  ticker                       = var.ticker
  dataset                      = var.dataset_name
  scraping_days                = 5
  tags                         = local.common_tags

  depends_on = [module.iam]
}

# EventBridge Schedule for automated scraping
module "eventbridge" {
  source = "./modules/eventbridge"

  project_name         = var.project_name
  environment          = var.environment
  lambda_scraping_arn  = module.lambda.scraping_function_arn
  lambda_scraping_name = module.lambda.scraping_function_name
  schedule_expression  = "cron(0 22 ? * MON-FRI *)" # 19h BRT, dias úteis
  tags                 = local.common_tags

  depends_on = [module.lambda]
}

# Glue ETL Job + Catalog + Crawler
module "glue" {
  source = "./modules/glue"

  project_name   = var.project_name
  environment    = var.environment
  s3_bucket_name = var.bucket_name
  dataset        = var.dataset_name
  ticker         = var.ticker
  glue_version   = "4.0"
  tags           = local.common_tags

  depends_on = [module.s3]
}

# S3 Event Notification para acionar Lambda Trigger Glue
module "s3_notification" {
  source = "./modules/s3_notification"

  s3_bucket_name          = var.bucket_name
  lambda_trigger_glue_arn = module.lambda.trigger_glue_function_arn
  lambda_permission_id    = module.lambda.s3_permission_id

  depends_on = [module.lambda, module.glue]
}

# Athena (Workgroup + local de resultados)
module "athena" {
  source = "./modules/athena"

  project_name   = var.project_name
  environment    = var.environment
  s3_bucket_name = var.bucket_name
  tags           = local.common_tags

  depends_on = [module.s3, module.glue]
}
