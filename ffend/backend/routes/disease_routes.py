"""
Disease detection routes
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import logging
from datetime import datetime, timezone
from plantid_service import get_plantid_service

disease_bp = Blueprint('diseases', __name__)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@disease_bp.route('/detect', methods=['POST'])
def detect_disease():
    """
    Detect diseases in a plant from an uploaded image
    
    Expected request:
    - Content-Type: multipart/form-data
    - Files: 'image' (required) - Plant image file
    
    Returns:
    {
        "success": true,
        "data": {
            "isHealthy": false,
            "title": "Disease Name",
            "probability": 85.5,
            "description": "...",
            "severity": "High",
            "causes": ["Cause 1", "Cause 2"],
            "symptoms": ["Symptom 1", "Symptom 2"],
            "homeRemedies": ["Remedy 1", "Remedy 2"],
            "fertilizer": ["Fertilizer recommendation"],
            "pesticide": ["Pesticide recommendation"],
            "prevention": ["Prevention tip"]
        }
    }
    """
    try:
        # Check if image file is provided
        if 'image' not in request.files:
            logger.warning('Disease detection request without image file')
            return jsonify({
                'success': False,
                'error': 'Missing image file',
                'message': 'Please upload an image file with key "image"'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning('Disease detection request with empty filename')
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
        
        logger.info(f'Processing disease detection for file: {filename}')
        
        # Get PlantID service and detect disease
        plantid_service = get_plantid_service()
        result = plantid_service.detect_disease(image_data, filename)
        
        if result is None:
            logger.error('PlantID service returned no result')
            return jsonify({
                'success': False,
                'error': 'Detection failed',
                'message': 'Could not analyze plant from image. Please try with a clearer photo.'
            }), 500
        
        if not result.get('success'):
            logger.info(f'No diseases detected in image')
            return jsonify({
                'success': True,
                'data': {
                    'isHealthy': True,
                    'message': result.get('message', 'Plant appears healthy'),
                    'confidence': 100
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        logger.info(f'Disease detected: {result.get("title")}')
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error during disease detection: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@disease_bp.route('/detect/base64', methods=['POST'])
def detect_disease_base64():
    """
    Detect diseases in a plant from a base64-encoded image
    
    Expected request (JSON):
    {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJ...",
        "filename": "plant.jpg" (optional)
    }
    
    Returns: Same as /detect endpoint
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            logger.warning('Disease detection request without image data')
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
        
        logger.info(f'Processing disease detection for base64 image')
        
        # Get PlantID service and detect disease
        plantid_service = get_plantid_service()
        result = plantid_service.detect_disease(image_data, filename)
        
        if result is None:
            logger.error('PlantID service returned no result')
            return jsonify({
                'success': False,
                'error': 'Detection failed',
                'message': 'Could not analyze plant from image. Please try with a clearer photo.'
            }), 500
        
        if not result.get('success'):
            logger.info(f'No diseases detected in image')
            return jsonify({
                'success': True,
                'data': {
                    'isHealthy': True,
                    'message': result.get('message', 'Plant appears healthy'),
                    'confidence': 100
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 200
        
        logger.info(f'Disease detected: {result.get("title")}')
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f'Error during disease detection: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Server error',
            'message': str(e)
        }), 500


@disease_bp.route('/common', methods=['GET'])
def get_common_diseases():
    """Get list of common plant diseases for reference"""
    common_diseases = [
        {
            'id': 'rootRot',
            'title': 'Root Rot',
            'severity': 'High',
            'description': 'Fungal root decay'
        },
        {
            'id': 'powderyMildew',
            'title': 'Powdery Mildew',
            'severity': 'Moderate',
            'description': 'White dusty coating on leaves'
        },
        {
            'id': 'downyMildew',
            'title': 'Downy Mildew',
            'severity': 'Moderate',
            'description': 'Yellowish patches on leaf surfaces'
        },
        {
            'id': 'anthracnose',
            'title': 'Anthracnose',
            'severity': 'High',
            'description': 'Dark sunken lesions on leaves'
        },
        {
            'id': 'blackSpot',
            'title': 'Black Spot',
            'severity': 'Moderate',
            'description': 'Black circular spots on leaves'
        },
        {
            'id': 'rust',
            'title': 'Rust Disease',
            'severity': 'Moderate',
            'description': 'Orange-brown pustules on leaves'
        },
    ]
    
    return jsonify({
        'success': True,
        'data': common_diseases
    }), 200
