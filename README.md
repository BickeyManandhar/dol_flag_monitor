# FLAG Monitor - Complete Deployment Guide
## Automated FLAG DOL Processing Times Monitor

> Serverless AWS Lambda monitor that scrapes FLAG DOL processing times, stores data in DynamoDB, and sends email alerts via SNS when dates change — fully deployed with Terraform.

---

## 📋 Table of Contents

1. [What This Does](#what-this-does)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Step 1: Install Required Tools](#step-1-install-required-tools)
5. [Step 2: Setup AWS Credentials](#step-2-setup-aws-credentials)
6. [Step 3: Configure Your Settings](#step-3-configure-your-settings)
7. [Step 4: Build Lambda Package](#step-4-build-lambda-package)
8. [Step 5: Deploy with Terraform](#step-5-deploy-with-terraform)
9. [Step 6: Confirm Email Subscription](#step-6-confirm-email-subscription)
10. [Step 7: Test Everything](#step-7-test-everything)
11. [API Gateway - Manual Trigger](#api-gateway---manual-trigger)
12. [What Gets Created](#what-gets-created)
13. [Daily Operations](#daily-operations)
14. [Troubleshooting](#troubleshooting)
15. [Updating & Maintenance](#updating--maintenance)
16. [Cost Breakdown](#cost-breakdown)

---

## What This Does

This system automatically monitors the FLAG DOL Analyst Review processing date and notifies you via email/SMS.

**Features:**
- ✅ Checks FLAG website twice daily (6 AM & 6 PM)
- ✅ Sends notification when date changes
- ✅ Sends daily status updates (so you know it's working)
- ✅ Manual trigger via API Gateway URL (trigger from phone/browser)
- ✅ Completely automated - set it and forget it
- ✅ Costs less than $0.10/month

**What You're Monitoring:**
- Website: https://flag.dol.gov/processingtimes
- Specific field: **Analyst Review** date

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRIGGERS                                 │
├─────────────────────────────────────────────────────────────────┤
│  EventBridge (6AM) ──┐                                          │
│  EventBridge (6PM) ──┼──▶  Lambda Function  ◀── API Gateway     │
│  API Gateway URL  ───┘     (Python code)        (manual trigger)│
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────────┐
              │ DynamoDB │  │   SNS    │  │  CloudWatch  │
              │ (storage)│  │ (email)  │  │   (logs)     │
              └──────────┘  └──────────┘  └──────────────┘
```

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
wget https://releases.hashicorp.com/terraform/1.6.6/terraform_1.6.6_linux_amd64.zip
unzip terraform_1.6.6_linux_amd64.zip
sudo mv terraform /usr/local/bin/
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
aws --version
```

#### On Linux:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

---

### 1.3: Verify Python

Python is needed to build the Lambda function package.

```bash
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

### 2.1: Get AWS Access Keys

1. **Login to AWS Console**: https://console.aws.amazon.com/
2. **Click your username** (top right corner)
3. Click **"Security credentials"**
4. Scroll down to **"Access keys"** section
5. Click **"Create access key"**
6. Choose **"Command Line Interface (CLI)"**
7. Check the confirmation box
8. Click **"Create access key"**
9. **Copy both values:**
   - **Access key ID** (looks like: `AKIAIOSFODNN7EXAMPLE`)
   - **Secret access key** (looks like: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
10. Click **"Download .csv file"** (backup - keep this safe!)

---

### 2.2: Configure AWS CLI

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

---

## Step 3: Configure Your Settings

**Time: 5 minutes**

### 3.1: Create Configuration File

```bash
# Copy the example file
cp terraform.tfvars.example terraform.tfvars

# On Windows:
copy terraform.tfvars.example terraform.tfvars
```

### 3.2: Edit Configuration

Open `terraform.tfvars` in any text editor:

```bash
# Windows
notepad terraform.tfvars

# Mac/Linux
nano terraform.tfvars
```

### 3.3: Set Your Email (REQUIRED!)

Change this line:
```hcl
notification_email = "your-email@example.com"
```

### 3.4: Adjust Timezone (If Not Eastern Time)

Default is **Eastern Time (EST/EDT)**.

| Timezone | 6 AM | 6 PM |
|----------|------|------|
| **EST/EDT** | `cron(0 11 * * ? *)` | `cron(0 23 * * ? *)` |
| **CST/CDT** | `cron(0 12 * * ? *)` | `cron(0 0 * * ? *)` |
| **MST/MDT** | `cron(0 13 * * ? *)` | `cron(0 1 * * ? *)` |
| **PST/PDT** | `cron(0 14 * * ? *)` | `cron(0 2 * * ? *)` |

### 3.5: Save the File

---

## Step 4: Build Lambda Package

**Time: 2 minutes**

This creates the ZIP files that Terraform will upload to AWS.

**On Mac/Linux:**
```bash
chmod +x build.sh
./build.sh
```

**On Windows:**
```cmd
build.bat
```

**Expected output:**
```
==========================================
Building FLAG Monitor Lambda Package
==========================================
[OK] Lambda function package created: lambda_function.zip
[OK] Lambda layer package created: lambda_layer.zip
==========================================
Build Complete!
==========================================
```

**Verify files created:**
```bash
ls -lh *.zip
# lambda_function.zip (~2-4 KB)
# lambda_layer.zip (~500 KB - 1 MB)
```

---

## Step 5: Deploy with Terraform

**Time: 5 minutes**

### 5.1: Initialize Terraform

```bash
terraform init
```

### 5.2: Review the Plan (Optional)

```bash
terraform plan
```

### 5.3: Deploy Everything!

```bash
terraform apply
```

Type `yes` when prompted.

**This takes about 2-3 minutes.**

🎉 **Deployment complete!**

---

## Step 6: Confirm Email Subscription

**Time: 2 minutes**

1. Check your email for **"AWS Notification - Subscription Confirmation"**
2. **Check spam/junk folder** if you don't see it
3. Click the **"Confirm subscription"** link

✅ **You're now subscribed and will receive notifications!**

---

## Step 7: Test Everything

**Time: 3 minutes**

### 7.1: Manually Invoke Lambda

```bash
aws lambda invoke --function-name FLAG-Monitor --payload '{}' response.json
```

### 7.2: Check Response

```bash
cat response.json
# Or on Windows: type response.json
```

### 7.3: Check Your Email

You should receive a notification email within 1-2 minutes.

✅ **If you got the email, everything is working!**

---

## API Gateway - Manual Trigger

API Gateway provides a URL to trigger the Lambda manually from any device — your phone, browser, or anywhere with internet access.

### Getting Your Trigger URL

After deployment, get your URL:

```bash
terraform output trigger_url
```

Output:
```
"https://abc123xyz.execute-api.us-east-1.amazonaws.com/trigger"
```

### How to Use It

**From Browser:**
Just paste the URL in your browser's address bar and hit Enter.

**From Phone:**
1. Open the URL in your phone's browser
2. Bookmark it for quick access
3. Tap the bookmark anytime to trigger a check

**From Command Line:**
```bash
curl https://abc123xyz.execute-api.us-east-1.amazonaws.com/trigger
```

### What Happens When You Trigger

1. Lambda executes immediately
2. Scrapes FLAG website
3. Compares with stored date
4. Sends you an email notification
5. Returns JSON response in browser:
   ```json
   {"statusCode": 200, "body": "{\"message\": \"No change\", \"current\": \"August 2024\"}"}
   ```

### API Gateway Cost

| Usage | Cost |
|-------|------|
| First 1 million requests/month | **FREE** (12 months) |
| After free tier | $1.00 per million requests |

For manual triggers (maybe 100/month), cost is essentially **$0.00**.

### Security Note

The URL is public but obscure (random characters). Anyone with the URL can trigger your Lambda, but:
- It only reads a public website
- Worst case: someone triggers extra checks (minimal cost)
- If concerned, you can add authentication later

---

## What Gets Created

### AWS Resources

| Resource | Name | Purpose |
|----------|------|---------|
| Lambda Function | `FLAG-Monitor` | Runs your Python code |
| Lambda Layer | `FLAG-Monitor-Dependencies` | Python packages (requests, bs4) |
| DynamoDB Table | `FLAGProcessingTimes` | Stores last known date |
| SNS Topic | `FLAG-Monitor-Notifications` | Sends emails |
| EventBridge Rules | `FLAG-Monitor-6AM`, `FLAG-Monitor-6PM` | Scheduled triggers |
| API Gateway | `FLAG-Monitor-API` | Manual trigger URL |
| IAM Role | `FLAG-Monitor-Lambda-Role` | Permissions |
| CloudWatch Logs | `/aws/lambda/FLAG-Monitor` | Execution logs |

### Local Files Created

```
flag_monitor_complete/
├── terraform.tfvars          # Your config (DO NOT COMMIT)
├── terraform.tfstate         # State file (DO NOT COMMIT)
├── terraform.tfstate.backup  
├── .terraform/               
├── lambda_function.zip       
├── lambda_layer.zip          
└── response.json            
```

---

## Daily Operations

### Automatic Checks

Every day at 6 AM and 6 PM:
1. EventBridge triggers Lambda
2. Lambda scrapes FLAG website
3. Compares with DynamoDB
4. Sends notification via SNS

### Notification Types

**Date Changed:**
```
Subject: 🎉 FLAG Analyst Review Date UPDATED!

Previous Date: August 2024
New Date: September 2024
```

**No Change (daily status):**
```
Subject: FLAG Monitor Status: No Change

Current Analyst Review Date: August 2024
Status: No change since last check
```

### Useful Commands

```bash
# View logs
aws logs tail /aws/lambda/FLAG-Monitor --follow

# Check stored date
aws dynamodb scan --table-name FLAGProcessingTimes

# Manual trigger via CLI
aws lambda invoke --function-name FLAG-Monitor response.json

# Get API Gateway URL
terraform output trigger_url
```

---

## Troubleshooting

### No Email Received

1. Check spam/junk folder
2. Verify subscription: AWS Console → SNS → Topics → Subscriptions
3. Status should be "Confirmed"

### Lambda Timeout

```bash
# Check logs
aws logs tail /aws/lambda/FLAG-Monitor --since 1h
```

### Build Script Fails

```bash
# Update pip
python3 -m pip install --upgrade pip

# On Windows, if --user conflict:
pip install requests beautifulsoup4 --target build\layer\python --no-user
```

### API Gateway Not Working

```bash
# Verify it exists
terraform output trigger_url

# If empty, redeploy
terraform apply
```

---

## Updating & Maintenance

### Change Notification Time

1. Edit `terraform.tfvars`
2. Update `morning_cron` / `evening_cron`
3. Run `terraform apply`

### Change Email

1. Edit `terraform.tfvars`
2. Run `terraform apply`
3. Confirm new email subscription

### Update Lambda Code

1. Edit `lambda_function.py`
2. Run `./build.sh` (or `build.bat`)
3. Run `terraform apply`

### Pause Monitoring

```bash
aws events disable-rule --name FLAG-Monitor-6AM
aws events disable-rule --name FLAG-Monitor-6PM
```

### Resume Monitoring

```bash
aws events enable-rule --name FLAG-Monitor-6AM
aws events enable-rule --name FLAG-Monitor-6PM
```

### Destroy Everything

```bash
terraform destroy
# Type 'yes' to confirm
```

⚠️ **This is permanent!**

---

## Cost Breakdown

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Lambda | ~60 executions | $0.00 (free tier) |
| DynamoDB | <1KB storage | $0.00 (free tier) |
| SNS | ~60 emails | ~$0.03 |
| API Gateway | <100 requests | $0.00 (free tier) |
| CloudWatch | 7-day logs | $0.00 (free tier) |
| EventBridge | 60 events | $0.00 (free tier) |
| **Total** | | **~$0.03/month** |

---

## Technologies Used

- **Python** - Lambda function code
- **AWS Lambda** - Serverless compute
- **AWS DynamoDB** - NoSQL database
- **AWS SNS** - Email notifications
- **AWS EventBridge** - Scheduled triggers
- **AWS API Gateway** - HTTP endpoint for manual triggers
- **AWS CloudWatch** - Logging
- **AWS IAM** - Security & permissions
- **Terraform** - Infrastructure as Code
- **BeautifulSoup** - Web scraping

---

## License

MIT License - feel free to use and modify.

---

🎉 **Your FLAG monitor is now running 24/7 in the cloud!**
