output "notification_id" {
  description = "ID da notificação S3"
  value       = aws_s3_bucket_notification.lambda_trigger.id
}
