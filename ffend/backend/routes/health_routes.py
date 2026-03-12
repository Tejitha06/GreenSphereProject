"""
Health check routes
"""

from flask import Blueprint, jsonify
from datetime import datetime, timezone

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'GreenSphere API',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0'
    }), 200


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with service status"""
    return jsonify({
        'status': 'healthy',
        'service': 'GreenSphere API',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'services': {
            'api': 'operational',
            'plant_identification': 'operational',
            'disease_detection': 'operational'
        }
    }), 200
