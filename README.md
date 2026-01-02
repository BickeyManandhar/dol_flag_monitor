# FLAG Monitor - Complete Deployment Guide
## Automated FLAG DOL Processing Times Monitor

---

## 📋 Table of Contents

1. [What This Does](#what-this-does)
2. [Prerequisites](#prerequisites)
3. [Step 1: Install Required Tools](#step-1-install-required-tools)
4. [Step 2: Setup AWS Credentials](#step-2-setup-aws-credentials)
5. [Step 3: Configure Your Settings](#step-3-configure-your-settings)
6. [Step 4: Build Lambda Package](#step-4-build-lambda-package)
7. [Step 5: Deploy with Terraform](#step-5-deploy-with-terraform)
8. [Step 6: Confirm Email Subscription](#step-6-confirm-email-subscription)
9. [Step 7: Test Everything](#step-7-test-everything)
10. [What Gets Created](#what-gets-created)
11. [Daily Operations](#daily-operations)
12. [Troubleshooting](#troubleshooting)
13. [Updating & Maintenance](#updating--maintenance)

---

## What This Does

This system automatically monitors the FLAG DOL Analyst Review processing date and notifies you via email/SMS.

**Features:**
- ✅ Checks FLAG website twice daily (6 AM & 6 PM)
- ✅ Sends notification when date changes from "August 2024"
- ✅ Sends daily status updates (so you know it's working)
- ✅ Completely automated - set it and forget it
- ✅ Costs less than $0.10/month

**What You're Monitoring:**
- Website: https://flag.dol.gov/processingtimes
- Specific field: **Analyst Review** date
- Current value: **August 2024** (as of your screenshot)

---

## Prerequisites

**You need:**
1. ☐ A computer (Windows, Mac, or Linux)
2. ☐ Internet connection
3. ☐ AWS Account (free tier is fine)
4. ☐ Email address
5. ☐ About 30-45 minutes

**Skills needed:**
- Basic command line usage (we'll guide you!)
- No prior AWS or Terraform experience required

---

## Step 1: Install Required Tools

**Time: 10-15 minutes**

### 1.1: Install Terraform

Terraform is the tool that will create all AWS resources for you.

#### On Windows:

1. Download from: https://www.terraform.io/downloads
2. Extract the ZIP file
3. You'll get a file called `terraform.exe`
4. Move it to: `C:\Windows\System32\`
5. Verify installation:
   ```cmd
   terraform version
   ```
   Should show: `Terraform v1.x.x`

#### On Mac:

```bash
# Using Homebrew (install Homebrew first from brew.sh if needed)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify
terraform version
```

#### On Linux:

```bash
# Download Terraform
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip

# Extract
unzip terraform_1.6.6_linux_amd64.zip

# Move to system path
sudo mv terraform /usr/local/bin/

# Verify
terraform version
```

---

### 1.2: Install AWS CLI

The AWS CLI lets Terraform communicate with your AWS account.

#### On Windows:

1. Download: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Run the installer
3. Accept all defaults
4. Verify:
   ```cmd
   aws --version
   ```

#### On Mac:

```bash
brew install awscli

# Verify
aws --version
```

#### On Linux:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify
aws --version
```

---

### 1.3: Verify Python

Python is needed to build the Lambda function package.

```bash
# Check version
python3 --version

# Should show Python 3.8 or higher
```

**If not installed:**

- **Windows**: Download from https://www.python.org/downloads/
- **Mac**: `brew install python3`
- **Linux**: `sudo apt install python3 python3-pip`

---

## Step 2: Setup AWS Credentials

**Time: 10 minutes**

This is how Terraform will authenticate to your AWS account.

### 2.1: Get AWS Access Keys

1. **Login to AWS Console**: https://console.aws.amazon.com/

2. **Click your username** (top right corner)

3. Click **"Security credentials"**

4. Scroll down to **"Access keys"** section

5. Click **"Create access key"**

6. Choose **"Command Line Interface (CLI)"**

7. Check the confirmation box: "I understand..."

8. Click **"Create access key"**

9. **IMPORTANT**: You'll see two values:
   - **Access key ID** (looks like: `AKIAIOSFODNN7EXAMPLE`)
   - **Secret access key** (looks like: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

10. **Copy both values** - you'll need them in the next step

11. Click **"Download .csv file"** (backup - keep this safe!)

---

### 2.2: Configure AWS CLI

Open your terminal/command prompt and run:

```bash
aws configure
```

You'll be prompted for:

```
AWS Access Key ID [None]: <paste your Access Key ID>
AWS Secret Access Key [None]: <paste your Secret Access Key>
Default region name [None]: us-east-1
Default output format [None]: json
```

**Press Enter after each line.**

---

### 2.3: Verify Credentials

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

✅ **If you see this, you're ready to proceed!**

❌ **If you get an error**, double-check your access keys and try `aws configure` again.

---

## Step 3: Configure Your Settings

**Time: 5 minutes**

### 3.1: Extract the Project Files

1. Extract the ZIP file you downloaded
2. You should have a folder with these files:
   ```
   flag_monitor_complete/
   ├── main.tf
   ├── variables.tf
   ├── outputs.tf
   ├── terraform.tfvars.example
   ├── lambda_function.py
   ├── requirements.txt
   ├── build.sh (Linux/Mac)
   ├── build.bat (Windows)
   ├── .gitignore
   └── README.md (this file)
   ```

---

### 3.2: Open Terminal in Project Folder

**On Windows:**
1. Open the folder in File Explorer
2. Type `cmd` in the address bar
3. Press Enter

**On Mac:**
1. Open Terminal
2. Type: `cd ` (with a space after cd)
3. Drag the folder into Terminal
4. Press Enter

**On Linux:**
1. Open Terminal
2. Navigate: `cd /path/to/flag_monitor_complete`

---

### 3.3: Create Configuration File

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# On Windows:
copy terraform.tfvars.example terraform.tfvars
```

---

### 3.4: Edit Configuration

Open `terraform.tfvars` in any text editor:

**Windows:** `notepad terraform.tfvars`
**Mac/Linux:** `nano terraform.tfvars` or `vim terraform.tfvars`

---

### 3.5: Set Your Email (REQUIRED!)

Find this line:
```hcl
notification_email = "your-email@example.com"
```

Change it to your actual email:
```hcl
notification_email = "bickey@gmail.com"
```

---

### 3.6: Adjust Timezone (If Not Eastern Time)

Default is **Eastern Time (EST/EDT)** with checks at 6 AM and 6 PM.

**If you're in a different timezone**, update these lines:

**For Pacific Time (PST/PDT):**
```hcl
morning_cron = "cron(0 14 * * ? *)"  # 6 AM PST
evening_cron = "cron(0 2 * * ? *)"   # 6 PM PST
timezone = "America/Los_Angeles"
```

**For Central Time (CST/CDT):**
```hcl
morning_cron = "cron(0 12 * * ? *)"  # 6 AM CST
evening_cron = "cron(0 0 * * ? *)"   # 6 PM CST
timezone = "America/Chicago"
```

**For Mountain Time (MST/MDT):**
```hcl
morning_cron = "cron(0 13 * * ? *)"  # 6 AM MST
evening_cron = "cron(0 1 * * ? *)"   # 6 PM MST
timezone = "America/Denver"
```

---

### 3.7: Optional - Add SMS Notifications

If you want text messages too:

```hcl
notification_phone = "+12345678900"  # Include country code!
```

Leave as `""` if you only want email.

---

### 3.8: Save the File

- **nano**: Press `Ctrl+X`, then `Y`, then `Enter`
- **vim**: Press `Esc`, type `:wq`, press `Enter`
- **Notepad**: Click File → Save

---

## Step 4: Build Lambda Package

**Time: 2 minutes**

This creates the ZIP files that Terraform will upload to AWS.

### 4.1: Run Build Script

**On Mac/Linux:**
```bash
chmod +x build.sh
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

---

### 4.2: Expected Output

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

---

### 4.3: Verify Files Created

```bash
ls -lh lambda_function.zip lambda_layer.zip

# Or on Windows:
dir lambda_function.zip lambda_layer.zip
```

You should see:
- `lambda_function.zip` (~2-4 KB)
- `lambda_layer.zip` (~500 KB - 1 MB)

✅ **If you see both files, proceed to next step!**

---

## Step 5: Deploy with Terraform

**Time: 5 minutes**

Now we'll create all AWS resources with a few commands!

### 5.1: Initialize Terraform

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.x.x...
- Installed hashicorp/aws v5.x.x

Terraform has been successfully initialized!
```

This downloads the AWS provider plugin.

---

### 5.2: Review the Plan (Optional but Recommended)

See what Terraform will create:

```bash
terraform plan
```

You'll see a list of about 15 resources:
- `aws_lambda_function.flag_monitor`
- `aws_dynamodb_table.flag_processing_times`
- `aws_sns_topic.flag_notifications`
- `aws_iam_role.lambda_role`
- `aws_cloudwatch_event_rule.morning_check`
- `aws_cloudwatch_event_rule.evening_check`
- And more...

**This is what will be created in your AWS account.**

---

### 5.3: Deploy Everything!

```bash
terraform apply
```

Terraform will show you the plan again and ask:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**Type:** `yes` (and press Enter)

---

### 5.4: Watch the Magic Happen

You'll see output like:
```
aws_dynamodb_table.flag_processing_times: Creating...
aws_sns_topic.flag_notifications: Creating...
aws_iam_role.lambda_role: Creating...
aws_dynamodb_table.flag_processing_times: Creation complete
aws_sns_topic.flag_notifications: Creation complete
aws_sns_topic_subscription.email_subscription: Creating...
...
aws_lambda_function.flag_monitor: Creating...
aws_lambda_function.flag_monitor: Still creating... [10s elapsed]
aws_lambda_function.flag_monitor: Creation complete
...

Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

notification_instructions = <<EOT

===================================================================
FLAG Monitor Deployed Successfully! 
===================================================================

IMPORTANT: Check your email (bickey@gmail.com) and confirm the SNS subscription!

Resources Created:
- Lambda Function: FLAG-Monitor
- DynamoDB Table: FLAGProcessingTimes
- SNS Topic: FLAG-Monitor-Notifications
...
```

**This takes about 2-3 minutes.**

🎉 **Deployment complete! Your infrastructure is now running in AWS!**

---

## Step 6: Confirm Email Subscription

**Time: 2 minutes**

### 6.1: Check Your Email

Look for an email from **AWS Notifications** with subject:
```
AWS Notification - Subscription Confirmation
```

**Check your spam/junk folder if you don't see it!**

---

### 6.2: Click Confirmation Link

Click the **"Confirm subscription"** link in the email.

Your browser will open and show:
```
Subscription confirmed!
```

✅ **You're now subscribed and will receive notifications!**

---

## Step 7: Test Everything

**Time: 3 minutes**

Let's make sure it works!

### 7.1: Manually Invoke Lambda

```bash
aws lambda invoke \
  --function-name FLAG-Monitor \
  --payload '{}' \
  response.json
```

**Expected output:**
```json
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```

---

### 7.2: Check Response

```bash
cat response.json

# Or on Windows:
type response.json
```

Should show:
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Date changed\", \"current\": \"August 2024\"}"
}
```

---

### 7.3: Check Your Email

Within 1-2 minutes, you should receive an email like:

```
Subject: FLAG Monitor Started

FLAG DOL Processing Times Monitor is now active!

Current Analyst Review Date: August 2024

You will receive notifications:
- Every day at 6 AM and 6 PM (status update)
- Immediately when the date changes

Check the site at: https://flag.dol.gov/processingtimes

Timestamp: 2025-01-02 04:32 PM
```

✅ **If you got this email, everything is working perfectly!**

---

### 7.4: View Logs (Optional)

```bash
aws logs tail /aws/lambda/FLAG-Monitor --follow
```

You'll see the Lambda execution logs in real-time.

Press `Ctrl+C` to exit.

---

## What Gets Created

### In Your AWS Account:

1. **Lambda Function** (`FLAG-Monitor`)
   - Runs your Python monitoring code
   - Triggered by EventBridge schedules
   - Has permissions to access SNS and DynamoDB

2. **DynamoDB Table** (`FLAGProcessingTimes`)
   - Stores the last known Analyst Review date
   - Used to detect when date changes

3. **SNS Topic** (`FLAG-Monitor-Notifications`)
   - Sends emails/SMS
   - You're subscribed to this topic

4. **SNS Subscriptions**
   - Email subscription (confirmed by you)
   - SMS subscription (if you added phone number)

5. **IAM Role** (`FLAG-Monitor-Lambda-Role`)
   - Allows Lambda to access other AWS services
   - Follows least-privilege security model

6. **EventBridge Rules** (2 schedules)
   - `FLAG-Monitor-6AM` - Triggers at 6 AM
   - `FLAG-Monitor-6PM` - Triggers at 6 PM

7. **CloudWatch Log Group** (`/aws/lambda/FLAG-Monitor`)
   - Stores execution logs
   - 7-day retention

---

### Files Created Locally:

```
flag_monitor_complete/
├── terraform.tfvars          # Your configuration (DO NOT COMMIT!)
├── terraform.tfstate         # Current state (DO NOT COMMIT!)
├── terraform.tfstate.backup  # Previous state (DO NOT COMMIT!)
├── .terraform/               # Terraform plugins
├── lambda_function.zip       # Lambda code package
├── lambda_layer.zip          # Python dependencies
└── response.json            # Test response
```

---

## Daily Operations

### What Happens Automatically

**Every day at 6 AM and 6 PM (your timezone):**

1. EventBridge triggers Lambda function
2. Lambda fetches FLAG website
3. Extracts Analyst Review date
4. Compares with stored value in DynamoDB
5. Sends you a notification via SNS

**Two types of notifications:**

**Type 1: Date Changed (What you're waiting for!)**
```
Subject: 🎉 FLAG Analyst Review Date UPDATED!

The Analyst Review date has MOVED!

Previous Date: August 2024
New Date: September 2024

This means PERM applications are being processed faster!
```

**Type 2: No Change (Daily status)**
```
Subject: FLAG Monitor Status: No Change

Current Analyst Review Date: August 2024
Status: No change since last check

Next check: In 12 hours
```

---

### Checking Status

**View recent Lambda executions:**
```bash
aws lambda list-functions --query 'Functions[?FunctionName==`FLAG-Monitor`]'
```

**View logs:**
```bash
aws logs tail /aws/lambda/FLAG-Monitor --follow
```

**Check DynamoDB for stored date:**
```bash
aws dynamodb get-item \
  --table-name FLAGProcessingTimes \
  --key '{"id": {"S": "analyst_review_date"}}'
```

---

## Troubleshooting

### Issue: No Email Received After Deployment

**Possible causes:**

1. **SNS subscription not confirmed**
   - Check spam/junk folder
   - Go to AWS Console → SNS → Topics → FLAG-Monitor-Notifications → Subscriptions
   - Status should be "Confirmed", not "Pending"

2. **Wrong email in terraform.tfvars**
   - Check `terraform.tfvars` file
   - Run `terraform apply` again to update

**Solution:**
```bash
# Check subscription status
aws sns list-subscriptions-by-topic \
  --topic-arn $(terraform output -raw sns_topic_arn)
```

---

### Issue: Lambda Timeout or Errors

**Check logs:**
```bash
aws logs tail /aws/lambda/FLAG-Monitor --since 1h
```

**Common errors:**

1. **Network timeout** - Website might be slow
   - Solution: Increase timeout in `main.tf` (already set to 30s)

2. **Permission denied** - IAM role issue
   - Solution: Run `terraform apply` again

---

### Issue: Wrong Timezone

**Problem:** Notifications at wrong time

**Solution:**

1. Edit `terraform.tfvars`
2. Update `morning_cron` and `evening_cron` values
3. Run:
   ```bash
   terraform apply
   ```

---

### Issue: Build Script Fails

**Error:** `pip install` fails

**Solution:**
```bash
# Update pip
python3 -m pip install --upgrade pip

# Try build again
./build.sh  # or build.bat on Windows
```

---

### Issue: Terraform Apply Fails

**Error:** "Error creating Lambda function"

**Checklist:**
- ✅ `lambda_function.zip` exists (run `build.sh`)
- ✅ `lambda_layer.zip` exists (run `build.sh`)
- ✅ AWS credentials configured (`aws sts get-caller-identity`)
- ✅ Sufficient IAM permissions

---

## Updating & Maintenance

### Updating Configuration

**Change notification time:**

1. Edit `terraform.tfvars`
2. Update `morning_cron` or `evening_cron`
3. Run:
   ```bash
   terraform apply
   ```

**Add/change email:**

1. Edit `terraform.tfvars`
2. Update `notification_email`
3. Run:
   ```bash
   terraform apply
   ```
4. Confirm new email subscription

---

### Updating Lambda Code

If you want to modify the monitoring logic:

1. Edit `lambda_function.py`
2. Rebuild package:
   ```bash
   ./build.sh  # or build.bat
   ```
3. Deploy:
   ```bash
   terraform apply
   ```

---

### Viewing Costs

**AWS Cost Explorer:**
1. Go to AWS Console
2. Search for "Cost Explorer"
3. View charges by service

**Expected monthly cost:** ~$0.03 (mostly in free tier)

---

### Pausing the Monitor

**Disable schedules:**
```bash
# Disable morning check
aws events disable-rule --name FLAG-Monitor-6AM

# Disable evening check
aws events disable-rule --name FLAG-Monitor-6PM
```

**Re-enable:**
```bash
aws events enable-rule --name FLAG-Monitor-6AM
aws events enable-rule --name FLAG-Monitor-6PM
```

---

### Destroying Everything

**To completely remove all AWS resources:**

```bash
terraform destroy
```

Type `yes` when prompted.

This will delete:
- Lambda function
- DynamoDB table (and all data)
- SNS topic and subscriptions
- EventBridge rules
- IAM roles
- CloudWatch logs

**⚠️ WARNING: This is permanent! You'll need to redeploy from scratch.**

---

## AWS Console Verification

Want to see your resources in AWS Console?

1. **Login**: https://console.aws.amazon.com/
2. **Region**: Make sure you're in **us-east-1** (top right)

**Check resources:**

- **Lambda**: https://console.aws.amazon.com/lambda/ → Functions → `FLAG-Monitor`
- **DynamoDB**: https://console.aws.amazon.com/dynamodb/ → Tables → `FLAGProcessingTimes`
- **SNS**: https://console.aws.amazon.com/sns/ → Topics → `FLAG-Monitor-Notifications`
- **EventBridge**: https://console.aws.amazon.com/events/ → Rules → `FLAG-Monitor-6AM`, `FLAG-Monitor-6PM`
- **CloudWatch**: https://console.aws.amazon.com/cloudwatch/ → Logs → `/aws/lambda/FLAG-Monitor`

---

## Summary

🎉 **You've successfully deployed an automated monitoring system!**

**What you built:**
- ✅ Automated web scraper (Python)
- ✅ Serverless computing (AWS Lambda)
- ✅ NoSQL database (DynamoDB)
- ✅ Notification system (SNS)
- ✅ Scheduled triggers (EventBridge)
- ✅ Infrastructure as Code (Terraform)

**What happens next:**
- ✅ System checks FLAG website at 6 AM and 6 PM daily
- ✅ You get email notifications when date changes
- ✅ You get daily status updates
- ✅ Everything runs automatically - no action needed from you!

**When you'll get alerted:**
As soon as the Analyst Review date moves from **"August 2024"** to a newer date!

---

## Need Help?

**Check these resources:**
- `QUICKSTART.md` - Quick reference guide
- `DETAILED_SETUP.md` - Even more detailed setup

**Common commands:**
```bash
# View Terraform state
terraform show

# View outputs
terraform output

# View logs
aws logs tail /aws/lambda/FLAG-Monitor --follow

# Test function
aws lambda invoke --function-name FLAG-Monitor response.json
```

---

## Cost Breakdown

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda | 60 executions | $0.00 (free tier) |
| Lambda Layer | Storage | $0.00 (free tier) |
| DynamoDB | On-demand, <1KB | $0.00 (free tier) |
| SNS | ~60 emails | $0.03 |
| SNS | ~60 SMS (optional) | $3.00 |
| CloudWatch | 7-day logs | $0.00 (free tier) |
| EventBridge | 60 events | $0.00 (free tier) |
| **Total (email only)** | | **$0.03/month** |
| **Total (with SMS)** | | **$3.03/month** |

---

## What You Learned

This project teaches real-world skills:

**Technologies:**
- Python programming
- AWS Lambda (serverless)
- DynamoDB (NoSQL database)
- SNS (notifications)
- EventBridge (scheduling)
- Terraform (Infrastructure as Code)
- AWS CLI
- IAM (security & permissions)

**Concepts:**
- Infrastructure as Code
- Serverless architecture
- Event-driven systems
- Web scraping
- Automated monitoring
- Cloud deployment

**This is production-grade infrastructure!** 🚀

---

**Congratulations! You're all set!** 🎉

Your FLAG monitor is now running 24/7 in the cloud!
