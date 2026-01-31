"""
FLAG DOL Processing Times Monitor - Enhanced with Dual Date Tracking
Tracks TWO dates:
1. "as of" date - When DOL last updated the data
2. Analyst Review date - The actual processing date

Checks and sends notifications via email/SMS
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
import re

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

def calculate_months_difference(current_analyst_date, my_date):
    """
    Calculate how many months until my_date becomes current
    Returns:
    - 0 if already current or past
    - Positive number if waiting (e.g., 2 means "2 months away")
    - Negative number if analyst date is ahead of my date
    """
    analyst = parse_date_to_comparable(current_analyst_date)
    mine = parse_date_to_comparable(my_date)
    
    if analyst >= mine:
        return 0  # Already current!
    
    # Calculate difference
    year_diff = mine[0] - analyst[0]
    month_diff = mine[1] - analyst[1]
    
    total_months = (year_diff * 12) + month_diff
    return total_months

def get_progress_visual(months_away):
    """
    Create a visual progress indicator
    Returns a formatted string with progress bar and status
    """
    if months_away == 0:
        return """
╔══════════════════════════════════════════════════╗
║  ✅✅✅  YOUR DATE IS CURRENT!  ✅✅✅          ║
╚══════════════════════════════════════════════════╝
"""
    elif months_away == 1:
        return """
╔══════════════════════════════════════════════════╗
║  🔥🔥  ONLY 1 MONTH AWAY!  🔥🔥                 ║
╚══════════════════════════════════════════════════╝
Progress: [████████████████████░░] 95%
"""
    elif months_away == 2:
        return """
╔══════════════════════════════════════════════════╗
║  ⏰  2 MONTHS AWAY - Getting Close!  ⏰         ║
╚══════════════════════════════════════════════════╝
Progress: [██████████████████░░░░] 90%
"""
    elif months_away <= 3:
        return f"""
╔══════════════════════════════════════════════════╗
║  📊  {months_away} MONTHS AWAY - Almost There!  📊           ║
╚══════════════════════════════════════════════════╝
Progress: [████████████████░░░░░░] 80%
"""
    elif months_away <= 6:
        progress_pct = max(10, 100 - (months_away * 15))
        filled = int(progress_pct / 5)
        empty = 20 - filled
        bar = '█' * filled + '░' * empty
        return f"""
╔══════════════════════════════════════════════════╗
║  ⏳  {months_away} MONTHS AWAY  ⏳                         ║
╚══════════════════════════════════════════════════╝
Progress: [{bar}] {progress_pct}%
"""
    else:
        progress_pct = max(5, 100 - (months_away * 10))
        filled = int(progress_pct / 5)
        empty = 20 - filled
        bar = '█' * filled + '░' * empty
        return f"""
╔══════════════════════════════════════════════════╗
║  📅  {months_away} MONTHS AWAY  📅                         ║
╚══════════════════════════════════════════════════╝
Progress: [{bar}] {progress_pct}%
"""

def get_current_processing_data():
    """
    Scrape the FLAG website to get BOTH:
    1. The "as of" date (when data was last updated by DOL)
    2. The Analyst Review date (actual processing date)
    
    Returns: dict with 'as_of_date' and 'analyst_review_date', or None if error
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(FLAG_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the "as of" date
        # Look for text like "PERM Processing Times (as of 12/01/2025)"
        as_of_date = None
        
        # Search for heading or paragraph with "as of"
        # IMPORTANT: Look specifically for "PERM Processing Times" to avoid matching other programs
        text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div'])
        for element in text_elements:
            text = element.get_text(strip=True)
            # Must contain both "PERM" and "as of" (not just "processing")
            if 'as of' in text.lower() and 'perm' in text.lower() and 'processing' in text.lower():
                # Extract date using regex
                # Pattern 1: (as of MM/DD/YYYY)
                match = re.search(r'as of\s+(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
                if match:
                    as_of_date = match.group(1)
                    break

                # Pattern 2: (as of Month DD, YYYY)
                match = re.search(r'as of\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})', text, re.IGNORECASE)
                if match:
                    as_of_date = match.group(1)
                    break
        
        # Find the Analyst Review date from table
        analyst_review_date = None
        
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                first_cell = cells[0].get_text(strip=True)
                if 'Analyst Review' in first_cell:
                    analyst_review_date = cells[1].get_text(strip=True)
                    break
        
        if not analyst_review_date:
            print("ERROR: Could not find Analyst Review date")
            return None
        
        result = {
            'as_of_date': as_of_date or 'Not found',
            'analyst_review_date': analyst_review_date
        }
        
        print(f"Scraped data: {result}")
        return result
        
    except Exception as e:
        print(f"Error scraping website: {str(e)}")
        return None

def get_previous_data():
    """
    Get the previously stored data from DynamoDB
    Returns: dict with 'as_of_date' and 'analyst_review_date', or None
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(Key={'id': 'processing_data'})
        
        if 'Item' in response:
            return {
                'as_of_date': response['Item'].get('as_of_date'),
                'analyst_review_date': response['Item'].get('analyst_review_date')
            }
        return None
        
    except Exception as e:
        print(f"Error reading from DynamoDB: {str(e)}")
        return None

def save_current_data(data):
    """
    Save the current processing data to DynamoDB
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(
            Item={
                'id': 'processing_data',
                'as_of_date': data['as_of_date'],
                'analyst_review_date': data['analyst_review_date'],
                'last_checked': now_et().isoformat()
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
    Tracks BOTH "as of" date and Analyst Review date
    """
    
    print(f"Starting FLAG monitor check at {now_et().isoformat()}")
    
    # Get current data from website
    current_data = get_current_processing_data()
    
    if not current_data:
        error_msg = "❌ ERROR: Unable to retrieve processing times from FLAG website"
        print(error_msg)
        send_notification("FLAG Monitor Error", error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to scrape website'})
        }
    
    print(f"Current data: {current_data}")
    
    # Get previous data from DynamoDB
    previous_data = get_previous_data()
    
    # Check if MY LC date is now current!
    my_date_is_current = is_date_current_or_past(
        current_data['analyst_review_date'], 
        MY_LC_DATE
    )
    
    # Determine what changed
    as_of_changed = False
    analyst_date_changed = False
    
    if previous_data:
        as_of_changed = previous_data['as_of_date'] != current_data['as_of_date']
        analyst_date_changed = previous_data['analyst_review_date'] != current_data['analyst_review_date']
    
    # Handle different scenarios
    if not previous_data:
        # First time running
        if my_date_is_current:
            subject = "🎉 FLAG Monitor Started - Your LC Date is ALREADY Current!"
            message = f"""
FLAG DOL Processing Times Monitor is now active!

{get_progress_visual(0)}

🎊 GREAT NEWS: Your LC date is ALREADY current!

📅 Data Last Updated (as of): {current_data['as_of_date']}
📊 Analyst Review Date: {current_data['analyst_review_date']}
🎯 Your LC Date: {MY_LC_DATE}

Your PERM application should already be in the processing queue!

Twice daily (6 AM & 6 PM), you'll be notified of:
- Any changes to the "as of" date (DOL data refreshes)
- Any changes to the Analyst Review date (processing progress)
- Current status even if nothing changes

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        else:
            months_away = calculate_months_difference(current_data['analyst_review_date'], MY_LC_DATE)
            subject = "FLAG Monitor Started"
            message = f"""
FLAG DOL Processing Times Monitor is now active!

{get_progress_visual(months_away)}

📅 Data Last Updated (as of): {current_data['as_of_date']}
📊 Analyst Review Date: {current_data['analyst_review_date']}
🎯 Your LC Date: {MY_LC_DATE}

⏳ Estimated Wait: {months_away} month{"s" if months_away != 1 else ""} until your date is current

Twice daily (6 AM & 6 PM), you'll be notified of:
- Any changes to the "as of" date (DOL data refreshes)
- Any changes to the Analyst Review date (processing progress)
- Special alert when your LC date becomes current!
- Current status even if nothing changes

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        
        save_current_data(current_data)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'First run - data stored',
                'data': current_data,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }
    
    elif as_of_changed and analyst_date_changed:
        # BOTH changed!
        # Check if this made YOUR date current
        if my_date_is_current and not is_date_current_or_past(previous_data['analyst_review_date'], MY_LC_DATE):
            # YOUR DATE JUST BECAME CURRENT!
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

✅ BOTH dates changed and YOUR priority date is NOW CURRENT!

📅 Data Last Updated (as of):
   Previous: {previous_data['as_of_date']}
   New: {current_data['as_of_date']}

📊 Analyst Review Date:
   Previous: {previous_data['analyst_review_date']}
   New: {current_data['analyst_review_date']}

🎯 Your LC Date: {MY_LC_DATE}

🚀 This means your PERM application should now be in the 
   queue for processing!

NEXT STEPS:
1. Keep an eye on your email for any RFE (Request for Evidence)
2. Check your PERM case status regularly
3. Coordinate with your attorney/HR

Check the full details at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}

🎊 Best of luck with your green card journey! 🎊
            """
        else:
            months_away = calculate_months_difference(current_data['analyst_review_date'], MY_LC_DATE)
            subject = "🎉 FLAG UPDATE: Both Dates Changed!"
            message = f"""
FLAG DOL Processing Times - IMPORTANT UPDATE

🎉 BOTH dates have changed!

{get_progress_visual(months_away) if months_away > 0 else ""}

📅 Data Last Updated (as of):
   Previous: {previous_data['as_of_date']}
   New: {current_data['as_of_date']}

📊 Analyst Review Date:
   Previous: {previous_data['analyst_review_date']}
   New: {current_data['analyst_review_date']}

🎯 Your LC Date: {MY_LC_DATE}
   Status: {"✅ CURRENT!" if my_date_is_current else f"{months_away} month{'s' if months_away != 1 else ''} away"}

✅ DOL updated their data AND processing moved forward!

Check the full details at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        
        save_current_data(current_data)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Both dates changed',
                'previous': previous_data,
                'current': current_data,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }
    
    elif as_of_changed and not analyst_date_changed:
        # Only "as of" changed - Data refreshed but no progress
        months_away = calculate_months_difference(current_data['analyst_review_date'], MY_LC_DATE)
        subject = "📊 FLAG UPDATE: Data Refreshed (No Progress Yet)"
        message = f"""
FLAG DOL Processing Times - Data Updated

{get_progress_visual(months_away) if months_away > 0 else ""}

📅 DOL refreshed their data, but processing hasn't moved forward yet.

Data Last Updated (as of):
   Previous: {previous_data['as_of_date']}
   New: {current_data['as_of_date']}

📊 Analyst Review Date (unchanged):
   Still: {current_data['analyst_review_date']}

🎯 Your LC Date: {MY_LC_DATE}
   Status: {"✅ Already current!" if my_date_is_current else f"{months_away} month{'s' if months_away != 1 else ''} away"}

ℹ️ This is normal - DOL updates data periodically even when processing 
   dates don't change. It confirms the data is current.

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
        """
        
        save_current_data(current_data)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'As of date changed, analyst date unchanged',
                'previous': previous_data,
                'current': current_data,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }
    
    elif not as_of_changed and analyst_date_changed:
        # Only Analyst Review changed
        # Check if this made YOUR date current
        if my_date_is_current and not is_date_current_or_past(previous_data['analyst_review_date'], MY_LC_DATE):
            # YOUR DATE JUST BECAME CURRENT!
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

📊 Analyst Review Date:
   Previous: {previous_data['analyst_review_date']}
   New: {current_data['analyst_review_date']}

🎯 Your LC Date: {MY_LC_DATE}

📅 Data Last Updated (as of): {current_data['as_of_date']}

🚀 This means your PERM application should now be in the 
   queue for processing!

NEXT STEPS:
1. Keep an eye on your email for any RFE (Request for Evidence)
2. Check your PERM case status regularly
3. Coordinate with your attorney/HR

Check the full details at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}

🎊 Best of luck with your green card journey! 🎊
            """
        else:
            months_away = calculate_months_difference(current_data['analyst_review_date'], MY_LC_DATE)
            subject = "🎉 FLAG UPDATE: Processing Date Moved!"
            message = f"""
FLAG DOL Processing Times - PROCESSING MOVED FORWARD

{get_progress_visual(months_away)}

📊 The Analyst Review date changed!

Analyst Review Date:
   Previous: {previous_data['analyst_review_date']}
   New: {current_data['analyst_review_date']}

🎯 Your LC Date: {MY_LC_DATE}
   Status: {"✅ CURRENT!" if my_date_is_current else f"Getting closer! Only {months_away} month{'s' if months_away != 1 else ''} away!"}

📅 Data Last Updated (as of): {current_data['as_of_date']}

✅ PERM applications are being processed faster!

Check the full details at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        
        save_current_data(current_data)
        send_notification(subject, message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analyst date changed, as of date unchanged',
                'previous': previous_data,
                'current': current_data,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }
    
    else:
        # Nothing changed - Regular status update
        if my_date_is_current:
            subject = "FLAG Monitor: Your LC Date is Current ✅"
            message = f"""
FLAG DOL Processing Times - Daily Check

🎉 REMINDER: Your LC date is CURRENT!

📅 Data Last Updated (as of): {current_data['as_of_date']}
📊 Analyst Review Date: {current_data['analyst_review_date']}
🎯 Your LC Date: {MY_LC_DATE}

Status: No changes since last check

Your application should be in the processing queue.
Keep checking for any updates from DOL!

Next check: In 12 hours

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        else:
            months_away = calculate_months_difference(current_data['analyst_review_date'], MY_LC_DATE)
            subject = "FLAG Monitor Status: No Changes"
            message = f"""
FLAG DOL Processing Times - Daily Check

{get_progress_visual(months_away)}

📊 Current Status (No changes):

📅 Data Last Updated (as of): {current_data['as_of_date']}
📊 Analyst Review Date: {current_data['analyst_review_date']}
🎯 Your LC Date: {MY_LC_DATE}

⏳ Estimated Wait: {months_away} month{"s" if months_away != 1 else ""} until your date is current

Status: No changes since last check

Currently processing: {current_data['analyst_review_date']}
Waiting for it to reach: {MY_LC_DATE}

Next check: In 12 hours

Check the site at: {FLAG_URL}

Timestamp: {now_et().strftime('%Y-%m-%d %I:%M %p %Z')}
            """
        
        save_current_data(current_data)
        send_notification(subject, message)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No changes',
                'current': current_data,
                'my_lc_date': MY_LC_DATE,
                'my_date_is_current': my_date_is_current
            })
        }