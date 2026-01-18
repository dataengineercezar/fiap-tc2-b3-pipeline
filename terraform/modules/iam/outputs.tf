output "lambda_scraping_role_arn" {
  description = "ARN da IAM Role para Lambda de scraping"
  value       = aws_iam_role.lambda_scraping.arn
}

output "lambda_scraping_role_name" {
  description = "Nome da IAM Role para Lambda de scraping"
  value       = aws_iam_role.lambda_scraping.name
}

output "lambda_trigger_glue_role_arn" {
  description = "ARN da IAM Role para Lambda trigger Glue"
  value       = aws_iam_role.lambda_trigger_glue.arn
}

output "lambda_trigger_glue_role_name" {
  description = "Nome da IAM Role para Lambda trigger Glue"
  value       = aws_iam_role.lambda_trigger_glue.name
}
