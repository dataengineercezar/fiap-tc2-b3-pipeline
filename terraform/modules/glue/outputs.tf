output "glue_job_name" {
  description = "Nome do Glue Job"
  value       = aws_glue_job.etl.name
}

output "glue_job_arn" {
  description = "ARN do Glue Job"
  value       = aws_glue_job.etl.arn
}

output "glue_role_arn" {
  description = "ARN da IAM Role do Glue"
  value       = aws_iam_role.glue_job.arn
}

output "glue_database_name" {
  description = "Nome do Glue Catalog Database"
  value       = aws_glue_catalog_database.main.name
}

output "glue_crawler_name" {
  description = "Nome do Glue Crawler"
  value       = aws_glue_crawler.refined.name
}

output "glue_script_s3_path" {
  description = "Caminho do script no S3"
  value       = "s3://${var.s3_bucket_name}/${aws_s3_object.glue_script.key}"
}
