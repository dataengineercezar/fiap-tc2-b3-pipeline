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

variable "dataset" {
  description = "Nome do dataset"
  type        = string
}

variable "ticker" {
  description = "Ticker do ativo"
  type        = string
}

variable "glue_version" {
  description = "Versão do AWS Glue"
  type        = string
  default     = "4.0"
}

variable "tags" {
  description = "Tags comuns para recursos"
  type        = map(string)
  default     = {}
}
