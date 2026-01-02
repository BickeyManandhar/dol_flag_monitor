# FLAG Monitor - QUICK START (Terraform)

## 1. Prerequisites (1 minute)

```bash
# Check you have these installed:
terraform version    # Need v1.0+
aws --version        # Need AWS CLI
python3 --version    # Need Python 3
aws sts get-caller-identity  # Verify AWS credentials work
```

## 2. Configure (2 minutes)

```bash
# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit with your email (REQUIRED!)
nano terraform.tfvars   # or use any text editor
```

**Minimum required change:**
```hcl
notification_email = "your-email@example.com"
```

**Optional - adjust timezone:**
See comments in `terraform.tfvars` for your timezone's cron expressions.

## 3. Build Lambda Package (1 minute)

**Linux/Mac:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

Creates: `lambda_function.zip` and `lambda_layer.zip`

## 4. Deploy to AWS (2 minutes)

```bash
# Initialize Terraform
terraform init

# Review what will be created (optional but recommended)
terraform plan

# Deploy!
terraform apply
# Type 'yes' when prompted
```

## 5. Confirm Email (1 minute)

1. **Check your email** (including spam folder)
2. Look for: "AWS Notification - Subscription Confirmation"
3. **Click** the confirmation link

## 6. Test It! (1 minute)

```bash
# Manually trigger the function
aws lambda invoke \
  --function-name FLAG-Monitor \
  --payload '{}' \
  response.json

# Check the result
cat response.json

# View logs
aws logs tail /aws/lambda/FLAG-Monitor --follow
```

**You should receive an email notification!**

## That's It! 🎉

You'll now get notifications:
- Every day at 6 AM and 6 PM
- Immediately when the Analyst Review date changes from "August 2024"

---

## Common Commands

### Update Settings
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

### Check What's Deployed
```bash
terraform show
```

### Destroy Everything
```bash
terraform destroy
# Type 'yes' to confirm
```

---

## Timezone Cheat Sheet

Edit `morning_cron` and `evening_cron` in `terraform.tfvars`:

| Timezone | 6 AM | 6 PM |
|----------|------|------|
| **EST/EDT** | `cron(0 11 * * ? *)` | `cron(0 23 * * ? *)` |
| **CST/CDT** | `cron(0 12 * * ? *)` | `cron(0 0 * * ? *)` |
| **MST/MDT** | `cron(0 13 * * ? *)` | `cron(0 1 * * ? *)` |
| **PST/PDT** | `cron(0 14 * * ? *)` | `cron(0 2 * * ? *)` |

---

## Cost

- **~$0.03/month** (email only)
- **~$3/month** (with SMS)

Almost entirely covered by AWS free tier!

---

## Need Help?

See `README.md` for detailed documentation and troubleshooting.
