"""
Routes package initialization
"""

from .health_routes import health_bp
from .plant_routes import plant_bp
from .disease_routes import disease_bp
from .n8n_routes import n8n_bp

__all__ = ['health_bp', 'plant_bp', 'disease_bp', 'n8n_bp']
