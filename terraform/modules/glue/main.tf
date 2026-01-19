# IAM Role para Glue Job
resource "aws_iam_role" "glue_job" {
  name = "${var.project_name}-glue-job-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-glue-job-role"
    }
  )
}

# Policy para acesso S3
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-s3-access"
  role = aws_iam_role.glue_job.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      }
    ]
  })
}

# Policy para permitir que o próprio job dispare o crawler ao final (R7)
resource "aws_iam_role_policy" "glue_crawler_control" {
  name = "glue-crawler-control"
  role = aws_iam_role.glue_job.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "glue:StartCrawler",
          "glue:GetCrawler",
          "glue:GetCrawlerMetrics"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach AWS managed policy para Glue Service
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_job.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Upload script Python para S3
resource "aws_s3_object" "glue_script" {
  bucket = var.s3_bucket_name
  key    = "glue-scripts/glue_etl_job.py"
  source = "${path.root}/../src/glue/glue_etl_job.py"
  etag   = filemd5("${path.root}/../src/glue/glue_etl_job.py")

  tags = var.tags
}

# Glue Job ETL
resource "aws_glue_job" "etl" {
  name              = "${var.project_name}-etl-${var.environment}"
  role_arn          = aws_iam_role.glue_job.arn
  glue_version      = var.glue_version
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 60 # 60 minutos

  command {
    name            = "glueetl"
    script_location = "s3://${var.s3_bucket_name}/${aws_s3_object.glue_script.key}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.s3_bucket_name}/glue-spark-logs/"
    "--TempDir"                          = "s3://${var.s3_bucket_name}/glue-temp/"
    "--S3_BUCKET"                        = var.s3_bucket_name
    "--DATASET"                          = var.dataset
    "--TICKER"                           = var.ticker
    "--CRAWLER_NAME"                      = aws_glue_crawler.refined.name
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-glue-etl-${var.environment}"
      Component = "Glue"
      Purpose   = "ETL"
    }
  )
}

# Glue Catalog Database
resource "aws_glue_catalog_database" "main" {
  name        = "${var.project_name}-db-${var.environment}"
  description = "Database for ${var.project_name} refined data"

  tags = var.tags
}

# Glue Crawler para catalogar dados refined
resource "aws_glue_crawler" "refined" {
  name          = "${var.project_name}-crawler-refined-${var.environment}"
  role          = aws_iam_role.glue_job.arn
  database_name = aws_glue_catalog_database.main.name

  s3_target {
    # Para manter o ambiente de apresentação "limpo" (uma tabela principal),
    # apontamos o crawler para o prefixo do dataset.
    path = "s3://${var.s3_bucket_name}/refined/dataset=${var.dataset}/"
  }

  schedule = "cron(0 23 ? * MON-FRI *)" # 20h BRT (23h UTC), após o Glue Job

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-crawler-refined-${var.environment}"
      Component = "Glue"
      Purpose   = "DataCatalog"
    }
  )
}

# CloudWatch Log Group para Glue Job
resource "aws_cloudwatch_log_group" "glue_job" {
  name              = "/aws-glue/jobs/${aws_glue_job.etl.name}"
  retention_in_days = 7

  tags = var.tags
}
