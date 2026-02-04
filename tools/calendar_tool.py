"""
Calendar Tool
Calendar operations with Google Calendar integration and robust time parsing
"""

import os.path
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pickle

# Google API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Local simulation fallback
_local_events = []
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'token.pickle')


class CalendarEvent:
    """Represents a calendar event"""
    def __init__(self, title: str, start_time: datetime, end_time: datetime, description: str = ""):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.description = description


def get_google_service():
    """Authenticate and return Google Calendar service"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds, cache_discovery=False)


def parse_time(time_str: str, date_str: str = "today") -> datetime:
    """
    Robustly parse time strings like "10PM", "10:30 PM", "22:00", "10pm IST"
    """
    now = datetime.now()
    
    # Parse date
    if date_str.lower() == "today":
        date = now.date()
    elif date_str.lower() == "tomorrow":
        date = (now + timedelta(days=1)).date()
    else:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            date = now.date()
    
    # Clean input
    time_str = time_str.strip().upper()
    
    # Remove common timezone suffixes to avoid parsing errors
    # e.g. "10PM IST" -> "10PM"
    time_str = re.sub(r'\s+(IST|EST|PST|CST|MST|GMT|UTC|[A-Z]{3,4})$', '', time_str)
    
    # Regex for various time formats
    # Matches: 10, 10:30, 10PM, 10:30PM, 10 PM
    match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$', time_str)
    
    if not match:
        # Default to 9 AM if parsing fails completely
        return datetime.combine(date, datetime.min.time().replace(hour=9))
        
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    meridiem = match.group(3)
    
    if meridiem == "PM" and hour != 12:
        hour += 12
    elif meridiem == "AM" and hour == 12:
        hour = 0
        
    return datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))


def check_calendar(date: str = "today") -> Dict:
    """Check calendar events (Google or Local)"""
    try:
        service = get_google_service()
        target_date = parse_time("9 AM", date)
        
        # Google Calendar
        if service:
            start_of_day = target_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end_of_day = target_date.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            events_result = service.events().list(calendarId='primary', timeMin=start_of_day,
                                                timeMax=end_of_day, singleEvents=True,
                                                orderBy='startTime').execute()
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                # Simple formatting
                if 'T' in start:
                    dt_start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_fmt_start = dt_start.strftime("%I:%M %p")
                    
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    dt_end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    time_fmt_end = dt_end.strftime("%I:%M %p")
                else:
                    time_fmt_start = "All Day"
                    time_fmt_end = "All Day"
                    
                formatted_events.append({
                    "title": event['summary'],
                    "start": time_fmt_start,
                    "end": time_fmt_end,
                    "description": event.get('description', '')
                })
                
            return {
                "success": True,
                "type": "google_calendar",
                "date": str(target_date.date()),
                "events": formatted_events,
                "count": len(formatted_events)
            }
            
        # Local Fallback
        else:
            local_events_on_date = [
                e for e in _local_events
                if e.start_time.date() == target_date.date()
            ]
            return {
                "success": True,
                "type": "local_simulation",
                "date": str(target_date.date()),
                "events": [
                    {
                        "title": e.title,
                        "start": e.start_time.strftime("%I:%M %p"),
                        "end": e.end_time.strftime("%I:%M %p"),
                        "description": e.description
                    }
                    for e in local_events_on_date
                ],
                "count": len(local_events_on_date)
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_event(title: str, start_time_str: str, duration_minutes: int = 60,
                 date: str = "today", description: str = "") -> Dict:
    """Create event (Google or Local)"""
    try:
        start_time = parse_time(start_time_str, date)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        service = get_google_service()
        
        # Google Calendar
        if service:
            # Google Calendar API requires timezone-aware datetime if 'timeZone' is not specified
            # or if 'timeZone' is None.
            # Convert naive datetime to local system time (aware)
            start_time_aware = start_time.astimezone()
            end_time_aware = end_time.astimezone()
            
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time_aware.isoformat(),
                },
                'end': {
                    'dateTime': end_time_aware.isoformat(),
                },
            }
            event = service.events().insert(calendarId='primary', body=event).execute()
            return {
                "success": True,
                "type": "google_calendar",
                "message": f"Created Google Calendar event: {title}",
                "link": event.get('htmlLink')
            }
            
        # Local Fallback
        else:
            new_event = CalendarEvent(title, start_time, end_time, description)
            _local_events.append(new_event)
            return {
                "success": True,
                "type": "local_simulation",
                "message": f"Created local event: {title}",
                "start": start_time.strftime("%I:%M %p")
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}
