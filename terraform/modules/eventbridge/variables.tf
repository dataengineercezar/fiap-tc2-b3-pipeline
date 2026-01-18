variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, prod)"
  type        = string
}

variable "lambda_scraping_arn" {
  description = "ARN da função Lambda de scraping"
  type        = string
}

variable "lambda_scraping_name" {
  description = "Nome da função Lambda de scraping"
  type        = string
}

variable "schedule_expression" {
  description = "Expressão cron para agendamento (UTC)"
  type        = string
  default     = "cron(0 22 ? * MON-FRI *)" # 19h BRT (22h UTC), dias úteis
}

variable "tags" {
  description = "Tags comuns para recursos"
  type        = map(string)
  default     = {}
}
