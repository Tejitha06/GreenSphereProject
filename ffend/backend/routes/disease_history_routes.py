"""
Disease history routes for storing and retrieving disease identification history
"""

from flask import Blueprint, request, jsonify
from models import db, DiseaseIdentification, User
from datetime import datetime, timezone
import logging
import json
import base64

logger = logging.getLogger(__name__)

disease_history_bp = Blueprint('disease_history', __name__)


@disease_history_bp.route('/history/save', methods=['POST'])
def save_disease_identification():
    """
    Save a disease identification to history
    Expected JSON:
    {
        "user_id": 1,
        "disease_name": "Powdery Mildew",
        "disease_type": "Fungal",
        "confidence": 92.5,
        "image_base64": "...",  # Base64 encoded image
        "image_filename": "disease.jpg",
        "disease_info": "{...}"  # JSON string with disease details
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        disease_name = data.get('disease_name', '').strip()
        disease_type = data.get('disease_type', '').strip()
        confidence = data.get('confidence')
        image_base64 = data.get('image_base64')
        image_filename = data.get('image_filename', '').strip()
        disease_info = data.get('disease_info')
        
        # Validate required fields
        if not user_id or not disease_name:
            return jsonify({
                'success': False,
                'message': 'User ID and disease name are required'
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
        
        # Create new disease identification record
        disease_id = DiseaseIdentification(
            user_id=user_id,
            disease_name=disease_name,
            disease_type=disease_type,
            confidence=confidence,
            image_data=image_data,
            image_filename=image_filename,
            disease_info=disease_info
        )
        
        try:
            db.session.add(disease_id)
            db.session.commit()
            
            logger.info(f'Disease identification saved for user {user_id}: {disease_name}')
            
            return jsonify({
                'success': True,
                'message': 'Disease identification saved',
                'disease_id': disease_id.id,
                'data': disease_id.to_dict()
            }), 201
        
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error saving disease identification: {str(e)}')
            return jsonify({
                'success': False,
                'message': 'Error saving disease identification'
            }), 500
    
    except Exception as e:
        logger.error(f'Error in save_disease_identification: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@disease_history_bp.route('/history/user/<int:user_id>', methods=['GET'])
def get_user_disease_history(user_id: int):
    """
    Get all disease identifications for a user
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
        
        # Get disease identifications ordered by most recent first
        identifications = DiseaseIdentification.query.filter_by(user_id=user_id)\
            .order_by(DiseaseIdentification.identified_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        # Get total count
        total_count = DiseaseIdentification.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'data': [disease.to_dict() for disease in identifications]
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching disease history for user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error fetching history'
        }), 500


@disease_history_bp.route('/history/recent/<int:user_id>', methods=['GET'])
def get_recent_disease_history(user_id: int):
    """
    Get recent disease identifications for a user (default 4)
    Optional query param:
    - count: Number of recent diseases to return (default: 4, max: 20)
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
        
        # Get recent disease identifications
        identifications = DiseaseIdentification.query.filter_by(user_id=user_id)\
            .order_by(DiseaseIdentification.identified_at.desc())\
            .limit(count)\
            .all()
        
        # Get total count
        total_count = DiseaseIdentification.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'recent_count': len(identifications),
            'total': total_count,
            'data': [disease.to_dict() for disease in identifications]
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching recent disease history for user {user_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error fetching history'
        }), 500


@disease_history_bp.route('/history/<int:disease_id>', methods=['GET'])
def get_disease_identification(disease_id: int):
    """
    Get specific disease identification details
    """
    try:
        disease = DiseaseIdentification.query.get(disease_id)
        
        if not disease:
            return jsonify({
                'success': False,
                'message': 'Disease identification not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': disease.to_dict()
        }), 200
    
    except Exception as e:
        logger.error(f'Error fetching disease identification {disease_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@disease_history_bp.route('/history/<int:disease_id>', methods=['DELETE'])
def delete_disease_identification(disease_id: int):
    """
    Delete a disease identification from history
    """
    try:
        disease = DiseaseIdentification.query.get(disease_id)
        
        if not disease:
            return jsonify({
                'success': False,
                'message': 'Disease identification not found'
            }), 404
        
        db.session.delete(disease)
        db.session.commit()
        
        logger.info(f'Disease identification deleted: {disease_id}')
        
        return jsonify({
            'success': True,
            'message': 'Disease identification deleted'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting disease identification {disease_id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500


@disease_history_bp.route('/history/health', methods=['GET'])
def disease_history_health():
    """Health check for disease history service"""
    return jsonify({
        'status': 'Disease history service running'
    }), 200
