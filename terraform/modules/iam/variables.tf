# IAM Module - Roles and Policies for Lambda and Glue

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
