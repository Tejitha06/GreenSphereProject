"""
Plant identification routes
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import logging
from datetime import datetime, timezone
from plantid_service import get_plantid_service

plant_bp = Blueprint('plants', __name__)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@plant_bp.route('/identify', methods=['POST'])
def identify_plant():
    """
    Identify a plant from an uploaded image
    
    Expected request:
    - Content-Type: multipart/form-data
    - Files: 'image' (required) - Plant image file
    
    Returns:
    {
        "success": true,
        "data": {
            "confidence": 95.5,
            "name": "Plant Name",
            "scientific": "Scientific name",
            "common_names": ["Common 1", "Common 2"],
            "description": "...",
            "purposes": ["Air Purification", "Decorative"],
            "suitability": "...",
            "soil": "...",
            "water": "...",
            "climate": "...",
            "toxicity": "safe",
            "toxicityInfo": "...",
            "medical": "..."
        }
    }
    """
    try:
        # Check if image file is provided
        if 'image' not in request.files:
            logger.warning('Plant identification request without image file')
            return jsonify({
                'success': False,
                'error': 'Missing image file',
                'message': 'Please upload an image file with key "image"'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning('Plant identification request with empty filename')
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            logger.warning(f'Invalid file type: {file.filename}')
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'message': f'Allowed formats: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f'File too large: {file_size} bytes')
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'Maximum file size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 413
        
        # Read file data
        image_data = file.read()
        filename = secure_filename(file.filename)
        
        logger.info(f'Processing plant identification for file: {filename}')
        
        # Get PlantID service and identify plant
        plantid_service = get_plantid_service()
        result = plantid_service.identify_plant(image_data, filename)
        
        if result is None:
            logger.error('PlantID service returned no result')
            return jsonify({
                'success': False,
                'error': 'Identification failed',
                'message': 'Could not identify plant from image. Please try with a clearer photo.'
            }), 500
        
        logger.info(f'Plant identification successful: {result.get("name")}')
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error during plant identification: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@plant_bp.route('/identify/base64', methods=['POST'])
def identify_plant_base64():
    """
    Identify a plant from a base64-encoded image
    
    Expected request (JSON):
    {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJ...",
        "filename": "plant.jpg" (optional)
    }
    
    Returns: Same as /identify endpoint
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            logger.warning('Plant identification request without image data')
            return jsonify({
                'success': False,
                'error': 'Missing image data',
                'message': 'Please provide image as base64 encoded data'
            }), 400
        
        image_str = data.get('image', '')
        filename = data.get('filename', 'plant.jpg')
        
        # Handle data URI format
        if image_str.startswith('data:'):
            image_str = image_str.split(',')[1]
        
        # Decode base64
        import base64
        try:
            image_data = base64.b64decode(image_str)
        except Exception as e:
            logger.warning(f'Invalid base64 image data: {str(e)}')
            return jsonify({
                'success': False,
                'error': 'Invalid image data',
                'message': 'Image data is not valid base64'
            }), 400
        
        logger.info(f'Processing plant identification for base64 image')
        
        # Get PlantID service and identify plant
        plantid_service = get_plantid_service()
        result = plantid_service.identify_plant(image_data, filename)
        
        if result is None:
            logger.error('PlantID service returned no result')
            return jsonify({
                'success': False,
                'error': 'Identification failed',
                'message': 'Could not identify plant from image. Please try with a clearer photo.'
            }), 500
        
        logger.info(f'Plant identification successful: {result.get("name")}')
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error during plant identification: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@plant_bp.route('/common', methods=['GET'])
def get_common_plants():
    """Get list of common plants for reference"""
    common_plants = [
        {
            'id': 'snake',
            'name': 'Snake Plant',
            'scientific': 'Sansevieria trifasciata',
            'toxicity': 'toxic'
        },
        {
            'id': 'monstera',
            'name': 'Monstera',
            'scientific': 'Monstera deliciosa',
            'toxicity': 'toxic'
        },
        {
            'id': 'pothos',
            'name': 'Golden Pothos',
            'scientific': 'Epipremnum aureum',
            'toxicity': 'toxic'
        },
        {
            'id': 'spider',
            'name': 'Spider Plant',
            'scientific': 'Chlorophytum comosum',
            'toxicity': 'safe'
        },
        {
            'id': 'peace-lily',
            'name': 'Peace Lily',
            'scientific': 'Spathiphyllum',
            'toxicity': 'toxic'
        },
        {
            'id': 'zz',
            'name': 'ZZ Plant',
            'scientific': 'Zamioculcas zamiifolia',
            'toxicity': 'toxic'
        },
    ]
    
    return jsonify({
        'success': True,
        'data': common_plants
    }), 200


@plant_bp.route('/validate', methods=['POST'])
def validate_plant_name():
    """
    Validate if a given name is a real plant
    
    Expected request:
    {
        "plant_name": "Rose"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "valid": true,
            "message": "Rose is recognized as a valid plant",
            "suggestions": ["Rosa canina", "Rosa damascena"]
        }
    }
    """
    try:
        data = request.get_json()
        plant_name = data.get('plant_name', '').strip()
        
        if not plant_name:
            return jsonify({
                'success': False,
                'error': 'Plant name is required',
                'data': {'valid': False}
            }), 400
        
        # Common plant validation list (expanded)
        common_plants_list = [
            # Flowers
            'rose', 'tulip', 'lily', 'daisy', 'sunflower', 'dahlia', 'iris',
            'lavender', 'peony', 'chrysanthemum', 'carnation', 'gerbera',
            'orchid', 'hibiscus', 'bougainvillea', 'marigold', 'pansy',
            'violet', 'petunia', 'zinnia', 'snapdragon', 'gladiolus',
            'hydrangea', 'magnolia', 'azalea', 'camellia', 'bluebell',
            
            # Herbs
            'basil', 'mint', 'rosemary', 'thyme', 'oregano', 'parsley',
            'cilantro', 'sage', 'dill', 'chives', 'tarragon', 'marjoram',
            'lavender', 'chamomile', 'peppermint', 'spearmint', 'lemon balm',
            'tulsi', 'ginger', 'turmeric', 'garlic',
            
            # Vegetables
            'tomato', 'lettuce', 'spinach', 'carrot', 'broccoli', 'cauliflower',
            'cabbage', 'cucumber', 'zucchini', 'pepper', 'pumpkin', 'squash',
            'bean', 'pea', 'corn', 'onion', 'garlic', 'leek', 'celery',
            'radish', 'turnip', 'beet', 'potato', 'eggplant',
            
            # Houseplants
            'monstera', 'pothos', 'snake plant', 'peace lily', 'spider plant',
            'philodendron', 'ficus', 'rubber plant', 'dracaena', 'yucca',
            'aglaonema', 'calathea', 'maranta', 'alocasia', 'anthurium',
            'areca palm', 'bird of paradise', 'christmas cactus', 'jade plant',
            'aloe vera', 'succulent', 'echeveria', 'sedum', 'haworthia',
            
            # Trees
            'oak', 'maple', 'birch', 'pine', 'cedar', 'spruce', 'fir',
            'elm', 'ash', 'willow', 'poplar', 'beech', 'oak', 'chestnut',
            'hawthorn', 'rowan', 'linden', 'sycamore', 'cherry', 'apple',
            'pear', 'plum', 'peach', 'almond', 'walnut', 'ash', 'holly',
            
            # Fruits
            'apple', 'banana', 'orange', 'lemon', 'lime', 'grapefruit',
            'strawberry', 'blueberry', 'raspberry', 'blackberry', 'grape',
            'watermelon', 'peach', 'pineapple', 'mango', 'papaya', 'kiwi',
            'coconut', 'avocado', 'pomegranate', 'fig', 'date', 'olive',
            
            # Medicinal/Special
            'aloe', 'neem', 'moringa', 'ashwagandha', 'brahmi', 'tulsi',
            'mint', 'ginger', 'turmeric', 'curcuma', 'cinnamon', 'clove',
            'cardamom', 'fennel', 'fenugreek', 'mustard',
        ]
        
        # Non-plant keywords to filter out
        non_plant_keywords = [
            'animal', 'cat', 'dog', 'bird', 'fish', 'insect', 'spider',
            'car', 'house', 'rock', 'stone', 'water', 'plastic', 'metal',
            'paper', 'wood', 'glass', 'toy', 'phone', 'computer', 'book'
        ]
        
        plant_name_lower = plant_name.lower()
        
        # Check against non-plant keywords
        for keyword in non_plant_keywords:
            if keyword in plant_name_lower:
                return jsonify({
                    'success': True,
                    'data': {
                        'valid': False,
                        'message': f'"{plant_name}" does not appear to be a plant name.',
                        'suggestions': []
                    }
                }), 200
        
        # Check against common plants list
        for common_plant in common_plants_list:
            if common_plant in plant_name_lower or plant_name_lower in common_plant:
                return jsonify({
                    'success': True,
                    'data': {
                        'valid': True,
                        'message': f'"{plant_name}" is recognized as a valid plant.',
                        'suggestions': []
                    }
                }), 200
        
        # If name is very short or contains only symbols, reject it
        if len(plant_name) < 2 or not any(c.isalpha() for c in plant_name):
            return jsonify({
                'success': True,
                'data': {
                    'valid': False,
                    'message': f'"{plant_name}" does not appear to be a valid plant name.',
                    'suggestions': []
                }
            }), 200
        
        # Fallback heuristic: If name contains letters and is reasonable length, consider it potentially valid
        has_letters = any(c.isalpha() for c in plant_name)
        reasonable_length = 2 <= len(plant_name) <= 50
        
        if has_letters and reasonable_length:
            return jsonify({
                'success': True,
                'data': {
                    'valid': True,
                    'message': f'"{plant_name}" appears to be a valid plant name.',
                    'suggestions': []
                }
            }), 200
        else:
            return jsonify({
                'success': True,
                'data': {
                    'valid': False,
                    'message': f'"{plant_name}" does not appear to be a valid plant name.',
                    'suggestions': []
                }
            }), 200
    
    except Exception as e:
        logger.error(f"Plant validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'message': str(e)
        }), 500

