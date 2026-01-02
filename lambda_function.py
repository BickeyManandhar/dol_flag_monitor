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

# AWS clients
sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Configuration from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'FLAGProcessingTimes')
FLAG_URL = 'https://flag.dol.gov/processingtimes'

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
                'last_updated': datetime.now().isoformat()
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
    
    print(f"Starting FLAG monitor check at {datetime.now().isoformat()}")
    
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
    
    # Check if date has changed
    if previous_date != current_date:
        # Date has changed!
        if previous_date:
            subject = "🎉 FLAG Analyst Review Date UPDATED!"
            message = f"""
FLAG DOL Processing Times Update Alert

✅ The Analyst Review date has MOVED!

Previous Date: {previous_date}
New Date: {current_date}

This means PERM applications are being processed faster!

Check the full details at:
{FLAG_URL}

Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
            """
        else:
            # First time running
            subject = "FLAG Monitor Started"
            message = f"""
FLAG DOL Processing Times Monitor is now active!

Current Analyst Review Date: {current_date}

You will receive notifications:
- Every day at 6 AM and 6 PM (status update)
- Immediately when the date changes

Check the site at: {FLAG_URL}

Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
            """
        
        # Save new date
        save_current_date(current_date)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Date changed',
                'previous': previous_date,
                'current': current_date
            })
        }
    
    else:
        # Date hasn't changed - send regular status update
        subject = "FLAG Monitor Status: No Change"
        message = f"""
FLAG DOL Processing Times - Daily Check

📊 Current Status:
Analyst Review Date: {current_date}
Status: No change since last check

The date is still processing PERM applications filed in {current_date}.

Next check: In 12 hours

Check the site at: {FLAG_URL}

Timestamp: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
        """
        
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No change',
                'current': current_date
            })
        }
