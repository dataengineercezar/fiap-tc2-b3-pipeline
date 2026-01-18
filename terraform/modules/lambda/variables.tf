variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod)"
  type        = string
}

variable "s3_bucket_name" {
  description = "Nome do bucket S3 data lake"
  type        = string
}

variable "lambda_scraping_role_arn" {
  description = "ARN da role IAM para Lambda de scraping"
  type        = string
}

variable "lambda_trigger_glue_role_arn" {
  description = "ARN da role IAM para Lambda que aciona Glue"
  type        = string
}

variable "ticker" {
  description = "Ticker do ativo (ex: PETR4)"
  type        = string
  default     = "PETR4"
}

variable "dataset" {
  description = "Nome do dataset"
  type        = string
  default     = "petr4"
}

variable "scraping_days" {
  description = "Número de dias para buscar no scraping (últimos N dias)"
  type        = number
  default     = 5
}

variable "tags" {
  description = "Tags comuns para recursos"
  type        = map(string)
  default     = {}
}
