"""
LightMeter Analysis Routes
===========================
Plant light analysis endpoint integrated with Gemini API with key rotation
Flow: Plant.ID (identify species) → Gemini (get light requirements) → Grayscale (measure light) → Compare
"""

from flask import Blueprint, request, jsonify, render_template_string, send_from_directory
from PIL import Image
import numpy as np
import requests
import base64
import io
from datetime import datetime
import random
from difflib import SequenceMatcher
import json
import logging
import os
from config import Config

logger = logging.getLogger(__name__)

lightmeter_bp = Blueprint('lightmeter', __name__)

# Load API Keys from config (which loads from .env)
config = Config()
GEMINI_API_KEYS = config.GEMINI_API_KEYS  # List of keys for rotation
PLANTID_API_KEYS = config.PLANTID_API_KEYS  # List of keys for rotation
PLANTID_API_URL = config.PLANTID_API_URL  # v3 from config
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')  # Loaded from .env

# Import Gemini API safely
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning('[WARNING] google.generativeai not available')

# Gemini key rotation index
_gemini_key_idx = 0

def _get_next_gemini_key():
    """Get next Gemini key for rotation"""
    global _gemini_key_idx
    if not GEMINI_API_KEYS or len(GEMINI_API_KEYS) == 0:
        return None
    key = GEMINI_API_KEYS[_gemini_key_idx % len(GEMINI_API_KEYS)]
    _gemini_key_idx += 1
    return key

def _configure_gemini_api():
    """Configure Gemini API with current key"""
    key = _get_next_gemini_key()
    if key and key.strip():
        try:
            genai.configure(api_key=key)
            logger.debug(f'[GEMINI] Configured with key rotation index {_gemini_key_idx - 1}')
            return True
        except Exception as e:
            logger.warning(f'[GEMINI] Configuration failed with key: {str(e)}')
            return False
    return False

# Validate Gemini API
if GEMINI_AVAILABLE:
    if GEMINI_API_KEYS and len(GEMINI_API_KEYS) > 0:
        _configure_gemini_api()
        logger.info(f'[GEMINI] API ready with {len(GEMINI_API_KEYS)} keys for rotation')
    else:
        logger.warning('[WARNING] GEMINI_API_KEYS not configured - light requirements will be hardcoded')
else:
    logger.warning('[WARNING] google.generativeai library not installed')

# Plant Database with ideal light requirements (grayscale values)
PLANT_DATABASE = {
    'snake plant': {'min': 50, 'max': 200, 'ideal': 'Low to Bright', 'is_low_light': True},
    'pothos': {'min': 60, 'max': 180, 'ideal': 'Low to Medium', 'is_low_light': True},
    'philodendron': {'min': 65, 'max': 170, 'ideal': 'Low to Medium', 'is_low_light': True},
    'monstera': {'min': 80, 'max': 200, 'ideal': 'Medium to Bright', 'is_low_light': False},
    'fiddle leaf fig': {'min': 140, 'max': 220, 'ideal': 'Medium-Bright to Bright', 'is_low_light': False},
    'peace lily': {'min': 50, 'max': 150, 'ideal': 'Low to Medium', 'is_low_light': True},
    'areca palm': {'min': 100, 'max': 200, 'ideal': 'Medium to Bright', 'is_low_light': False},
    'rubber plant': {'min': 120, 'max': 220, 'ideal': 'Medium to Bright', 'is_low_light': False},
    'spider plant': {'min': 70, 'max': 190, 'ideal': 'Medium to Bright', 'is_low_light': False},
    'african violet': {'min': 80, 'max': 180, 'ideal': 'Medium Light', 'is_low_light': False},
    'jade plant': {'min': 130, 'max': 230, 'ideal': 'Medium-Bright to Bright', 'is_low_light': False},
    'aloe vera': {'min': 140, 'max': 250, 'ideal': 'Bright Light', 'is_low_light': False},
    'boston fern': {'min': 60, 'max': 140, 'ideal': 'Low to Medium', 'is_low_light': True},
    'zz plant': {'min': 55, 'max': 200, 'ideal': 'Low to Bright', 'is_low_light': True},
    'chinese evergreen': {'min': 50, 'max': 140, 'ideal': 'Low to Medium', 'is_low_light': True},
    'dracaena': {'min': 50, 'max': 180, 'ideal': 'Low to Medium', 'is_low_light': True},
    'calathea': {'min': 60, 'max': 130, 'ideal': 'Low to Medium', 'is_low_light': True},
    'orchid': {'min': 90, 'max': 160, 'ideal': 'Medium Light', 'is_low_light': False},
    'succulents': {'min': 130, 'max': 240, 'ideal': 'Bright Light', 'is_low_light': False},
    'herbs': {'min': 150, 'max': 240, 'ideal': 'Bright Light', 'is_low_light': False},
}

# Common plant name aliases for better API matching
PLANT_ALIASES = {
    'sanseviera': 'snake plant',
    'sansevieria': 'snake plant',
    'sanseveria': 'snake plant',
    'devil\'s ivy': 'pothos',
    'celadon pothos': 'pothos',
    'epipremnum aureum': 'pothos',
    'swiss cheese plant': 'monstera',
    'monstera deliciosa': 'monstera',
    'ficus lyrata': 'fiddle leaf fig',
    'spathiphyllum wallisii': 'peace lily',
    'white peace lily': 'peace lily',
    'dypsis lutescens': 'areca palm',
    'chrysalidocarpus lutescens': 'areca palm',
    'ficus elastica': 'rubber plant',
    'red rubber plant': 'rubber plant',
    'chlorophytum comosum': 'spider plant',
    'saintpaulia': 'african violet',
    'crassula ovata': 'jade plant',
    'nephrolepis exaltata': 'boston fern',
    'zamioculcas zamiifolia': 'zz plant',
    'aglaonema': 'chinese evergreen',
    'goethals': 'chinese evergreen',
    'dracaena marginata': 'dracaena',
    'calathea orbifolia': 'calathea',
    'phalaenopsis': 'orchid',
    'cattleya': 'orchid',
    'dendrobium': 'orchid',
    'echeveria': 'succulents',
    'jade': 'jade plant',
    'aloe': 'aloe vera',
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_weather_by_coords(lat, lon):
    """Fetch weather data from OpenWeather API using coordinates"""
    try:
        logger.info(f"Fetching weather for coordinates: {lat}, {lon}")
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        weather_response = requests.get(weather_url, timeout=3)  # Reduced from 5 to 3 seconds
        weather_data = weather_response.json()
        
        if 'clouds' not in weather_data or 'weather' not in weather_data:
            return None
        
        location_name = weather_data.get('name', 'Unknown Location')
        if 'sys' in weather_data and 'country' in weather_data['sys']:
            location_name += f", {weather_data['sys']['country']}"
        
        return {
            'location': location_name,
            'cloud_cover': weather_data['clouds'].get('all', 50),
            'description': weather_data['weather'][0].get('description', 'Unknown'),
            'humidity': weather_data['main'].get('humidity', 50),
            'temperature': weather_data['main'].get('temp', 20)
        }
    except Exception as e:
        logger.warning(f"Error fetching weather by coordinates: {str(e)}")
        return None


def get_weather_data(location):
    """Fetch weather data from OpenWeather API"""
    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={OPENWEATHER_API_KEY}"
        geo_response = requests.get(geo_url, timeout=3)  # Reduced from 5 to 3 seconds
        geo_data = geo_response.json()
        
        if not geo_data or len(geo_data) == 0:
            return None
        
        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        
        return get_weather_by_coords(lat, lon)
    except Exception as e:
        logger.warning(f"Error fetching weather data: {str(e)}")
        return None


def estimate_sunlight_intensity(weather_data):
    """Estimate sunlight intensity (0-100) based on weather conditions"""
    if not weather_data:
        return 50
    
    cloud_cover = weather_data['cloud_cover']
    intensity = 100 - cloud_cover
    return max(10, min(100, intensity))


def generate_suggestions(detected_light_level, weather_intensity, location, plant_name=None):
    """Generate contextual suggestions based on light level, weather, and identified plant"""
    
    # Generic suggestions
    generic_suggestions = {
        'low_light': [
            "Move the plant closer to a window.",
            "Place the plant near an east-facing window for morning sunlight.",
            "Move the plant to a balcony or terrace.",
            "Avoid placing the plant in dark corners of the room.",
            "Increase exposure to natural daylight.",
            "Consider using an artificial LED grow light.",
            "Ensure the plant receives at least 4–6 hours of sunlight daily."
        ],
        'high_light': [
            "Move the plant to an area with indirect sunlight.",
            "Place the plant behind a curtain or shade.",
            "Move the plant away from direct afternoon sun.",
            "Place the plant under partial shade.",
            "Use a sheer curtain to filter intense sunlight.",
            "Consider moving the plant indoors during peak sun hours."
        ],
        'ideal_light': [
            "The lighting condition is ideal for this plant.",
            "Keep the plant in the current location.",
            "Maintain the current care routine.",
            "Monitor the plant regularly for optimal growth.",
            "This location provides perfect natural light balance."
        ]
    }
    
    # Plant-specific suggestions (when plant is identified)
    plant_specific_suggestions = {
        'low_light': [
            f"{plant_name} typically prefers bright light - this location is too shaded.",
            f"Move your {plant_name} to a brighter spot to promote healthy growth.",
            f"{plant_name} leaves may appear pale or weak in this low light condition.",
            f"A south-facing window would be ideal for your {plant_name}.",
            f"Consider supplementing with a grow light to help your {plant_name} thrive."
        ],
        'high_light': [
            f"{plant_name} is getting too much direct sun in this location.",
            f"Filter the intense light around your {plant_name} with a sheer curtain.",
            f"Move your {plant_name} slightly away from the window.",
            f"The afternoon sun may be scorching your {plant_name} - provide afternoon shade.",
            f"{plant_name} may develop bleached or burnt leaves if kept in such bright light."
        ],
        'ideal_light': [
            f"Perfect! This light level is ideal for your {plant_name}.",
            f"Your {plant_name} is receiving the optimal sunlight it needs to thrive.",
            f"Keep your {plant_name} in this location for best growth results.",
            f"The lighting here is exactly what your {plant_name} prefers.",
            f"Your {plant_name} will flourish with consistent light at this level."
        ]
    }
    
    warnings = {
        'low_light': "Low light conditions may slow plant growth and cause weak or yellowing leaves.",
        'high_light': "Excessive sunlight may cause leaf burn or dehydration.",
        'ideal_light': ""
    }
    
    smart_suggestions = {
        'low_light': [
            f"Watering: Water less frequently in low light (every 10-14 days)",
            "Pruning: Remove dead leaves to encourage new growth toward light",
            f"Humidity: Increase humidity to {weather_intensity + 20}% to compensate for low light",
            "Growth Rate: Expect slower growth - this is normal in low light conditions",
            "Winter Care: Move plant to brightest available location during winter months"
        ],
        'high_light': [
            f"Watering: Water more frequently to prevent soil dryness (every 3-5 days)",
            "Leaf Protection: Wipe leaves monthly to remove dust and maximize photosynthesis",
            f"Temperature: Keep plant cool - aim for 18-24°C with air circulation",
            "Pest Check: High light attracts more pests - inspect weekly",
            "Fertilizing: Feed every 2 weeks during growing season for strong growth"
        ],
        'ideal_light': [
            "Consistency: Maintain this light level - it's perfect for photosynthesis",
            "Rotation: Rotate plant 90° weekly for evenly distributed growth",
            f"Seasonal Adjustment: Light may decrease in winter - be prepared to relocate if needed",
            "Blooming: Ideal light promotes flowering - expect blooms in 4-8 weeks",
            "Fertilizing Schedule: Feed bi-weekly to support abundant growth"
        ]
    }
    
    category = 'ideal_light'
    if detected_light_level == 'Low Light':
        category = 'low_light'
    elif detected_light_level == 'Bright Light':
        category = 'high_light'
    
    # Choose suggestions based on whether plant was identified
    if plant_name:
        # Use plant-specific suggestions if plant was identified
        selected_suggestions = random.sample(plant_specific_suggestions[category], min(3, len(plant_specific_suggestions[category])))
    else:
        # Use generic suggestions if no plant identified
        selected_suggestions = random.sample(generic_suggestions[category], min(3, len(generic_suggestions[category])))
    
    selected_smart = random.sample(smart_suggestions[category], min(3, len(smart_suggestions[category])))
    
    return {
        'category': category,
        'suggestions': selected_suggestions,
        'warning': warnings[category],
        'smart_suggestions': selected_smart,
        'weather_intensity': weather_intensity,
        'location': location,
        'plant_identified': bool(plant_name),
        'plant_name': plant_name
    }


def identify_plant_from_image_api(img_array):
    """Identify plant using Plant.ID API with automatic key rotation"""
    try:
        logger.info('[PLANT.ID] Starting Plant.ID Identification with automatic key rotation')
        
        # Use PlantIDService for automatic key rotation
        from plantid_service import get_plantid_service
        
        service = get_plantid_service()
        if not service:
            logger.error('[PLANT.ID] PlantIDService not available')
            return {'success': False, 'error': 'PlantID service unavailable'}
        
        # Convert numpy array to PIL Image to bytes
        from PIL import Image as PILImage
        
        pil_img = PILImage.fromarray(img_array.astype('uint8'))
        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        img_bytes = img_byte_arr.getvalue()
        
        # Call PlantIDService with automatic key rotation
        result = service.identify_plant(image_data=img_bytes)
        
        logger.info(f'[PLANT.ID] Raw service response: {result}')
        
        if result and result.get('success'):
            # PlantIDService returns 'name' key, not 'plant_name'
            plant_name = result.get('name', '').lower().strip()
            confidence = result.get('confidence', 0)
            
            logger.info(f'[PLANT.ID] ✓ Success: {plant_name} ({confidence}% confidence)')
            
            return {
                'success': True,
                'plant_name': plant_name,  # Map 'name' to 'plant_name' for downstream code
                'confidence': float(confidence) / 100 if confidence > 1 else confidence,  # Normalize to 0-1
                'source': 'plantid_v3_api',
                'full_result': result  # Include full result for additional data
            }
        else:
            error_msg = result.get('error', 'Unknown error') if result else 'No result'
            logger.warning(f'[PLANT.ID] Failed: {error_msg}')
            return {'success': False, 'error': error_msg}
        
    except Exception as e:
        logger.error(f'[PLANT.ID] Exception: {str(e)}')
        logger.exception(e)
        return {'success': False, 'error': str(e)}


def detect_plant_from_image(img_array):
    """Detect plant using color analysis"""
    try:
        logger.info('Starting Advanced Plant Detection')
        from PIL import Image as PILImage
        
        pil_img = PILImage.fromarray(img_array.astype('uint8'))
        img_hsv = pil_img.convert('HSV')
        hsv_array = np.array(img_hsv)
        
        h_values = hsv_array[:,:,0]
        s_values = hsv_array[:,:,1]
        v_values = hsv_array[:,:,2]
        
        avg_hue = np.mean(h_values)
        avg_sat = np.mean(s_values)
        avg_val = np.mean(v_values)
        hue_variance = np.std(h_values)
        sat_variance = np.std(s_values)
        
        scores = {}
        
        if 40 < avg_hue < 100 and avg_sat > 30:
            if avg_val > 160:
                scores['monstera'] = 0.85
                scores['spider plant'] = 0.80
            elif avg_val > 130:
                scores['pothos'] = 0.85
                scores['monstera'] = 0.75
            else:
                scores['peace lily'] = 0.80
                scores['snake plant'] = 0.78
        
        elif (avg_hue < 30 or avg_hue > 330) and avg_sat > 20:
            if avg_val > 140:
                scores['rubber plant'] = 0.85
            else:
                scores['jade plant'] = 0.85
            scores['succulents'] = 0.75
        
        elif 50 < avg_hue < 65:
            scores['spider plant'] = 0.90
            scores['pothos'] = 0.75
        
        elif 240 < avg_hue < 360 and avg_val > 100:
            scores['orchid'] = 0.90
            scores['succulents'] = 0.70
        
        elif 180 < avg_hue < 240:
            scores['aloe vera'] = 0.85
            scores['succulents'] = 0.88
        
        elif avg_sat < 40 and avg_val > 100:
            scores['peace lily'] = 0.75
            scores['snake plant'] = 0.70
        
        if hue_variance > 25:
            scores['spider plant'] = min(1.0, scores.get('spider plant', 0.5) + 0.15)
            scores['pothos'] = min(1.0, scores.get('pothos', 0.5) + 0.10)
        
        if not scores:
            scores['snake plant'] = 0.60
            scores['monstera'] = 0.55
            scores['pothos'] = 0.50
        
        if scores:
            top_plant = max(scores, key=scores.get)
            logger.info(f'Top detection: {top_plant}')
            return top_plant
        
    except Exception as e:
        logger.warning(f'Plant detection error: {str(e)}')
    
    return 'plant'


def get_plant_info_from_gemini(plant_name):
    """Query Gemini API to get ideal light requirements with key rotation"""
    if not plant_name:
        return None
    
    if not GEMINI_AVAILABLE or not GEMINI_API_KEYS or len(GEMINI_API_KEYS) == 0:
        logger.info(f'[GEMINI] Not configured for: {plant_name}')
        return None
    
    # Try up to 3 keys before giving up
    max_attempts = min(3, len(GEMINI_API_KEYS))
    
    for attempt in range(max_attempts):
        try:
            # Configure next key
            if not _configure_gemini_api():
                logger.warning(f'[GEMINI] Failed to configure key on attempt {attempt + 1}')
                continue
            
            logger.info(f'[GEMINI] Querying for light requirements: {plant_name} (attempt {attempt + 1}/{max_attempts})')
            
            prompt = f"""
You are a plant biology expert. For the plant species: {plant_name}
            
Return ONLY valid JSON (no markdown, no extra text) with this exact format:
{{
    "plant_name": "{plant_name}",
    "min": <integer 0-255>,
    "max": <integer 0-255>,
    "ideal": "<string describing ideal light>",
    "is_low_light": <boolean>,
    "reasoning": "<brief explanation>"
}}

Scale: 0-70=Low, 71-160=Medium, 161-255=Bright

Be accurate for this specific plant."""
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt, timeout=10)
            response_text = response.text.strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.warning(f'[GEMINI] No JSON found in response: {response_text[:100]}')
                continue
            
            json_str = response_text[json_start:json_end]
            plant_data = json.loads(json_str)
            
            # Validate response
            required_keys = ['min', 'max', 'ideal', 'is_low_light']
            if not all(key in plant_data for key in required_keys):
                logger.warning(f'[GEMINI] Missing required keys in response: {plant_data.keys()}')
                continue
            
            # Ensure min < max
            min_val = int(plant_data.get('min', 50))
            max_val = int(plant_data.get('max', 200))
            if min_val >= max_val:
                min_val, max_val = min_val, max_val + 50
            
            result = {
                'name': plant_name,
                'data': {
                    'min': min_val,
                    'max': max_val,
                    'ideal': plant_data.get('ideal', 'Medium Light'),
                    'is_low_light': plant_data.get('is_low_light', False)
                },
                'reasoning': plant_data.get('reasoning', ''),
                'source': 'gemini_ai'
            }
            
            logger.info(f'[GEMINI] ✓ Success: {plant_name} - Light range {min_val}-{max_val}')
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f'[GEMINI] JSON parse error (attempt {attempt + 1}): {str(e)}')
        except Exception as e:
            logger.warning(f'[GEMINI] API error (attempt {attempt + 1}): {str(e)}')
    
    logger.warning(f'[GEMINI] All {max_attempts} attempts failed for: {plant_name}')
    return None


def get_plant_info(plant_name):
    """Get plant info from Gemini API with fallback to local database"""
    if not plant_name:
        return None
    
    plant_name_lower = plant_name.lower().strip()
    cleaned_name = plant_name_lower
    qualifiers = ['common ', 'wild ', 'variegated ', 'striped ', 'golden ', 'silver ', 'giant ', 'dwarf ']
    for qualifier in qualifiers:
        if cleaned_name.startswith(qualifier):
            cleaned_name = cleaned_name.replace(qualifier, '', 1).strip()
    
    # Try Gemini API first (with proper key rotation)
    if GEMINI_API_KEYS and len(GEMINI_API_KEYS) > 0:
        gemini_result = get_plant_info_from_gemini(cleaned_name or plant_name)
        if gemini_result:
            return gemini_result
    
    
    # Fallback to local database
    logger.debug(f'Falling back to local database for: {plant_name}')
    
    if cleaned_name in PLANT_ALIASES:
        matched_name = PLANT_ALIASES[cleaned_name]
        logger.debug(f'Alias matched "{plant_name}" to "{matched_name}"')
        return {'name': plant_name, 'data': PLANT_DATABASE[matched_name]}
    
    if cleaned_name in PLANT_DATABASE:
        return {'name': plant_name, 'data': PLANT_DATABASE[cleaned_name]}
    
    for db_plant, data in PLANT_DATABASE.items():
        if db_plant in cleaned_name or cleaned_name in db_plant:
            return {'name': plant_name, 'data': data}
    
    best_match = None
    best_ratio = 0.6
    
    for db_plant in PLANT_DATABASE.keys():
        ratio = SequenceMatcher(None, cleaned_name, db_plant).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = db_plant
    
    if best_match:
        logger.debug(f'Fuzzy matched "{plant_name}" to "{best_match}" ({best_ratio:.0%})')
        return {'name': plant_name, 'data': PLANT_DATABASE[best_match]}
    
    logger.debug(f'No match found for plant: {plant_name}')
    return None


def compare_plant_light(current_grayscale, plant_info):
    """Compare current light with plant's ideal requirements"""
    if not plant_info:
        return None
    
    plant_data = plant_info['data']
    min_val = plant_data['min']
    max_val = plant_data['max']
    
    if current_grayscale < min_val:
        status = '🔴 Too Dark'
        advice = f"Your plant needs more light. Current: {current_grayscale:.1f}, Minimum needed: {min_val}"
    elif current_grayscale > max_val:
        status = '🔴 Too Bright'
        advice = f"Light level is excessive. Current: {current_grayscale:.1f}, Maximum: {max_val}"
    else:
        status = '🟢 Perfect Light'
        advice = f"Light conditions are ideal for {plant_info['name']}!"
    
    return {
        'status': status,
        'current': current_grayscale,
        'min': min_val,
        'max': max_val,
        'advice': advice,
        'range': f"{min_val}-{max_val}"
    }


# ============================================
# LIGHTMETER ROUTES
# ============================================

# Serve LightMeter frontend files
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@lightmeter_bp.route('/lightmeter')
def serve_lightmeter():
    """Serve LightMeter HTML interface"""
    try:
        lightmeter_path = os.path.join(BACKEND_DIR, 'lightmeter.html')
        if os.path.isfile(lightmeter_path):
            return send_from_directory(BACKEND_DIR, 'lightmeter.html')
        else:
            logger.error(f'lightmeter.html not found at {lightmeter_path}')
            return jsonify({'error': 'LightMeter interface not found'}), 404
    except Exception as e:
        logger.error(f'Error serving lightmeter.html: {str(e)}')
        return jsonify({'error': 'Failed to load LightMeter'}), 500

@lightmeter_bp.route('/lightmeter.js')
def serve_lightmeter_js():
    """Serve LightMeter JavaScript file"""
    try:
        js_path = os.path.join(BACKEND_DIR, 'lightmeter.js')
        if os.path.isfile(js_path):
            return send_from_directory(BACKEND_DIR, 'lightmeter.js', mimetype='application/javascript')
        else:
            logger.error(f'lightmeter.js not found at {js_path}')
            return jsonify({'error': 'LightMeter script not found'}), 404
    except Exception as e:
        logger.error(f'Error serving lightmeter.js: {str(e)}')
        return jsonify({'error': 'Failed to load LightMeter script'}), 500

@lightmeter_bp.route('/lightmeter.css')
def serve_lightmeter_css():
    """Serve LightMeter CSS file"""
    try:
        css_path = os.path.join(BACKEND_DIR, 'lightmeter.css')
        if os.path.isfile(css_path):
            return send_from_directory(BACKEND_DIR, 'lightmeter.css', mimetype='text/css')
        else:
            logger.error(f'lightmeter.css not found at {css_path}')
            return jsonify({'error': 'LightMeter styles not found'}), 404
    except Exception as e:
        logger.error(f'Error serving lightmeter.css: {str(e)}')
        return jsonify({'error': 'Failed to load LightMeter styles'}), 500

@lightmeter_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze plant image for light conditions
    """
    import signal
    import platform
    
    # Set a timeout for the entire analysis (90 seconds max)
    def timeout_handler(signum, frame):
        logger.error('ANALYSIS TIMEOUT: Request took longer than 90 seconds')
        raise TimeoutError('Analysis request timed out')
    
    # Only set signal handler on Unix-like systems (not Windows)
    timeout_set = False
    if platform.system() != 'Windows':
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(90)  # 90 second timeout
            timeout_set = True
            logger.info('Signal timeout handler set (Unix/Linux only)')
        except Exception as e:
            logger.warning(f'Could not set timeout alarm: {e}')
    else:
        logger.info('Signal timeout skipped on Windows system')
    
    try:
        logger.info('LIGHTMETER ANALYSIS REQUEST')
        
        if 'image' not in request.files:
            logger.error('No image file in request')
            return jsonify({'error': 'No image uploaded'}), 400
        
        image_file = request.files['image']
        if not image_file or image_file.filename == '':
            logger.error('Empty image file')
            return jsonify({'error': 'No image file selected'}), 400
        
        lat = request.form.get('lat')
        lon = request.form.get('lon')
        location = request.form.get('location', 'Unknown')
        plant_name = request.form.get('plant_name', '')
        
        logger.info(f'Request: {image_file.filename}, Location: {location}')

        try:
            img = Image.open(image_file)
            img = img.convert('RGB')
            np_img = np.array(img)
            logger.info(f'Image loaded: {img.size[0]}x{img.size[1]}')
        except Exception as e:
            logger.error(f'Failed to process image: {str(e)}')
            return jsonify({'error': f'Invalid image file: {str(e)}'}), 400

        gray_img = np.dot(np_img[...,:3], [0.299, 0.587, 0.114])
        avg_gray = np.mean(gray_img)

        if avg_gray < 70:
            detected_light = 'Low Light'
        elif avg_gray < 160:
            detected_light = 'Medium Light'
        else:
            detected_light = 'Bright Light'
        
        logger.info(f'Grayscale: {avg_gray:.2f}, Light: {detected_light}')

        weather_data = None
        
        if lat and lon:
            try:
                weather_data = get_weather_by_coords(float(lat), float(lon))
            except Exception as e:
                logger.warning(f'Error fetching weather by coords: {e}')
        
        if not weather_data:
            try:
                weather_data = get_weather_data(location)
            except Exception as e:
                logger.warning(f'Error fetching weather: {e}')
        
        weather_intensity = estimate_sunlight_intensity(weather_data)
        weather_description = ''
        temperature = 'N/A'
        humidity = 'N/A'
        
        if weather_data and 'description' in weather_data:
            weather_description = weather_data['description'].title()
            temperature = weather_data.get('temperature', 'N/A')
            humidity = weather_data.get('humidity', 'N/A')
            if location == 'Unknown':
                location = weather_data.get('location', 'Unknown Location')
            logger.info(f'Weather: {weather_description}, {temperature}°C, {humidity}%')
        else:
            logger.info('Weather data unavailable')

        plant_auto_detected = False
        api_used = False
        plant_comparison = None
        plant_full_info = None
        plant_info = None  # Initialize before use
        
        if not plant_name:
            logger.info('Attempting auto-detection...')
            logger.info('[DEBUG] Attempting Plant.ID API identification...')
            api_result = identify_plant_from_image_api(np_img)
            
            logger.info(f'[DEBUG] Plant.ID API Result: {api_result}')
            
            if api_result.get('success'):
                plant_name = api_result.get('plant_name')
                api_confidence = api_result.get('confidence', 0)
                plant_auto_detected = True
                api_used = True
                plant_full_info = api_result.get('full_result')  # Save full info
                logger.info(f'[SUCCESS] Plant.ID identified: {plant_name} ({api_confidence:.0%} confidence)')
            else:
                logger.warning(f'[WARNING] Plant.ID API failed: {api_result.get("error", "Unknown error")}')
                logger.info('[DEBUG] Using local detection as fallback')
                detected_plant = detect_plant_from_image(np_img)
                if detected_plant:
                    plant_name = detected_plant
                    plant_auto_detected = True
                    logger.info(f'[LOCAL] Detected: {plant_name}')
                else:
                    logger.warning('[WARNING] Local detection also failed')
        
        # Get plant-specific information for suggestions (BEFORE generating suggestions)
        plant_comparison = None
        if plant_name:
            logger.info(f'[DEBUG] Analyzing light requirements for: {plant_name}')
            plant_info = get_plant_info(plant_name)
            
            if plant_info:
                logger.info(f'[SUCCESS] Plant info found: {plant_info.get("name")}')
                logger.info(f'[DEBUG] Light data source: {plant_info.get("source", "unknown")}')
                plant_comparison = compare_plant_light(avg_gray, plant_info)
                logger.info(f'[DEBUG] Plant comparison: {plant_comparison}')
            else:
                logger.warning(f'[WARNING] Plant not found in database: {plant_name}')
        
        # Generate suggestions AFTER plant identification (now with plant-specific info)
        suggestion_data = generate_suggestions(detected_light, weather_intensity, location, plant_name)

        response_data = {
            'average_grayscale': float(avg_gray),
            'detected_light': detected_light,
            'location': location,
            'weather_intensity': weather_intensity,
            'weather_description': weather_description,
            'temperature': temperature,
            'humidity': humidity,
            'suggestions': suggestion_data['suggestions'],
            'warning': suggestion_data['warning'],
            'has_warning': bool(suggestion_data['warning']),
            'smart_suggestions': suggestion_data['smart_suggestions'],
            'category': suggestion_data['category'],
            'api_used': api_used,
            'plantid_api_used': api_used,
            'plant_auto_detected': plant_auto_detected
        }
        
        # ALWAYS include plant_name if identified (not just when plant_comparison exists)
        if plant_name:
            response_data['plant_name'] = plant_name
            
            # Add plant-specific details from Plant.ID API
            if plant_full_info:
                # Include common names and other helpful info
                if plant_full_info.get('common_names'):
                    response_data['common_names'] = plant_full_info['common_names']
                if plant_full_info.get('description'):
                    response_data['plant_description'] = plant_full_info['description']
                if plant_full_info.get('best_light'):
                    response_data['plant_light_preference'] = plant_full_info['best_light']
                if plant_full_info.get('scientific'):
                    response_data['scientific_name'] = plant_full_info['scientific']
        
        if plant_comparison:
            response_data['plant_comparison'] = plant_comparison
            # Include source of light requirements
            if plant_info:
                response_data['light_data_source'] = plant_info.get('source', 'unknown')
                # Include plant-specific care info from light requirements
                if plant_info.get('reasoning'):
                    response_data['light_analysis_reasoning'] = plant_info['reasoning']
        
        logger.info('ANALYSIS COMPLETE')
        
        # Disable timeout alarm
        try:
            signal.alarm(0)
        except:
            pass
        
        return jsonify(response_data)
    
    except TimeoutError as e:
        logger.error(f'Analysis timeout: {str(e)}')
        try:
            signal.alarm(0)
        except:
            pass
        return jsonify({'error': 'Analysis took too long. Please try with a smaller image.'}), 504
    
    except Exception as e:
        logger.error(f'Unexpected error in analyze endpoint: {str(e)}')
        logger.exception(e)
        try:
            signal.alarm(0)
        except:
            pass
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


@lightmeter_bp.route('/analyze', methods=['GET'])
def analyze_get():
    """Health check for analyze endpoint"""
    return jsonify({"message": "LightMeter backend is running. Use POST to analyze plant data."})


@lightmeter_bp.route('/get-location-by-ip', methods=['GET'])
def get_location_by_ip():
    """Get location by user's IP address"""
    try:
        logger.info('IP Geolocation')
        
        # Primary IP API with 5 second timeout
        ip_url = "https://ip-api.com/json/?fields=status,country,city,lat,lon,countryCode,isp"
        response = requests.get(ip_url, timeout=5)
        data = response.json()
        
        if data.get('status') == 'success' and data.get('city') and data.get('lat') and data.get('lon'):
            location_data = {
                'lat': data.get('lat'),
                'lon': data.get('lon'),
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'location': f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
            }
            logger.info(f'IP Location Detected: {location_data["location"]}')
            return jsonify(location_data)
        else:
            raise Exception("Incomplete data from primary API")
    
    except Exception as e:
        logger.warning(f'Primary IP API failed (timeout or error): {str(e)}')
        
        try:
            # Fallback API with 5 second timeout
            fallback_url = "https://ipapi.co/json/"
            response = requests.get(fallback_url, timeout=5)
            data = response.json()
            
            if data.get('latitude') and data.get('longitude') and data.get('city'):
                location_data = {
                    'lat': data.get('latitude'),
                    'lon': data.get('longitude'),
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'location': f"{data.get('city', 'Unknown')}, {data.get('country_name', 'Unknown')}"
                }
                logger.info(f'Fallback IP Location: {location_data["location"]}')
                return jsonify(location_data)
            else:
                raise Exception("Incomplete data from fallback")
        
        except Exception as e2:
            logger.warning(f'Fallback API also failed: {str(e2)}')
            # Return default location quickly
            default_location = {
                'lat': 40.7128,
                'lon': -74.0060,
                'city': 'New York',
                'country': 'United States',
                'location': 'New York, United States (Default)'
            }
            logger.info('Using default location')
            return jsonify(default_location)


@lightmeter_bp.route('/get-weather-by-coords', methods=['GET'])
def get_weather_by_coords_endpoint():
    """Get weather data by latitude and longitude"""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not lat or not lon:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    try:
        lat = float(lat)
        lon = float(lon)
        weather_data = get_weather_by_coords(lat, lon)
        
        if weather_data:
            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Unable to fetch weather'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@lightmeter_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'LightMeter Backend',
        'version': '2.0',
        'endpoints': [
            'GET  /analyze              - Health check',
            'POST /analyze              - Analyze image & plant light',
            'GET  /get-location-by-ip   - Geolocation by IP',
            'GET  /get-weather-by-coords - Weather by coordinates'
        ]
    }), 200
