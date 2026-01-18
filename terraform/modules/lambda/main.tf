# Lambda Function para Scraping B3
# Acionada via EventBridge Schedule
# Usa S3 para deployment devido ao tamanho do ZIP (>50MB)
resource "aws_lambda_function" "scraping" {
  s3_bucket        = var.s3_bucket_name
  s3_key           = "lambda-deployments/lambda_scraping.zip"
  function_name    = "${var.project_name}-scraping-${var.environment}"
  role             = var.lambda_scraping_role_arn
  handler          = "lambda_scraping.lambda_handler"
  source_code_hash = filebase64sha256("${path.root}/../build/lambda_scraping.zip")
  runtime          = "python3.12"
  timeout          = 300 # 5 minutos
  memory_size      = 512 # MB

  environment {
    variables = {
      TICKER    = var.ticker
      DATASET   = var.dataset
      S3_BUCKET = var.s3_bucket_name
      S3_PREFIX = "raw"
      DAYS      = var.scraping_days
    }
  }

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-lambda-scraping-${var.environment}"
      Component = "Lambda"
      Function  = "DataIngestion"
    }
  )
}

# CloudWatch Log Group para Lambda Scraping
resource "aws_cloudwatch_log_group" "scraping" {
  name              = "/aws/lambda/${aws_lambda_function.scraping.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Lambda Function para Trigger Glue Job
# Será acionada por S3 Event Notification
resource "aws_lambda_function" "trigger_glue" {
  filename         = "${path.root}/../build/lambda_trigger_glue.zip"
  function_name    = "${var.project_name}-trigger-glue-${var.environment}"
  role             = var.lambda_trigger_glue_role_arn
  handler          = "lambda_trigger_glue.lambda_handler"
  source_code_hash = filebase64sha256("${path.root}/../build/lambda_trigger_glue.zip")
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256

  environment {
    variables = {
      GLUE_JOB_NAME = "${var.project_name}-etl-${var.environment}"
    }
  }

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-lambda-trigger-glue-${var.environment}"
      Component = "Lambda"
      Function  = "GlueTrigger"
    }
  )
}

# CloudWatch Log Group para Lambda Trigger Glue
resource "aws_cloudwatch_log_group" "trigger_glue" {
  name              = "/aws/lambda/${aws_lambda_function.trigger_glue.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# S3 Permission para Lambda Trigger Glue ser invocada pelo S3
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_glue.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_bucket_name}"
}
