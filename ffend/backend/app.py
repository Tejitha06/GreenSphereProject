"""
GreenSphere Flask Backend
Plant identification and disease detection using PlantID v3 API
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from config import config
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Import blueprints
from routes.plant_routes import plant_bp
from routes.disease_routes import disease_bp
from routes.health_routes import health_bp
from routes.email_routes import email_bp, mail
from routes.chatbot_routes import chatbot_bp
from routes.auth_routes import auth_bp
from routes.plant_history_routes import plant_history_bp
from routes.disease_history_routes import disease_history_bp
from routes.garden_routes import garden_bp
from routes.n8n_routes import n8n_bp
from routes.nursery_orders_routes import nursery_orders_bp
from routes.growth_routes import growth_bp
from routes.reminder_routes import reminder_bp
from routes.lightmeter_routes import lightmeter_bp

# Import models
from models import db, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get parent directory (where HTML files are)
FRONTEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///greensphere.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@greensphere.com')
    
    # Initialize Flask-Mail
    mail.init_app(app)
    
    # Initialize CORS
    CORS(app, 
         origins=app.config['CORS_ALLOWED_ORIGINS'],
         supports_credentials=True,
         methods=['GET', 'POST', 'OPTIONS', 'PUT'],
         allow_headers=['Content-Type', 'Authorization'])
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info('Database tables created')
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(plant_bp, url_prefix='/api/plants')
    app.register_blueprint(plant_history_bp, url_prefix='/api/plants')
    app.register_blueprint(disease_bp, url_prefix='/api/diseases')
    app.register_blueprint(disease_history_bp, url_prefix='/api/diseases')
    app.register_blueprint(garden_bp, url_prefix='/api/garden')
    app.register_blueprint(email_bp, url_prefix='/api/email')
    app.register_blueprint(n8n_bp, url_prefix='/api/n8n')
    app.register_blueprint(nursery_orders_bp, url_prefix='/api/nursery/orders')
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(growth_bp, url_prefix='/api')
    app.register_blueprint(reminder_bp, url_prefix='/api/garden')
    app.register_blueprint(lightmeter_bp)  # Register LightMeter endpoints at root level
    
    # Serve frontend HTML files
    @app.route('/')
    def serve_index():
        return send_from_directory(FRONTEND_DIR, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        # Don't serve if it's an API route
        if filename.startswith('api/'):
            return jsonify({'error': 'Not found'}), 404
        
        try:
            # Check if file exists in FRONTEND_DIR
            file_path = os.path.join(FRONTEND_DIR, filename)
            if os.path.isfile(file_path):
                return send_from_directory(FRONTEND_DIR, filename)
            else:
                logger.warning(f'File not found: {filename}')
                return jsonify({'error': 'Not found'}), 404
        except Exception as e:
            logger.error(f'Error serving {filename}: {str(e)}')
            return jsonify({'error': 'Not found', 'details': str(e)}), 404
    
    logger.info(f'Flask app created with config: {config_name}')
    return app


def register_error_handlers(app):
    """Register error handlers for common HTTP errors"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Internal Server Error: {str(error)}')
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred. Please try again later.',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 403


if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
