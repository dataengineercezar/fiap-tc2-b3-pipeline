# IAM Role para Lambda de Scraping

# Role para Lambda
resource "aws_iam_role" "lambda_scraping" {
  name = "${var.project_name}-lambda-scraping-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-lambda-scraping-role"
    }
  )
}

# Policy para Lambda escrever no S3
resource "aws_iam_role_policy" "lambda_s3_access" {
  name = "lambda-s3-access"
  role = aws_iam_role.lambda_scraping.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${var.s3_bucket_arn}",
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Attach AWS managed policy para CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_scraping.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Role para Lambda Trigger (que inicia Glue Job)
resource "aws_iam_role" "lambda_trigger_glue" {
  name = "${var.project_name}-lambda-trigger-glue-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-lambda-trigger-role"
    }
  )
}

# Policy para Lambda iniciar Glue Job
resource "aws_iam_role_policy" "lambda_start_glue" {
  name = "lambda-start-glue"
  role = aws_iam_role.lambda_trigger_glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach basic execution role para Lambda Trigger
resource "aws_iam_role_policy_attachment" "lambda_trigger_logs" {
  role       = aws_iam_role.lambda_trigger_glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
