output "schedule_rule_name" {
  description = "Nome da regra de agendamento"
  value       = aws_cloudwatch_event_rule.scraping_schedule.name
}

output "schedule_rule_arn" {
  description = "ARN da regra de agendamento"
  value       = aws_cloudwatch_event_rule.scraping_schedule.arn
}

output "schedule_expression" {
  description = "Expressão cron do agendamento"
  value       = aws_cloudwatch_event_rule.scraping_schedule.schedule_expression
}
