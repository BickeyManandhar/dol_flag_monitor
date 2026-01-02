output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.flag_monitor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.flag_monitor.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for notifications"
  value       = aws_sns_topic.flag_notifications.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.flag_processing_times.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda logs"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "morning_schedule_name" {
  description = "Name of the morning EventBridge schedule"
  value       = aws_cloudwatch_event_rule.morning_check.name
}

output "evening_schedule_name" {
  description = "Name of the evening EventBridge schedule"
  value       = aws_cloudwatch_event_rule.evening_check.name
}

output "notification_instructions" {
  description = "Next steps after deployment"
  value       = <<-EOT
  
  ===================================================================
  FLAG Monitor Deployed Successfully! 
  ===================================================================
  
  IMPORTANT: Check your email (${var.notification_email}) and confirm the SNS subscription!
  
  Resources Created:
  - Lambda Function: ${aws_lambda_function.flag_monitor.function_name}
  - DynamoDB Table: ${aws_dynamodb_table.flag_processing_times.name}
  - SNS Topic: ${aws_sns_topic.flag_notifications.name}
  - Morning Check: ${var.morning_cron}
  - Evening Check: ${var.evening_cron}
  
  Next Steps:
  1. Check your email for SNS subscription confirmation
  2. Click the confirmation link in the email
  3. Test the function: aws lambda invoke --function-name ${aws_lambda_function.flag_monitor.function_name} response.json
  4. View logs: aws logs tail /aws/lambda/${aws_lambda_function.flag_monitor.function_name} --follow
  
  The monitor will automatically check at 6 AM and 6 PM ${var.timezone}
  
  ===================================================================
  EOT
}
