"""
Plant history routes for storing and retrieving plant identification history
"""

from flask import Blueprint, request, jsonify
from models import db, PlantIdentification, User
from datetime import datetime, timezone
import logging
import json
import base64

logger = logging.getLogger(__name__)

plant_history_bp = Blueprint('plant_history', __name__)


@plant_history_bp.route('/history/save', methods=['POST'])
def save_plant_identification():
    """
    Save a plant identification to history
    Expected JSON:
    {
        "user_id": 1,
        "plant_name": "Tomato Plant",
        "scientific_name": "Solanum lycopersicum",
        "confidence": 95.5,
        "image_base64": "...",  # Base64 encoded image
        "image_filename": "tomato.jpg",
        "plant_info": "{...}"  # JSON string with plant details
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        plant_name = data.get('plant_name', '').strip()
        scientific_name = data.get('scientific_name', '').strip()
        confidence = data.get('confidence')
        image_base64 = data.get('image_base64')
        image_filename = data.get('image_filename', '').strip()
        plant_info = data.get('plant_info')
        
        # Validate required fields
        if not user_id or not plant_name:
            return jsonify({
                'success': False,
                'message': 'User ID and plant name are required'
            }), 400
        
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Convert base64 image to binary
        image_data = None
        if image_base64:
            try:
                # Remove data prefix if present
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]
                image_data = base64.b64decode(image_base64)
            except Exception as e:
                logger.warning(f'Could not decode image: {str(e)}')
        
        # Create new plant identification record
        plant_id = PlantIdentification(
            user_id=user_id,
            plant_name=plant_name,
            scientific_name=scientific_name,
            confidence=confidence,
            image_data=image_data,
            image_filename=image_filename,
            plant_info=plant_info
        )
        
        try:
            db.session.add(plant_id)
            db.session.commit()
            
            logger.info(f'Plant identification saved for user {user_id}: {plant_name}')
            
            return jsonify({
                'success': True,
                'message': 'Plant identification saved',
                'plant_id': plant_id.id,
                'data': plant_id.to_dict()
            }), 201
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error saving plant identification: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Error saving plant identification'
            }), 500
    
    except Exception as e:
        logger.error(f'Error in save_plant_identification: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@plant_history_bp.route('/history/user/<int:user_id>', methods=['GET'])
def get_user_plant_history(user_id: int):
    """
    Get all plant identifications for a user
    Optional query params:
    - limit: Number of records to return (default: 100)
    - offset: Offset for pagination (default: 0)
    """
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get pagination params
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate pagination
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10
        
        # Get plant identifications ordered by most recent first
        identifications = PlantIdentification.query.filter_by(user_id=user_id)\
            .order_by(PlantIdentification.identified_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # Get total count
        total_count = PlantIdentification.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'data': [plant.to_dict() for plant in identifications]
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching plant history for user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error fetching history'
        }), 500


@plant_history_bp.route('/history/recent/<int:user_id>', methods=['GET'])
def get_recent_plant_history(user_id: int):
    """
    Get recent plant identifications for a user (default 4)
    Optional query param:
    - count: Number of recent plants to return (default: 4, max: 20)
    """
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get count param
        count = request.args.get('count', 4, type=int)
        
        # Validate count
        if count > 20:
            count = 20
        if count < 1:
            count = 4
        
        # Get recent plant identifications
        identifications = PlantIdentification.query.filter_by(user_id=user_id)\
            .order_by(PlantIdentification.identified_at.desc())\
            .limit(count)\
            .all()
        
        # Get total count
        total_count = PlantIdentification.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'recent_count': len(identifications),
            'total': total_count,
            'data': [plant.to_dict() for plant in identifications]
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching recent plant history for user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error fetching history'
        }), 500


@plant_history_bp.route('/history/<int:plant_id>', methods=['GET'])
def get_plant_identification(plant_id: int):
    """
    Get specific plant identification details
    """
    try:
        plant = PlantIdentification.query.get(plant_id)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant identification not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': plant.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching plant identification {plant_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@plant_history_bp.route('/history/<int:plant_id>', methods=['DELETE'])
def delete_plant_identification(plant_id: int):
    """
    Delete a plant identification from history
    """
    try:
        plant = PlantIdentification.query.get(plant_id)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant identification not found'
            }), 404
        
        db.session.delete(plant)
        db.session.commit()
        
        logger.info(f'Plant identification deleted: {plant_id}')
        
        return jsonify({
            'success': True,
            'message': 'Plant identification deleted'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting plant identification {plant_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@plant_history_bp.route('/plants/history/health', methods=['GET'])
def plant_history_health():
    """Health check for plant history service"""
    return jsonify({
        'status': 'Plant history service running'
    }), 200
