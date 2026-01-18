# S3 Module - Data Lake (RAW + REFINED + ATHENA RESULTS)

variable "bucket_name" {
  description = "Nome do bucket S3"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "dataset_name" {
  description = "Nome do dataset"
  type        = string
}

variable "tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}
