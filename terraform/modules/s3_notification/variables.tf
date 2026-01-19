variable "s3_bucket_name" {
  description = "Nome do bucket S3"
  type        = string
}

variable "lambda_trigger_glue_arn" {
  description = "ARN da Lambda que aciona Glue"
  type        = string
}

variable "lambda_permission_id" {
  description = "ID da permissão Lambda (para depends_on)"
  type        = string
}
