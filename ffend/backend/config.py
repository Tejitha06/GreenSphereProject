import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Plant.id API Configuration with key rotation support
    PLANTID_API_KEYS = os.getenv('PLANTID_API_KEYS', '').split(',') if os.getenv('PLANTID_API_KEYS') else []
    PLANTID_API_KEY = os.getenv('PLANTID_API_KEY', '')  # legacy single key
    PLANTID_API_KEY_BACKUP = os.getenv('PLANTID_API_KEY_BACKUP', '')  # legacy backup
    PLANTID_API_URL = os.getenv('PLANTID_API_URL', 'https://api.plant.id/v3')
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
    
    # Gemini API Configuration with key rotation support
    GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '').split(',') if os.getenv('GEMINI_API_KEYS') else []
    
    # Optional: Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///greensphere.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
