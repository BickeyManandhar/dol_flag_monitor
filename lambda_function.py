"""
FLAG DOL Processing Times Monitor
Checks Analyst Review date and sends notifications via email/SMS
Runs twice daily at 6 AM and 6 PM
"""

import json
import boto3
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import os
from zoneinfo import ZoneInfo
from datetime import timezone

# AWS clients
sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Configuration from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'FLAGProcessingTimes')
FLAG_URL = 'https://flag.dol.gov/processingtimes'

# Example: Your LC Priority Date 
MY_LC_DATE = "October 2024"

ET = ZoneInfo("America/New_York")

def now_et():
    """Return current Eastern Time (EST/EDT)"""
    return datetime.now(timezone.utc).astimezone(ET)


def parse_date_to_comparable(date_str):
    """
    Convert date string like 'October 2024' to comparable format (2024, 10)
    Returns tuple (year, month) for comparison
    """
    try:
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        parts = date_str.strip().lower().split()
        month = months.get(parts[0], 0)
        year = int(parts[1])
        return (year, month)
    except:
        return (0, 0)

def is_date_current_or_past(current_analyst_date, my_date):
    """
    Check if the analyst review date has reached or passed my LC date
    Returns True if my_date is now current (analyst date >= my_date)
    """
    analyst = parse_date_to_comparable(current_analyst_date)
    mine = parse_date_to_comparable(my_date)
    return analyst >= mine

def get_current_analyst_date():
    """
    Scrape the FLAG website to get the current Analyst Review date
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(FLAG_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the PERM Processing Times table
        # Look for "Analyst Review" row
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                first_cell = cells[0].get_text(strip=True)
                if 'Analyst Review' in first_cell:
                    analyst_date = cells[1].get_text(strip=True)
                    return analyst_date
        
        return None
        
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return None

def get_previous_date():
    """
    Get the previously stored Analyst Review date from DynamoDB
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(Key={'id': 'analyst_review_date'})
        
        if 'Item' in response:
            return response['Item']['date']
        return None
        
    except Exception as e:
        print(f"Error reading from DynamoDB: {str(e)}")
        return None

def save_current_date(date_value):
    """
    Save the current Analyst Review date to DynamoDB
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(
            Item={
                'id': 'analyst_review_date',
                'date': date_value,
                'last_updated': now_et().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error saving to DynamoDB: {str(e)}")
        return False

def send_notification(subject, message):
    """
    Send notification via SNS (email/SMS)
    """
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"Notification sent: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    Main Lambda handler function
    Runs twice daily to check FLAG processing times
    """
    
    print(f"Starting FLAG monitor check at {now_et().isoformat()}")
    
    # Get current date from website
    current_date = get_current_analyst_date()
    
    if not current_date:
        error_msg = "❌ ERROR: Unable to retrieve Analyst Review date from FLAG website"
        print(error_msg)
        send_notification("FLAG Monitor Error", error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to scrape website'})
        }
    
    print(f"Current Analyst Review date: {current_date}")
    
    # Get previous date from DynamoDB
    previous_date = get_previous_date()
    
    # Check if MY LC date is now current!
    my_date_is_current = is_date_current_or_past(current_date, MY_LC_DATE)
    
    # Check if date has changed
    if previous_date != current_date:
        # Date has changed!
        if previous_date:
            # Check if this change made MY date current
            if my_date_is_current:
                subject = "🎉🎊 HOORAY! Your LC Date is NOW CURRENT! 🎊🎉"
                message = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎉🎉🎉 CONGRATULATIONS! 🎉🎉🎉                            ║
║                                                              ║
║   YOUR LC DATE IS NOW CURRENT!                               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

FLAG DOL Processing Times Update

✅ The Analyst Review date has reached YOUR priority date!

Your LC Date: {MY_LC_DATE}
Current Analyst Review Date: {current_date}
Previous Date: {previous_date}

🚀 This means your PERM application should now be in the 
   queue for processing!

NEXT STEPS:
1. Keep an eye on your email for any RFE (Request for Evidence)
2. Check your PERM case status regularly
3. Coordinate with your attorney/HR

Check the full details at:
{FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}

🎊 Best of luck with your green card journey! 🎊
                """
            else:
                subject = "🎉 FLAG Analyst Review Date UPDATED!"
                message = f"""
FLAG DOL Processing Times Update Alert

✅ The Analyst Review date has MOVED!

Previous Date: {previous_date}
New Date: {current_date}
Your LC Date: {MY_LC_DATE}

📊 Progress: The date is getting closer to your LC date!

This means PERM applications are being processed faster!

Check the full details at:
{FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
                """
        else:
            # First time running
            if my_date_is_current:
                subject = "🎉 FLAG Monitor Started - Your LC Date is ALREADY Current!"
                message = f"""
FLAG DOL Processing Times Monitor is now active!

🎊 GREAT NEWS: Your LC date is ALREADY current!

Your LC Date: {MY_LC_DATE}
Current Analyst Review Date: {current_date}

Your PERM application should already be in the processing queue!

You will receive notifications:
- Every day at 6 AM and 6 PM (status update)
- Immediately when the date changes

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
                """
            else:
                subject = "FLAG Monitor Started"
                message = f"""
FLAG DOL Processing Times Monitor is now active!

Current Analyst Review Date: {current_date}
Your LC Date: {MY_LC_DATE}

You will receive notifications:
- Every day at 6 AM and 6 PM (status update)
- Immediately when the date changes
- Special alert when your LC date becomes current!

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
                """
        
        # Save new date
        save_current_date(current_date)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Date changed',
                'previous': previous_date,
                'current': current_date,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }
    
    else:
        # Date hasn't changed - send regular status update
        if my_date_is_current:
            subject = "FLAG Monitor: Your LC Date is Current ✅"
            message = f"""
FLAG DOL Processing Times - Daily Check

🎉 REMINDER: Your LC date is CURRENT!

Your LC Date: {MY_LC_DATE}
Analyst Review Date: {current_date}
Status: No change since last check

Your application should be in the processing queue.
Keep checking for any updates from DOL!

Next check: In 12 hours

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        else:
            subject = "FLAG Monitor Status: No Change"
            message = f"""
FLAG DOL Processing Times - Daily Check

📊 Current Status:
Analyst Review Date: {current_date}
Your LC Date: {MY_LC_DATE}
Status: No change since last check

The date is still processing PERM applications filed in {current_date}.
Waiting for it to reach {MY_LC_DATE}...

Next check: In 12 hours

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No change',
                'current': current_date,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }