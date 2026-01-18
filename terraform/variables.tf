variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "sa-east-1"
}

variable "aws_profile" {
  description = "AWS CLI Profile to use (optional, leave empty for default credentials)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "b3-pipeline"
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "pos-tech-b3-pipeline-cezar-2026"
}

variable "dataset_name" {
  description = "Dataset name"
  type        = string
  default     = "petr4"
}

variable "ticker" {
  description = "Stock ticker symbol"
  type        = string
  default     = "petr4"
}

variable "glue_database_name" {
  description = "Glue Catalog database name"
  type        = string
  default     = "b3_database"
}

variable "glue_table_name" {
  description = "Glue Catalog table name"
  type        = string
  default     = "refined_petr4_petr4"
}
