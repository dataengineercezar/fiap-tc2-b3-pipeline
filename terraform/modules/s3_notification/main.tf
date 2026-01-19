# S3 Event Notification para acionar Lambda Trigger Glue
# Atende Requisito R3: Bucket aciona Lambda que chama Glue Job

resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = var.s3_bucket_name

  lambda_function {
    lambda_function_arn = var.lambda_trigger_glue_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/dataset="
    filter_suffix       = ".parquet"
  }

  depends_on = [var.lambda_permission_id]
}
