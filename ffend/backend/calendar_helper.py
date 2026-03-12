import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")


def get_calendar_service():
    """Loads credentials and returns Google Calendar service"""
    creds = None
    
    try:
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logger.info("✅ Token loaded from token.json")

        if not creds or not creds.valid:
            logger.warning(f"⚠️ Token invalid. Valid: {creds.valid if creds else False}")
            
            if creds and creds.expired and creds.refresh_token:
                logger.info("🔄 Attempting to refresh expired token...")
                try:
                    creds.refresh(Request())
                    logger.info("✅ Token refreshed successfully!")
                    # Save refreshed token
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())
                except Exception as refresh_error:
                    logger.error(f"❌ Token refresh failed: {str(refresh_error)}")
                    raise
            else:
                logger.error("❌ No valid refresh token available. Cannot authenticate!")
                raise Exception("No valid credentials and cannot refresh token")

        service = build("calendar", "v3", credentials=creds)
        logger.info("✅ Google Calendar service created successfully")
        return service
        
    except Exception as e:
        logger.error(f"❌ Calendar service error: {str(e)}", exc_info=True)
        raise


def create_watering_event(plant_name, interval_days, weather, user_email=None, timezone='UTC', reminder_time='07:00', latitude=None, longitude=None, care_message=None, start_dt=None, end_dt=None):
    """Creates Google Calendar watering reminder for user with attendee and email reminder. Supports dynamic care message and event timing."""
    try:
        service = get_calendar_service()

        # Use provided start/end datetime or fallback
        if start_dt and end_dt:
            start_date = start_dt
            end_date = end_dt
        else:
            hour, minute = 7, 0
            try:
                hour, minute = map(int, reminder_time.split(':'))
            except Exception:
                hour, minute = 7, 0
            now = datetime.now()
            start_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            end_date = start_date + timedelta(minutes=15)

        # Weather summary
        weather_summary = f"🌡️ Temp: {weather.get('temp', 'N/A')}°C\n💦 Humidity: {weather.get('humidity', 'N/A')}%\n☁️ Condition: {weather.get('description', 'N/A')}"
        location_summary = f"Lat: {latitude}, Lon: {longitude}" if latitude and longitude else "Location not available"

        description = (
            f"{care_message or 'Good morning!'}\n\n"
            f"Plant Care Reminder - {plant_name}\n\n"
            f"{weather_summary}\n{location_summary}\n\n"
            f"💧 Watering every {interval_days} day(s)\n"
            f"🌿 Powered by GreenSphere"
        )

        event = {
            "summary": f"Plant Care Reminder - {plant_name}",
            "description": description,
            "start": {
                "dateTime": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": timezone,
            },
            "attendees": [
                {"email": user_email}
            ] if user_email else [],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 0}
                ],
            },
        }

        created = service.events().insert(
            calendarId="primary",
            body=event,
            sendUpdates="all"
        ).execute()

        event_link = created.get('htmlLink', 'N/A')
        event_id = created.get("id")
        logger.info(f"✅ Calendar event created: {event_link} (ID: {event_id})")
        print(f"Google Calendar API response: {created}")
        return event_id
    except Exception as e:
        logger.error(f"❌ Failed to create calendar event: {str(e)}", exc_info=True)
        raise


def delete_watering_event(event_id):
    """Deletes a watering reminder from Google Calendar"""
    try:
        service = get_calendar_service()
        service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()
        logger.info(f"✅ Calendar event {event_id} deleted successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Could not delete event {event_id}: {str(e)}", exc_info=True)
        return False