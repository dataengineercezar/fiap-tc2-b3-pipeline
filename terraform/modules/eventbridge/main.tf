# EventBridge Scheduler para acionar Lambda de scraping diariamente
# Execução: Segunda a Sexta às 19h BRT (22h UTC)
# Atende requisito de automação: scraping diário sem intervenção manual

resource "aws_cloudwatch_event_rule" "scraping_schedule" {
  name                = "${var.project_name}-scraping-schedule-${var.environment}"
  description         = "Aciona Lambda de scraping diariamente após fechamento B3"
  schedule_expression = var.schedule_expression

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-scraping-schedule-${var.environment}"
      Component = "EventBridge"
      Purpose   = "AutomatedScraping"
    }
  )
}

resource "aws_cloudwatch_event_target" "lambda_scraping" {
  rule      = aws_cloudwatch_event_rule.scraping_schedule.name
  target_id = "LambdaScraping"
  arn       = var.lambda_scraping_arn

  input = jsonencode({
    source    = "eventbridge-schedule"
    timestamp = "$$.time"
  })
}

# Permissão para EventBridge invocar Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_scraping_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scraping_schedule.arn
}
