# FLAG Monitor - Complete Step-by-Step Deployment Guide

This guide assumes you're starting from scratch and will walk you through EVERYTHING including AWS credentials.

---

## Part 1: Prerequisites Setup (15-20 minutes)

### Step 1.1: Install Terraform

**Check if already installed:**
```bash
terraform version
```

**If not installed:**

**On Mac (using Homebrew):**
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**On Windows:**
1. Download from: https://www.terraform.io/downloads
2. Extract the zip file
3. Move `terraform.exe` to `C:\Windows\System32\` (or add to PATH)

**On Linux:**
```bash
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

**Verify:**
```bash
terraform version
# Should show: Terraform v1.x.x
```

---

### Step 1.2: Install AWS CLI

**Check if already installed:**
```bash
aws --version
```

**If not installed:**

**On Mac:**
```bash
brew install awscli
```

**On Windows:**
1. Download: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run the installer

**On Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Verify:**
```bash
aws --version
# Should show: aws-cli/2.x.x
```

---

### Step 1.3: Setup AWS Credentials

This is how Terraform will authenticate to your AWS account!

#### Option A: Using AWS CLI Configure (RECOMMENDED - Easiest)

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: <paste your access key>
AWS Secret Access Key [None]: <paste your secret key>
Default region name [None]: us-east-1
Default output format [None]: json
```

**Where to get Access Keys:**

1. **Login to AWS Console:** https://console.aws.amazon.com/
2. Click your username (top right) → **Security credentials**
3. Scroll to "Access keys" section
4. Click **"Create access key"**
5. Choose **"Command Line Interface (CLI)"**
6. Check the confirmation box
7. Click **"Create access key"**
8. **IMPORTANT:** Copy both:
   - Access key ID (looks like: `AKIAIOSFODNN7EXAMPLE`)
   - Secret access key (looks like: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
9. **Save these somewhere safe!** You can't see the secret key again.

**Test your credentials:**
```bash
aws sts get-caller-identity
```

Should show something like:
```json
{
    "UserId": "AIDAI...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

✅ **If you see this, Terraform can now access your AWS account!**

---

#### Option B: Using Environment Variables (Alternative)

If you prefer not to use `aws configure`, you can set environment variables:

**On Mac/Linux:**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-here"
export AWS_SECRET_ACCESS_KEY="your-secret-key-here"
export AWS_DEFAULT_REGION="us-east-1"
```

Add these to `~/.bashrc` or `~/.zshrc` to make them permanent.

**On Windows (Command Prompt):**
```cmd
set AWS_ACCESS_KEY_ID=your-access-key-here
set AWS_SECRET_ACCESS_KEY=your-secret-key-here
set AWS_DEFAULT_REGION=us-east-1
```

**On Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-here"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key-here"
$env:AWS_DEFAULT_REGION="us-east-1"
```

---

### Step 1.4: Verify Python Installation

```bash
python3 --version
# Should show: Python 3.8 or higher
```

**If not installed:**

**On Mac:**
```bash
brew install python3
```

**On Windows:**
Download from: https://www.python.org/downloads/

**On Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

## Part 2: Download and Setup Project (5 minutes)

### Step 2.1: Extract the Project

1. Download the `flag_monitor_terraform` folder you received
2. Extract it to a location on your computer, for example:
   - Mac/Linux: `~/projects/flag_monitor_terraform`
   - Windows: `C:\Users\YourName\projects\flag_monitor_terraform`

### Step 2.2: Open Terminal in Project Directory

**On Mac/Linux:**
```bash
cd ~/projects/flag_monitor_terraform
```

**On Windows (Command Prompt):**
```cmd
cd C:\Users\YourName\projects\flag_monitor_terraform
```

**On Windows (PowerShell):**
```powershell
cd C:\Users\YourName\projects\flag_monitor_terraform
```

### Step 2.3: Verify Files

```bash
ls -la
# or on Windows:
dir
```

You should see:
```
main.tf
variables.tf
outputs.tf
terraform.tfvars.example
build.sh
build.bat
lambda_function.py
requirements.txt
README.md
QUICKSTART.md
```

---

## Part 3: Configure Terraform (5 minutes)

### Step 3.1: Create Your Configuration File

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# On Windows:
copy terraform.tfvars.example terraform.tfvars
```

### Step 3.2: Edit Configuration

Open `terraform.tfvars` in your favorite text editor:

```bash
# Mac/Linux
nano terraform.tfvars
# or
vim terraform.tfvars
# or use VS Code
code terraform.tfvars

# Windows
notepad terraform.tfvars
# or use VS Code
code terraform.tfvars
```

### Step 3.3: Set Your Email (REQUIRED)

Change this line:
```hcl
notification_email = "your-email@example.com"
```

To your actual email:
```hcl
notification_email = "bickey@gmail.com"  # Use your real email!
```

### Step 3.4: Adjust Timezone (If Needed)

The default is set for **Eastern Time (EST/EDT)**.

**If you're in a different timezone**, update the cron expressions:

**For Pacific Time (PST/PDT):**
```hcl
morning_cron = "cron(0 14 * * ? *)"  # 6 AM PST = 2 PM UTC
evening_cron = "cron(0 2 * * ? *)"   # 6 PM PST = 2 AM UTC
timezone = "America/Los_Angeles"
```

**For Central Time (CST/CDT):**
```hcl
morning_cron = "cron(0 12 * * ? *)"  # 6 AM CST = 12 PM UTC
evening_cron = "cron(0 0 * * ? *)"   # 6 PM CST = 12 AM UTC
timezone = "America/Chicago"
```

**For Mountain Time (MST/MDT):**
```hcl
morning_cron = "cron(0 13 * * ? *)"  # 6 AM MST = 1 PM UTC
evening_cron = "cron(0 1 * * ? *)"   # 6 PM MST = 1 AM UTC
timezone = "America/Denver"
```

### Step 3.5: Optional - Add SMS

If you want SMS notifications too:
```hcl
notification_phone = "+12345678900"  # Include country code!
```

Leave as `""` if you only want email.

### Step 3.6: Save the File

- In nano: Press `Ctrl+X`, then `Y`, then `Enter`
- In vim: Press `Esc`, then type `:wq`, then `Enter`
- In other editors: Just save normally

---

## Part 4: Build Lambda Packages (2 minutes)

This creates the ZIP files that Terraform will upload to AWS.

### Step 4.1: Run Build Script

**On Mac/Linux:**
```bash
chmod +x build.sh  # Make it executable (first time only)
./build.sh
```

**On Windows (Command Prompt):**
```cmd
build.bat
```

**On Windows (PowerShell):**
```powershell
.\build.bat
```

### Step 4.2: Verify Build Output

You should see:
```
==========================================
Building FLAG Monitor Lambda Package
==========================================
Step 1: Creating Lambda function zip...
✓ Lambda function package created: lambda_function.zip
Step 2: Creating Lambda Layer with dependencies...
✓ Lambda layer package created: lambda_layer.zip

==========================================
Build Complete!
==========================================
```

### Step 4.3: Verify Files Created

```bash
ls -lh lambda_function.zip lambda_layer.zip

# You should see:
# lambda_function.zip (~2-4 KB)
# lambda_layer.zip (~500 KB - 1 MB)
```

---

## Part 5: Deploy with Terraform (5 minutes)

### Step 5.1: Initialize Terraform

This downloads the AWS provider plugin:

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...
- Installed hashicorp/aws v5.x.x

Terraform has been successfully initialized!
```

### Step 5.2: Review the Plan (Optional but Recommended)

See what Terraform will create:

```bash
terraform plan
```

You'll see a list of ~15 resources to be created:
- aws_lambda_function.flag_monitor
- aws_dynamodb_table.flag_processing_times
- aws_sns_topic.flag_notifications
- aws_iam_role.lambda_role
- etc.

**Review this to understand what's being created.**

### Step 5.3: Apply (Deploy!)

```bash
terraform apply
```

Terraform will show the plan again and ask:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**Type:** `yes` (and press Enter)

### Step 5.4: Watch Deployment

You'll see:
```
aws_dynamodb_table.flag_processing_times: Creating...
aws_sns_topic.flag_notifications: Creating...
aws_iam_role.lambda_role: Creating...
...
aws_lambda_function.flag_monitor: Creating...
...

Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

notification_instructions = <<EOT

===================================================================
FLAG Monitor Deployed Successfully! 
===================================================================

IMPORTANT: Check your email (bickey@gmail.com) and confirm the SNS subscription!
...
```

🎉 **Deployment complete!** The infrastructure is now running in AWS!

---

## Part 6: Confirm Email Subscription (2 minutes)

### Step 6.1: Check Your Email

Look for an email from **AWS Notifications** with subject:
```
AWS Notification - Subscription Confirmation
```

**Check your spam/junk folder if you don't see it!**

### Step 6.2: Confirm Subscription

Click the **"Confirm subscription"** link in the email.

You'll see a page saying:
```
Subscription confirmed!
```

✅ **Now you'll receive notifications!**

---

## Part 7: Test the System (3 minutes)

### Step 7.1: Manual Test Invocation

```bash
aws lambda invoke \
  --function-name FLAG-Monitor \
  --payload '{}' \
  response.json
```

Expected output:
```
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```

### Step 7.2: Check Response

```bash
cat response.json
```

Should show:
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Date changed\", \"current\": \"August 2024\"}"
}
```

### Step 7.3: Check Your Email

Within 1-2 minutes, you should receive an email:

```
Subject: FLAG Monitor Started

FLAG DOL Processing Times Monitor is now active!

Current Analyst Review Date: August 2024
...
```

✅ **If you got this email, everything works!**

### Step 7.4: View Logs (Optional)

```bash
aws logs tail /aws/lambda/FLAG-Monitor --follow
```

Press `Ctrl+C` to exit.

---

## Part 8: Verify Scheduled Execution

### Step 8.1: Check EventBridge Rules

```bash
aws events list-rules --name-prefix FLAG-Monitor
```

Should show two rules:
- FLAG-Monitor-6AM
- FLAG-Monitor-6PM

### Step 8.2: Wait for Scheduled Run

Your next automatic check will happen at:
- 6 AM (your timezone)
- 6 PM (your timezone)

You'll get an email notification!

---

## Understanding What Was Created

### AWS Resources in Your Account

Login to AWS Console and check:

1. **Lambda** → Functions → `FLAG-Monitor`
   - Your monitoring code running in the cloud

2. **DynamoDB** → Tables → `FLAGProcessingTimes`
   - Stores the last known Analyst Review date

3. **SNS** → Topics → `FLAG-Monitor-Notifications`
   - Your notification hub

4. **EventBridge** → Rules → `FLAG-Monitor-6AM` and `FLAG-Monitor-6PM`
   - Scheduled triggers

5. **IAM** → Roles → `FLAG-Monitor-Lambda-Role`
   - Permissions for Lambda to access SNS and DynamoDB

6. **CloudWatch** → Log groups → `/aws/lambda/FLAG-Monitor`
   - Execution logs

### How Terraform Authenticated

When you ran `terraform apply`, Terraform:

1. **Read your AWS credentials** from one of these locations (in order):
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - AWS credentials file (`~/.aws/credentials`)
   - IAM role (if running on EC2)

2. **Used those credentials** to create resources via AWS API

3. **Stored state** in `terraform.tfstate` file (tracks what was created)

---

## Common Commands Reference

### View What's Deployed
```bash
terraform show
terraform state list
```

### Update Configuration
```bash
# Edit terraform.tfvars
nano terraform.tfvars

# Apply changes
terraform apply
```

### View Logs
```bash
aws logs tail /aws/lambda/FLAG-Monitor --follow
```

### Test Function
```bash
aws lambda invoke --function-name FLAG-Monitor response.json
cat response.json
```

### Destroy Everything
```bash
terraform destroy
# Type 'yes' to confirm
```

---

## Troubleshooting

### Error: "No valid credential sources found"

**Problem:** Terraform can't find AWS credentials

**Solution:**
```bash
# Verify credentials are configured
aws sts get-caller-identity

# If this fails, run:
aws configure
# And enter your access key ID and secret access key
```

---

### Error: "NoSuchBucket" or "AccessDenied"

**Problem:** AWS credentials don't have permissions

**Solution:**
Your IAM user needs these permissions:
- `AWSLambdaFullAccess`
- `IAMFullAccess`
- `AmazonDynamoDBFullAccess`
- `AmazonSNSFullAccess`
- `AmazonEventBridgeFullAccess`
- `CloudWatchLogsFullAccess`

In AWS Console:
1. IAM → Users → Your User
2. Permissions → Add permissions → Attach policies directly
3. Search and attach the above policies

---

### Error: "lambda_function.zip: no such file"

**Problem:** Build script didn't run

**Solution:**
```bash
./build.sh
# or on Windows:
build.bat

# Then try again:
terraform apply
```

---

### Email Not Received

**Problem:** SNS subscription pending

**Solution:**
1. Check spam/junk folder
2. Check AWS Console: SNS → Topics → FLAG-Monitor-Notifications → Subscriptions
3. If status is "Pending confirmation", check email again
4. Resend confirmation:
   ```bash
   # Get subscription ARN
   aws sns list-subscriptions-by-topic \
     --topic-arn $(terraform output -raw sns_topic_arn)
   
   # Then manually subscribe again if needed
   ```

---

## What You Learned

✅ **Terraform** - Infrastructure as Code  
✅ **AWS CLI** - Command-line AWS management  
✅ **IAM** - AWS authentication and permissions  
✅ **Lambda** - Serverless functions  
✅ **DynamoDB** - NoSQL database  
✅ **SNS** - Notification service  
✅ **EventBridge** - Scheduled triggers  
✅ **CloudWatch** - Logging and monitoring  

This is production-grade DevOps work! 🚀

---

## Next Steps

1. ✅ You're done! The system is running.
2. Wait for your first scheduled notification (6 AM or 6 PM)
3. When the Analyst Review date changes, you'll get an alert!

---

**Need Help?**

All of this information is also in:
- `README.md` - Complete documentation
- `QUICKSTART.md` - Quick reference

---

🎉 **Congratulations!** You've deployed a production monitoring system using Infrastructure as Code!
