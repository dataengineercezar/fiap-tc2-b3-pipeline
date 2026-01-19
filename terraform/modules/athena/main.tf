resource "aws_athena_workgroup" "main" {
  name  = "${var.project_name}-athena-${var.environment}"
  state = "ENABLED"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.s3_bucket_name}/athena-results/"
    }
  }

  tags = merge(
    var.tags,
    {
      Name      = "${var.project_name}-athena-${var.environment}"
      Component = "Athena"
      Purpose   = "SQL"
    }
  )
}
