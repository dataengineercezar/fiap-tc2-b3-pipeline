# Outputs - will be uncommented as modules are created

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

output "s3_raw_prefix" {
  description = "S3 RAW prefix"
  value       = "raw/dataset=${var.dataset_name}/ticker=${var.ticker}/"
}

output "s3_refined_prefix" {
  description = "S3 REFINED prefix"
  value       = "refined/dataset=${var.dataset_name}/ticker=${var.ticker}/"
}

# IAM Outputs
output "lambda_scraping_role_arn" {
  description = "Lambda scraping role ARN"
  value       = module.iam.lambda_scraping_role_arn
}

output "lambda_trigger_glue_role_arn" {
  description = "Lambda trigger Glue role ARN"
  value       = module.iam.lambda_trigger_glue_role_arn
}

# Lambda Outputs
output "lambda_scraping_function_name" {
  description = "Lambda scraping function name"
  value       = module.lambda.scraping_function_name
}

output "lambda_scraping_function_arn" {
  description = "Lambda scraping function ARN"
  value       = module.lambda.scraping_function_arn
}

output "lambda_trigger_glue_function_name" {
  description = "Lambda trigger Glue function name"
  value       = module.lambda.trigger_glue_function_name
}

# EventBridge Outputs
output "eventbridge_schedule_rule_name" {
  description = "EventBridge schedule rule name"
  value       = module.eventbridge.schedule_rule_name
}

output "eventbridge_schedule_expression" {
  description = "EventBridge schedule cron expression"
  value       = module.eventbridge.schedule_expression
}

# output "glue_job_name" {
#   description = "Glue Job name"
#   value       = module.glue.job_name
# }

# output "glue_database_name" {
#   description = "Glue Database name"
#   value       = module.glue.database_name
# }

# output "lambda_function_name" {
#   description = "Lambda function name"
#   value       = module.lambda.function_name
# }

# output "athena_workgroup_name" {
#   description = "Athena workgroup name"
#   value       = module.athena.workgroup_name
# }
