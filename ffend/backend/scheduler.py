"""
Background scheduler that updates watering reminders
every morning based on fresh Hyderabad weather
"""


from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

import pytz
from datetime import datetime, timedelta

# Define scheduler globally
scheduler = BackgroundScheduler()

# Define logger globally
logger = logging.getLogger(__name__)

def weather_sync_and_reminder_scheduler(app):
    """
    Runs every 15 minutes (or 2 minutes in testing mode).
    Uses Gemini API with pre-saved plant data for intelligent watering schedules.
    No Plant.id API calls - uses stored plant information.
    """
    with app.app_context():
        try:
            from models import db, WateringReminder, GardenPlant
            from weather_helper import get_current_weather, get_gemini_watering_schedule
            from calendar_helper import create_watering_event

            reminders = WateringReminder.query.filter_by(reminder_enabled=True).all()
            print(f"📋 Found {len(reminders)} active reminders")

            for reminder in reminders:
                try:
                    plant = GardenPlant.query.get(reminder.plant_id)
                    if not plant:
                        continue

                    latitude = reminder.latitude
                    longitude = reminder.longitude
                    tz_str = reminder.user_timezone or 'UTC'
                    user_email = plant.user.email if hasattr(plant, 'user') and hasattr(plant.user, 'email') else None

                    # 1. Fetch weather for user location
                    weather = get_current_weather(latitude=latitude, longitude=longitude)
                    print(f"🌤️ Weather for {plant.plant_name} ({user_email}): {weather}")

                    # 2. Use pre-saved plant data (NO Plant.id API calls)
                    plant_data = {
                        'plant_name': plant.plant_name,
                        'scientific_name': plant.scientific_name,
                        'soil_type': plant.soil_type or 'well-draining',
                        'watering_capacity': plant.watering_capacity,
                        'sunlight_requirements': plant.sunlight_requirements,
                        'humidity_level': plant.humidity_level,
                        'temperature_range': plant.temperature_range,
                        'age': plant.age,
                        'fertilizer_needs': plant.fertilizer_needs
                    }
                    
                    # 3. Get Gemini-powered watering schedule
                    schedule = get_gemini_watering_schedule(plant_data, weather)
                    care_message = schedule.get('care_message', f'Time to check on your {plant.plant_name}!')
                    skip_watering = schedule.get('skip_watering', False)
                    interval_days = schedule.get('interval_days', reminder.interval_days)
                    
                    print(f"🤖 Gemini schedule for {plant.plant_name}: {interval_days} days, skip={skip_watering} (source: {schedule.get('source')})")
                    
                    # Update reminder interval if changed
                    if interval_days != reminder.interval_days:
                        reminder.interval_days = interval_days
                        print(f"📅 Updated watering interval to {interval_days} days")

                    # 4. Calculate reminder time
                    now_utc = datetime.utcnow()
                    try:
                        tz = pytz.timezone(tz_str)
                        now_local = now_utc.replace(tzinfo=pytz.utc).astimezone(tz)
                    except Exception:
                        now_local = now_utc

                    reminder_time = now_local + timedelta(minutes=2)  # Testing: 2 min after sync
                    
                    # 5. Prevent duplicate reminders for same user/plant/day
                    last_sent = reminder.last_reminder_sent
                    if last_sent and last_sent.date() == reminder_time.date():
                        print(f"🔁 Reminder already sent today for {plant.plant_name} ({user_email})")
                        continue

                    # 6. Skip if Gemini recommends skipping (rain, high humidity, etc.)
                    if skip_watering:
                        print(f"⏭️ Skipping watering for {plant.plant_name}: {schedule.get('skip_reason', 'Weather conditions')}")
                        # Still update the last check time but don't send reminder
                        reminder.weather_temp = weather.get('temp')
                        reminder.weather_humidity = weather.get('humidity')
                        reminder.weather_condition = weather.get('description')
                        db.session.commit()
                        continue

                    # 7. Create Google Calendar event with Gemini-generated care message
                    event_id = create_watering_event(
                        plant.plant_name,
                        interval_days,
                        weather,
                        user_email=user_email,
                        timezone=tz_str,
                        reminder_time=reminder_time.strftime('%H:%M'),
                        latitude=latitude,
                        longitude=longitude,
                        care_message=care_message,
                        start_dt=reminder_time,
                        end_dt=reminder_time + timedelta(minutes=15)
                    )
                    
                    # 8. Update reminder record
                    reminder.calendar_event_id = event_id
                    reminder.last_reminder_sent = reminder_time
                    reminder.weather_temp = weather.get('temp')
                    reminder.weather_humidity = weather.get('humidity')
                    reminder.weather_condition = weather.get('description')
                    db.session.commit()
                    
                    print(f"✅ Reminder scheduled for {plant.plant_name} ({user_email}) at {reminder_time}")

                except Exception as e:
                    print(f"❌ Error scheduling reminder for {reminder.id}: {e}")
                    continue

        except Exception as e:
            print(f"❌ Scheduler error: {e}")


def start_scheduler(app):
    """
    Call this once when Flask app starts.
    Schedules the morning update job.
    """
    # Run every 15 minutes
    scheduler.add_job(
        func=weather_sync_and_reminder_scheduler,
        trigger=CronTrigger(minute='*/2'),  # For testing: every 2 minutes
        args=[app],
        id='weather_sync_reminder',
        name='Weather sync and reminder scheduling',
        replace_existing=True
    )
    scheduler.start()
    print("⏰ Scheduler started! Weather sync every 15 minutes")
    logger.info("⏰ Scheduler started!")