variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod, etc.)"
  type        = string
  default     = "prod"
}

variable "notification_email" {
  description = "Email address to receive notifications"
  type        = string
  # You'll set this in terraform.tfvars
}

variable "additional_emails" {
  description = "Additional email addresses for notifications"
  type        = list(string)
  default     = []
}

# variable "notification_phone" {
#   description = "Phone number for SMS notifications (with country code, e.g., +12345678900). Leave empty to disable SMS."
#   type        = string
#   default     = ""
# }

variable "timezone" {
  description = "Your timezone for reference (doesn't affect cron, just for documentation)"
  type        = string
  default     = "America/New_York"
}

variable "morning_cron" {
  description = "Cron expression for morning check (6 AM). UTC time!"
  type        = string
  default     = "cron(0 11 * * ? *)"  # 6 AM EST = 11 AM UTC
  
  # Common timezone conversions (6 AM local time):
  # EST/EDT: cron(0 11 * * ? *)  - 11 AM UTC
  # CST/CDT: cron(0 12 * * ? *)  - 12 PM UTC
  # MST/MDT: cron(0 13 * * ? *)  - 1 PM UTC
  # PST/PDT: cron(0 14 * * ? *)  - 2 PM UTC
}

variable "evening_cron" {
  description = "Cron expression for evening check (6 PM). UTC time!"
  type        = string
  default     = "cron(0 23 * * ? *)"  # 6 PM EST = 11 PM UTC
  
  # Common timezone conversions (6 PM local time):
  # EST/EDT: cron(0 23 * * ? *)  - 11 PM UTC
  # CST/CDT: cron(0 0 * * ? *)   - 12 AM UTC (next day)
  # MST/MDT: cron(0 1 * * ? *)   - 1 AM UTC (next day)
  # PST/PDT: cron(0 2 * * ? *)   - 2 AM UTC (next day)
}
