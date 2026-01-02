terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# DynamoDB Table for storing processing dates
resource "aws_dynamodb_table" "flag_processing_times" {
  name           = "FLAGProcessingTimes"
  billing_mode   = "PAY_PER_REQUEST"  # On-demand pricing
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "FLAG Processing Times Storage"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# SNS Topic for notifications
resource "aws_sns_topic" "flag_notifications" {
  name = "FLAG-Monitor-Notifications"

  tags = {
    Name        = "FLAG Monitor Notifications"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# SNS Email Subscription
resource "aws_sns_topic_subscription" "email_subscription" {
  topic_arn = aws_sns_topic.flag_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Additional email subscriptions
resource "aws_sns_topic_subscription" "additional_emails" {
  for_each  = toset(var.additional_emails)
  topic_arn = aws_sns_topic.flag_notifications.arn
  protocol  = "email"
  endpoint  = each.value
}

# SNS SMS Subscription (optional)
# resource "aws_sns_topic_subscription" "sms_subscription" {
#   count     = var.notification_phone != "" ? 1 : 0
#   topic_arn = aws_sns_topic.flag_notifications.arn
#   protocol  = "sms"
#   endpoint  = var.notification_phone
# }


# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "FLAG-Monitor-Lambda-Role"

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

  tags = {
    Name        = "FLAG Monitor Lambda Role"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# IAM Policy for Lambda to access DynamoDB
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "FLAG-Monitor-DynamoDB-Policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.flag_processing_times.arn
      }
    ]
  })
}

# IAM Policy for Lambda to publish to SNS
resource "aws_iam_role_policy" "lambda_sns_policy" {
  name = "FLAG-Monitor-SNS-Policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.flag_notifications.arn
      }
    ]
  })
}

# Attach AWS managed policy for Lambda basic execution
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Layer for dependencies (requests, beautifulsoup4)
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "lambda_layer.zip"
  layer_name          = "FLAG-Monitor-Dependencies"
  compatible_runtimes = ["python3.11", "python3.12"]
  
  description = "Dependencies for FLAG Monitor: requests, beautifulsoup4"

  # This will be created by build script
  source_code_hash = fileexists("lambda_layer.zip") ? filebase64sha256("lambda_layer.zip") : null
}

# Lambda Function
resource "aws_lambda_function" "flag_monitor" {
  filename         = "lambda_function.zip"
  function_name    = "FLAG-Monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = fileexists("lambda_function.zip") ? filebase64sha256("lambda_function.zip") : null
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      SNS_TOPIC_ARN   = aws_sns_topic.flag_notifications.arn
      DYNAMODB_TABLE  = aws_dynamodb_table.flag_processing_times.name
    }
  }

  tags = {
    Name        = "FLAG Monitor Function"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy.lambda_dynamodb_policy,
    aws_iam_role_policy.lambda_sns_policy
  ]
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.flag_monitor.function_name}"
  retention_in_days = 7

  tags = {
    Name        = "FLAG Monitor Logs"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# EventBridge Rule for 6 AM check
resource "aws_cloudwatch_event_rule" "morning_check" {
  name                = "FLAG-Monitor-6AM"
  description         = "Trigger FLAG monitor at 6 AM ${var.timezone}"
  schedule_expression = var.morning_cron

  tags = {
    Name        = "FLAG Monitor Morning Schedule"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# EventBridge Target for morning check
resource "aws_cloudwatch_event_target" "morning_lambda" {
  rule      = aws_cloudwatch_event_rule.morning_check.name
  target_id = "FLAGMonitorMorning"
  arn       = aws_lambda_function.flag_monitor.arn
}

# Lambda permission for morning EventBridge rule
resource "aws_lambda_permission" "allow_morning_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeMorning"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flag_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.morning_check.arn
}

# EventBridge Rule for 6 PM check
resource "aws_cloudwatch_event_rule" "evening_check" {
  name                = "FLAG-Monitor-6PM"
  description         = "Trigger FLAG monitor at 6 PM ${var.timezone}"
  schedule_expression = var.evening_cron

  tags = {
    Name        = "FLAG Monitor Evening Schedule"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# EventBridge Target for evening check
resource "aws_cloudwatch_event_target" "evening_lambda" {
  rule      = aws_cloudwatch_event_rule.evening_check.name
  target_id = "FLAGMonitorEvening"
  arn       = aws_lambda_function.flag_monitor.arn
}

# Lambda permission for evening EventBridge rule
resource "aws_lambda_permission" "allow_evening_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeEvening"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flag_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.evening_check.arn
}

# ===========================================
# API Gateway for manual Lambda trigger
# ===========================================

# HTTP API Gateway
resource "aws_apigatewayv2_api" "flag_monitor_api" {
  name          = "FLAG-Monitor-API"
  protocol_type = "HTTP"

  tags = {
    Name        = "FLAG Monitor API"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Default stage with auto-deploy
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.flag_monitor_api.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Name        = "FLAG Monitor API Default Stage"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Lambda integration
resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.flag_monitor_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.flag_monitor.invoke_arn
  integration_method = "POST"
}

# Route to trigger Lambda
resource "aws_apigatewayv2_route" "trigger" {
  api_id    = aws_apigatewayv2_api.flag_monitor_api.id
  route_key = "GET /trigger"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flag_monitor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.flag_monitor_api.execution_arn}/*/*"
}

# Output the trigger URL
output "trigger_url" {
  description = "URL to manually trigger the FLAG Monitor"
  value       = "${aws_apigatewayv2_stage.default.invoke_url}/trigger"
}