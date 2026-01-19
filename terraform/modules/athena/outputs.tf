output "workgroup_name" {
  description = "Athena workgroup name"
  value       = aws_athena_workgroup.main.name
}
