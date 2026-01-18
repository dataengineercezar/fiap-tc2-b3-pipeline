output "bucket_name" {
  description = "Nome do bucket S3"
  value       = aws_s3_bucket.data_lake.id
}

output "bucket_arn" {
  description = "ARN do bucket S3"
  value       = aws_s3_bucket.data_lake.arn
}

output "bucket_domain_name" {
  description = "Domain name do bucket"
  value       = aws_s3_bucket.data_lake.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name"
  value       = aws_s3_bucket.data_lake.bucket_regional_domain_name
}
