# S3 Bucket para Data Lake B3 Pipeline

resource "aws_s3_bucket" "data_lake" {
  bucket = var.bucket_name

  tags = merge(
    var.tags,
    {
      Name        = var.bucket_name
      Purpose     = "B3 Data Lake - RAW/REFINED/ATHENA"
      Environment = var.environment
    }
  )
}

# Versionamento (boas práticas)
resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption at rest (boas práticas)
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloquear acesso público (segurança)
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy para otimização de custos (opcional)
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "transition-old-raw-data"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "expire-athena-results"
    status = "Enabled"

    filter {
      prefix = "athena-results/"
    }

    expiration {
      days = 30
    }
  }
}

# Event notification para Lambda (será usado na Etapa 3 - Requisito R3)
resource "aws_s3_bucket_notification" "data_lake_events" {
  bucket = aws_s3_bucket.data_lake.id

  # Será configurado na próxima etapa quando criar Lambda
  # lambda_function {
  #   lambda_function_arn = var.lambda_function_arn
  #   events              = ["s3:ObjectCreated:*"]
  #   filter_prefix       = "raw/"
  #   filter_suffix       = ".parquet"
  # }
}
