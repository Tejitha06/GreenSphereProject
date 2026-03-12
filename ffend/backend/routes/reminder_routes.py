"""
Watering Reminder Routes - Uses Gemini API with pre-saved plant data
"""

from flask import Blueprint, request, jsonify
from models import db, GardenPlant, WateringReminder, User
from datetime import datetime, timezone as dt_timezone
import logging
import os
import sys

# Go up one level from routes/ to backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from weather_helper import get_current_weather, get_gemini_watering_schedule
from calendar_helper import create_watering_event, delete_watering_event

logger = logging.getLogger(__name__)
reminder_bp = Blueprint('reminder', __name__)


@reminder_bp.route('/reminder/<int:plant_id>', methods=['POST'])
def toggle_reminder(plant_id):
    """Enable or disable watering reminder for a plant"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400


        reminder_enabled = data.get('reminder_enabled', False)
        user_id = data.get('user_id')
        user_email = data.get('user_email')
        plant_name = data.get('plant_name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        timezone = data.get('timezone') or 'UTC'
        reminder_time = data.get('reminder_time') or '07:00'

        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        plant = GardenPlant.query.filter_by(
            id=plant_id,
            user_id=user_id
        ).first()

        if not plant:
            return jsonify({'success': False, 'message': 'Plant not found'}), 404

        # ── ENABLE REMINDER ──
        if reminder_enabled:
            # Delete existing reminder if any
            existing = WateringReminder.query.filter_by(
                plant_id=plant_id,
                user_id=user_id
            ).first()

            if existing:
                try:
                    delete_watering_event(existing.calendar_event_id)
                except Exception as e:
                    logger.warning(f'Could not delete old event: {e}')
                db.session.delete(existing)
                db.session.commit()

            # 1. Get live weather for user location
            weather = get_current_weather(latitude=latitude, longitude=longitude)

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
            
            # 3. Get Gemini-powered watering schedule using pre-saved data
            schedule = get_gemini_watering_schedule(plant_data, weather)
            interval = schedule['interval_days']
            care_message = schedule.get('care_message', '')
            
            logger.info(f"📅 Watering schedule for {plant.plant_name}: {interval} days (source: {schedule.get('source', 'unknown')})")

            # 4. Create Google Calendar event with attendee and email reminder
            display_name = plant.preferred_name or plant.plant_name
            try:
                event_id = create_watering_event(
                    display_name,
                    interval,
                    weather,
                    user_email=user_email,
                    timezone=timezone,
                    reminder_time=reminder_time,
                    latitude=latitude,
                    longitude=longitude,
                    care_message=care_message
                )
                logger.info(f'✅ Calendar event created: {event_id}')
            except Exception as e:
                logger.error(f'❌ Calendar event creation failed: {str(e)}', exc_info=True)
                return jsonify({
                    'success': False,
                    'message': f'Failed to create calendar event: {str(e)}'
                }), 500

            # 5. Save to database
            reminder = WateringReminder(
                user_id=user_id,
                plant_id=plant_id,
                calendar_event_id=event_id,
                interval_days=interval,
                weather_temp=weather.get('temp'),
                weather_humidity=weather.get('humidity'),
                weather_condition=weather.get('description'),
                latitude=latitude,
                longitude=longitude,
                user_timezone=timezone,
                reminder_time=reminder_time
            )
            db.session.add(reminder)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Reminder set! Watering every {interval} day(s).',
                'interval_days': interval,
                'care_message': care_message,
                'next_watering_advice': schedule.get('next_watering_advice', ''),
                'schedule_source': schedule.get('source', 'unknown'),
                'weather': weather,
                'event_id': event_id
            })

        # ── DISABLE REMINDER ──
        else:
            existing = WateringReminder.query.filter_by(
                plant_id=plant_id,
                user_id=user_id
            ).first()

            if existing:
                try:
                    delete_watering_event(existing.calendar_event_id)
                except Exception as e:
                    logger.warning(f'Could not delete event: {e}')
                db.session.delete(existing)
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Reminder removed from Google Calendar.'
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'No reminder found to remove.'
                })

    except Exception as e:
        logger.error(f'Reminder error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@reminder_bp.route('/reminder/<int:plant_id>', methods=['GET'])
def get_reminder_status(plant_id):
    """Check if reminder exists for a plant"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'User ID required'}), 401

        reminder = WateringReminder.query.filter_by(
            plant_id=plant_id,
            user_id=user_id
        ).first()

        return jsonify({
            'success': True,
            'has_reminder': reminder is not None,
            'reminder': reminder.to_dict() if reminder else None
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500