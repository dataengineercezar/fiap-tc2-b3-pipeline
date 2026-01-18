output "scraping_function_arn" {
  description = "ARN da função Lambda de scraping"
  value       = aws_lambda_function.scraping.arn
}

output "scraping_function_name" {
  description = "Nome da função Lambda de scraping"
  value       = aws_lambda_function.scraping.function_name
}

output "trigger_glue_function_arn" {
  description = "ARN da função Lambda que aciona Glue"
  value       = aws_lambda_function.trigger_glue.arn
}

output "trigger_glue_function_name" {
  description = "Nome da função Lambda que aciona Glue"
  value       = aws_lambda_function.trigger_glue.function_name
}
