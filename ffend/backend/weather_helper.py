import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
CITY = "Hyderabad"

# Gemini API configuration for watering schedules
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'


class GeminiKeyRotator:
    """Manages multiple Gemini API keys and rotates on rate limit errors"""
    def __init__(self):
        api_keys_str = os.getenv('GEMINI_API_KEYS', '')
        self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        self.current_index = 0
        if self.api_keys:
            logger.info(f'[WateringHelper] Initialized {len(self.api_keys)} Gemini API keys')
    
    def get_next_key(self):
        """Get the next API key in rotation"""
        if not self.api_keys:
            return None
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        return key

# Initialize key rotator
gemini_rotator = GeminiKeyRotator()


def get_current_weather(latitude=None, longitude=None):
    """Fetches live weather for user location (lat/lon) or Hyderabad fallback"""
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        if latitude and longitude:
            params["lat"] = latitude
            params["lon"] = longitude
        else:
            params["q"] = CITY

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        weather = {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["main"],
            "city": data.get("name", CITY),
            "lat": data.get("coord", {}).get("lat"),
            "lon": data.get("coord", {}).get("lon")
        }
        print(f"🌤️ Weather fetched: {weather}")
        return weather

    except Exception as e:
        print(f"⚠️ Weather fetch failed: {e}")
        # Safe fallback — average Hyderabad weather
        return {
            "temp": 30,
            "humidity": 60,
            "description": "Clear",
            "city": CITY,
            "lat": None,
            "lon": None
        }


def calculate_watering_days(plant_name, soil_type, weather):
    """
    Calculates watering interval based on
    plant type + soil + live weather
    """

    # ── Step 1: Base interval by plant type ──
    plant = plant_name.lower()

    if any(p in plant for p in ["cactus", "succulent", "aloe", "agave"]):
        base_days = 14
    elif any(p in plant for p in ["fern", "calathea", "peace lily", "orchid"]):
        base_days = 2
    elif any(p in plant for p in ["monstera", "pothos", "philodendron", "ivy"]):
        base_days = 5
    elif any(p in plant for p in ["rose", "jasmine", "hibiscus", "marigold"]):
        base_days = 3
    elif any(p in plant for p in ["lavender", "sage", "rosemary", "thyme"]):
        base_days = 7
    elif any(p in plant for p in ["tulsi", "basil", "mint", "cilantro"]):
        base_days = 2
    elif any(p in plant for p in ["tomato", "pepper", "cucumber", "spinach"]):
        base_days = 2
    elif any(p in plant for p in ["palm", "banana", "mango", "avocado"]):
        base_days = 4
    else:
        base_days = 5

    # ── Step 2: Adjust for soil type ──
    soil = soil_type.lower()

    if "sandy" in soil or "well-drain" in soil:
        base_days -= 1
    elif "clay" in soil:
        base_days += 2
    elif "loam" in soil:
        pass
    elif "peat" in soil or "organic" in soil:
        base_days += 1

    # ── Step 3: Adjust for live weather ──
    temp = weather["temp"]
    humidity = weather["humidity"]
    condition = weather["description"]

    if temp > 38:
        base_days -= 2
    elif temp > 33:
        base_days -= 1

    if condition in ["Rain", "Drizzle", "Thunderstorm"]:
        base_days += 3

    if humidity < 30:
        base_days -= 1
    elif humidity > 75:
        base_days += 1

    return max(1, base_days)


def get_gemini_watering_schedule(plant_data, weather):
    """
    Uses Gemini API to calculate intelligent watering schedule based on 
    pre-saved plant data and current weather conditions.
    
    Args:
        plant_data: dict with keys like plant_name, scientific_name, soil_type, 
                    watering_capacity, sunlight_requirements, humidity_level, 
                    temperature_range, age, etc.
        weather: dict with temp, humidity, description, city
    
    Returns:
        dict with interval_days, care_message, next_watering_advice
    """
    api_key = gemini_rotator.get_next_key()
    
    if not api_key:
        logger.warning("No Gemini API key available, falling back to rule-based calculation")
        return _fallback_watering_schedule(plant_data, weather)
    
    try:
        # Build comprehensive prompt with all plant data
        plant_name = plant_data.get('plant_name', 'Unknown Plant')
        scientific_name = plant_data.get('scientific_name', '')
        soil_type = plant_data.get('soil_type', 'well-draining')
        watering_capacity = plant_data.get('watering_capacity', '')
        sunlight_req = plant_data.get('sunlight_requirements', '')
        humidity_level = plant_data.get('humidity_level', '')
        temperature_range = plant_data.get('temperature_range', '')
        age = plant_data.get('age', 'unknown')
        
        prompt = f"""You are a plant care expert. Based on the following plant and weather data, provide a watering schedule recommendation.

PLANT INFORMATION (Pre-saved data - use this, do NOT call any external plant identification API):
- Common Name: {plant_name}
- Scientific Name: {scientific_name or 'Not specified'}
- Current Age: {age}
- Soil Type: {soil_type}
- Stored Watering Info: {watering_capacity or 'Not specified'}
- Sunlight Requirements: {sunlight_req or 'Not specified'}
- Preferred Humidity: {humidity_level or 'Not specified'}
- Temperature Range: {temperature_range or 'Not specified'}

CURRENT WEATHER CONDITIONS:
- Temperature: {weather.get('temp', 'N/A')}°C
- Humidity: {weather.get('humidity', 'N/A')}%
- Conditions: {weather.get('description', 'Clear')}
- Location: {weather.get('city', 'Unknown')}

TASK: Provide a JSON response with EXACTLY this format (no markdown, no code blocks):
{{"interval_days": <number 1-14>, "care_message": "<brief morning reminder message>", "next_watering_advice": "<specific advice for this plant today>", "skip_watering": <true/false>, "skip_reason": "<reason if skip_watering is true, otherwise empty string>"}}

RULES:
1. interval_days should be between 1-14 based on plant type and weather
2. Consider rain/high humidity as reasons to skip watering
3. Consider high temperature as reason to water more frequently
4. Use the stored watering_capacity info if available
5. Adjust for plant age (younger plants need more frequent watering)
6. Return ONLY the JSON, no explanations"""

        headers = {'Content-Type': 'application/json'}
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.3,
                'maxOutputTokens': 500
            }
        }
        
        response = requests.post(
            f'{GEMINI_API_URL}?key={api_key}',
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                
                # Parse JSON response (handle potential markdown wrapping)
                import json
                if text.startswith('```'):
                    text = text.split('```')[1]
                    if text.startswith('json'):
                        text = text[4:]
                text = text.strip()
                
                schedule = json.loads(text)
                
                logger.info(f"✅ Gemini watering schedule for {plant_name}: {schedule.get('interval_days')} days")
                return {
                    'interval_days': int(schedule.get('interval_days', 3)),
                    'care_message': schedule.get('care_message', f'Time to check on your {plant_name}!'),
                    'next_watering_advice': schedule.get('next_watering_advice', ''),
                    'skip_watering': schedule.get('skip_watering', False),
                    'skip_reason': schedule.get('skip_reason', ''),
                    'source': 'gemini'
                }
        
        logger.warning(f"Gemini API returned status {response.status_code}")
        return _fallback_watering_schedule(plant_data, weather)
        
    except Exception as e:
        logger.error(f"Gemini watering schedule error: {e}")
        return _fallback_watering_schedule(plant_data, weather)


def _fallback_watering_schedule(plant_data, weather):
    """
    Fallback to rule-based watering calculation when Gemini is unavailable.
    Uses the existing calculate_watering_days logic.
    """
    plant_name = plant_data.get('plant_name', 'Plant')
    soil_type = plant_data.get('soil_type', 'well-draining')
    
    interval = calculate_watering_days(plant_name, soil_type, weather)
    
    # Generate care message based on weather
    temp = weather.get('temp', 25)
    humidity = weather.get('humidity', 50)
    condition = weather.get('description', 'Clear')
    
    skip_watering = False
    skip_reason = ''
    
    if condition in ['Rain', 'Drizzle', 'Thunderstorm']:
        skip_watering = True
        skip_reason = "Rain detected in your area"
        care_message = f"☔ Rain today! Skip watering your {plant_name}."
    elif humidity > 85:
        skip_watering = True
        skip_reason = "Very high humidity"
        care_message = f"💨 High humidity today. Your {plant_name} doesn't need watering."
    elif temp > 35:
        care_message = f"🌡️ Hot day! Your {plant_name} may need extra water today."
    else:
        care_message = f"Good morning! Time to check on your {plant_name}."
    
    return {
        'interval_days': interval,
        'care_message': care_message,
        'next_watering_advice': f"Water every {interval} day(s) based on current conditions.",
        'skip_watering': skip_watering,
        'skip_reason': skip_reason,
        'source': 'fallback'
    }


def get_plant_care_context(plant_data):
    """
    Extracts relevant care context from pre-saved plant data.
    This prevents the need to call Plant.id API repeatedly.
    """
    return {
        'name': plant_data.get('plant_name', 'Unknown'),
        'scientific_name': plant_data.get('scientific_name', ''),
        'soil_type': plant_data.get('soil_type', 'well-draining'),
        'watering_info': plant_data.get('watering_capacity', ''),
        'sunlight': plant_data.get('sunlight_requirements', ''),
        'humidity': plant_data.get('humidity_level', ''),
        'temperature': plant_data.get('temperature_range', ''),
        'age': plant_data.get('age', 'unknown'),
        'fertilizer': plant_data.get('fertilizer_needs', '')
    }