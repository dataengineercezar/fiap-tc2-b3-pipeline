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
