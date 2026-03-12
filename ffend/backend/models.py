"""
Database models for GreenSphere using SQLAlchemy
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import bcrypt
import jwt
import os
from typing import Optional, Dict, Any

db = SQLAlchemy()


class User(db.Model):
    """User model for storing user account information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Optional for OTP-based auth
    is_verified = db.Column(db.Boolean, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        if password:
            self.password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def generate_token(self, expires_in: int = 3600) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'exp': datetime.now(timezone.utc).timestamp() + expires_in
        }
        return jwt.encode(
            payload,
            os.getenv('SECRET_KEY', 'dev-secret-key'),
            algorithm='HS256'
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self) -> str:
        return f'<User {self.email}>'


class PlantIdentification(db.Model):
    """Plant identification history model for storing user's plant identification searches"""
    __tablename__ = 'plant_identifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    plant_name = db.Column(db.String(255), nullable=False)
    scientific_name = db.Column(db.String(255), nullable=True)
    confidence = db.Column(db.Float, nullable=True)  # Confidence percentage
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store image as binary
    image_filename = db.Column(db.String(255), nullable=True)
    plant_info = db.Column(db.Text, nullable=True)  # JSON string with plant details
    identified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('plant_identifications', lazy=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plant identification to dictionary"""
        import base64
        
        # Convert binary image data to base64 if available
        image_base64 = None
        if self.image_data:
            try:
                image_base64 = base64.b64encode(self.image_data).decode('utf-8')
            except Exception:
                pass
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plant_name': self.plant_name,
            'scientific_name': self.scientific_name,
            'confidence': self.confidence,
            'image_base64': image_base64,
            'image_filename': self.image_filename,
            'plant_info': self.plant_info,
            'identified_at': self.identified_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<PlantIdentification {self.plant_name}>'


class DiseaseIdentification(db.Model):
    """Disease identification history model for storing user's disease detection searches"""
    __tablename__ = 'disease_identifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    disease_name = db.Column(db.String(255), nullable=False)
    disease_type = db.Column(db.String(255), nullable=True)
    confidence = db.Column(db.Float, nullable=True)  # Confidence percentage
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store image as binary
    image_filename = db.Column(db.String(255), nullable=True)
    disease_info = db.Column(db.Text, nullable=True)  # JSON string with disease details
    identified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('disease_identifications', lazy=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert disease identification to dictionary"""
        import base64
        
        # Convert binary image data to base64 if available
        image_base64 = None
        if self.image_data:
            try:
                image_base64 = base64.b64encode(self.image_data).decode('utf-8')
            except Exception:
                pass
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'disease_name': self.disease_name,
            'disease_type': self.disease_type,
            'confidence': self.confidence,
            'image_base64': image_base64,
            'image_filename': self.image_filename,
            'disease_info': self.disease_info,
            'identified_at': self.identified_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<DiseaseIdentification {self.disease_name}>'


class GardenPlant(db.Model):
    """Model for plants added to user's garden"""
    __tablename__ = 'garden_plants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    plant_name = db.Column(db.String(120), nullable=False)
    scientific_name = db.Column(db.String(120))
    preferred_name = db.Column(db.String(120), nullable=True)  # User's custom display name
    age = db.Column(db.String(100), nullable=True)  # e.g., "1 year, 6 months, Just planted"
    watering_capacity = db.Column(db.String(500))  # e.g., "Water when soil is dry, 2-3 times per week"
    soil_type = db.Column(db.String(200))  # e.g., "Well-draining loamy soil"
    sunlight_requirements = db.Column(db.String(300))  # e.g., "6-8 hours of direct sunlight"
    temperature_range = db.Column(db.String(200))  # e.g., "18-25°C (65-77°F)"
    humidity_level = db.Column(db.String(200))  # e.g., "50-70% relative humidity"
    fertilizer_needs = db.Column(db.String(300))  # e.g., "Monthly during growing season"
    image_data = db.Column(db.LargeBinary)  # Binary image data (BLOB)
    image_filename = db.Column(db.String(255))  # Original filename
    plant_info = db.Column(db.Text)  # JSON text with additional plant information
    added_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('garden_plants', lazy='dynamic', cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert plant to dictionary for JSON response"""
        import base64
        
        # Convert image data to base64 if exists
        image_base64 = None
        if self.image_data:
            try:
                image_base64 = base64.b64encode(self.image_data).decode('utf-8')
            except Exception as e:
                print(f'Error encoding image: {e}')
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plant_name': self.plant_name,
            'scientific_name': self.scientific_name,
            'preferred_name': self.preferred_name,
            'age': self.age,
            'watering_capacity': self.watering_capacity,
            'soil_type': self.soil_type,
            'sunlight_requirements': self.sunlight_requirements,
            'temperature_range': self.temperature_range,
            'humidity_level': self.humidity_level,
            'fertilizer_needs': self.fertilizer_needs,
            'plant_info': self.plant_info,
            'image_base64': image_base64,
            'image_filename': self.image_filename,
            'added_at': self.added_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<GardenPlant {self.plant_name}>'


class NurseryOrder(db.Model):
    """Model for storing nursery orders placed by users"""
    __tablename__ = 'nursery_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    order_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # ORD-2026-xxxxx
    nursery_name = db.Column(db.String(255), nullable=False)
    nursery_area = db.Column(db.String(255), nullable=True)
    nursery_city = db.Column(db.String(100), nullable=True)
    nursery_state = db.Column(db.String(100), nullable=True)
    nursery_distance = db.Column(db.String(50), nullable=True)
    total_plants = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(50), nullable=False, default='pending')  # pending, paid, failed
    order_status = db.Column(db.String(50), nullable=False, default='placed')  # placed, confirmed, delivered, cancelled
    delivery_address = db.Column(db.String(500), nullable=True)
    order_notes = db.Column(db.Text, nullable=True)
    ordered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('nursery_orders', lazy=True, cascade='all, delete-orphan'))
    order_items = db.relationship('OrderItem', backref=db.backref('nursery_order', lazy=True), cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'nursery_name': self.nursery_name,
            'nursery_area': self.nursery_area,
            'nursery_city': self.nursery_city,
            'nursery_state': self.nursery_state,
            'nursery_distance': self.nursery_distance,
            'total_plants': self.total_plants,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'order_status': self.order_status,
            'delivery_address': self.delivery_address,
            'order_notes': self.order_notes,
            'items': [item.to_dict() for item in self.order_items],
            'ordered_at': self.ordered_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f'<NurseryOrder {self.order_id}>'


class OrderItem(db.Model):
    """Model for storing individual items in a nursery order"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('nursery_orders.id'), nullable=False, index=True)
    plant_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'plant_name': self.plant_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }
    
    def __repr__(self) -> str:
        return f'<OrderItem {self.plant_name}>'


class PlantProgress(db.Model):
    """Model for tracking plant health progress and measurements over time"""
    __tablename__ = 'plant_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    garden_plant_id = db.Column(db.Integer, db.ForeignKey('garden_plants.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Species verification (Plant.id)
    species_name = db.Column(db.String(255), nullable=True)  # Identified species name
    species_scientific = db.Column(db.String(255), nullable=True)  # Scientific name
    species_confidence = db.Column(db.Float, nullable=True)  # Plant.id confidence score
    species_verified = db.Column(db.Boolean, default=True)  # True if matches expected plant
    species_mismatch_reason = db.Column(db.String(500), nullable=True)  # Reason if verification failed
    
    # Health metrics
    health_score = db.Column(db.Float, nullable=True)  # 0-100
    health_status = db.Column(db.String(50), nullable=True)  # excellent, good, fair, poor, critical
    green_percentage = db.Column(db.Float, nullable=True)  # Percentage of green in image
    yellowing_percentage = db.Column(db.Float, nullable=True)  # Percentage of yellowing
    vibrancy_score = db.Column(db.Float, nullable=True)
    
    # Size/Growth metrics (pixels)
    height_pixels = db.Column(db.Integer, nullable=True)
    width_pixels = db.Column(db.Integer, nullable=True)
    area_pixels = db.Column(db.Integer, nullable=True)
    
    # Size/Growth metrics (estimated real measurements)
    height_cm = db.Column(db.Float, nullable=True)  # Estimated height in cm
    width_cm = db.Column(db.Float, nullable=True)  # Estimated width in cm
    area_cm2 = db.Column(db.Float, nullable=True)  # Estimated area in cm²
    pixels_per_cm = db.Column(db.Float, nullable=True)  # Calibration factor used
    
    # Growth tracking
    height_change_pct = db.Column(db.Float, nullable=True)  # % change since last measurement
    area_change_pct = db.Column(db.Float, nullable=True)  # % change since last measurement
    days_since_last = db.Column(db.Integer, nullable=True)  # Days since last analysis
    growth_rate = db.Column(db.String(50), nullable=True)  # slow, normal, fast, rapid
    
    # Leaf metrics
    estimated_leaf_count = db.Column(db.Integer, nullable=True)
    leaf_tips_detected = db.Column(db.Integer, nullable=True)  # From PlantCV morphology
    foliage_coverage = db.Column(db.Float, nullable=True)  # Percentage
    leaf_density = db.Column(db.String(50), nullable=True)  # sparse, moderate, dense
    
    # Additional analysis
    analysis_data = db.Column(db.Text, nullable=True)  # JSON with full analysis
    ai_recommendations = db.Column(db.Text, nullable=True)  # AI-generated recommendations
    ai_issues_detected = db.Column(db.Text, nullable=True)  # JSON array of detected issues
    image_data = db.Column(db.LargeBinary, nullable=True)  # Analyzed image
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Metadata
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    notes = db.Column(db.Text, nullable=True)  # User notes or AI summary
    
    # Relationships
    garden_plant = db.relationship('GardenPlant', backref=db.backref('progress_history', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('plant_progress', lazy=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress record to dictionary for JSON response"""
        import base64
        import json as json_lib
        
        # Convert image data to base64 if exists
        image_base64 = None
        if self.image_data:
            try:
                image_base64 = base64.b64encode(self.image_data).decode('utf-8')
            except Exception as e:
                print(f'Error encoding image: {e}')
        
        # Parse AI issues if stored as JSON string
        ai_issues = None
        if self.ai_issues_detected:
            try:
                ai_issues = json_lib.loads(self.ai_issues_detected) if isinstance(self.ai_issues_detected, str) else self.ai_issues_detected
            except:
                ai_issues = self.ai_issues_detected
        
        return {
            'id': self.id,
            'garden_plant_id': self.garden_plant_id,
            'user_id': self.user_id,
            # Species verification
            'species': {
                'name': self.species_name,
                'scientific_name': self.species_scientific,
                'confidence': self.species_confidence,
                'verified': self.species_verified,
                'mismatch_reason': self.species_mismatch_reason
            },
            # Health
            'health_score': self.health_score,
            'health_status': self.health_status,
            'green_percentage': self.green_percentage,
            'yellowing_percentage': self.yellowing_percentage,
            'vibrancy_score': self.vibrancy_score,
            # Size
            'size': {
                'height_pixels': self.height_pixels,
                'width_pixels': self.width_pixels,
                'area_pixels': self.area_pixels,
                'height_cm': self.height_cm,
                'width_cm': self.width_cm,
                'area_cm2': self.area_cm2,
                'pixels_per_cm': self.pixels_per_cm
            },
            # Growth tracking
            'growth': {
                'height_change_pct': self.height_change_pct,
                'area_change_pct': self.area_change_pct,
                'days_since_last': self.days_since_last,
                'growth_rate': self.growth_rate
            },
            # Leaves
            'leaves': {
                'estimated_count': self.estimated_leaf_count,
                'tips_detected': self.leaf_tips_detected,
                'foliage_coverage': self.foliage_coverage,
                'density': self.leaf_density
            },
            # AI analysis
            'ai': {
                'recommendations': self.ai_recommendations,
                'issues_detected': ai_issues
            },
            'image_base64': image_base64,
            'image_filename': self.image_filename,
            'recorded_at': self.recorded_at.isoformat(),
            'notes': self.notes
        }
    
    def __repr__(self) -> str:
        return f'<PlantProgress plant_id={self.garden_plant_id} score={self.health_score}>'


class WateringReminder(db.Model):
    """Model for storing watering reminders linked to plants and Google Calendar"""
    __tablename__ = 'watering_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('garden_plants.id'), nullable=False, index=True)
    calendar_event_id = db.Column(db.String(255), nullable=True)  # Google Calendar event ID
    interval_days = db.Column(db.Integer, nullable=False, default=3)  # Watering interval in days
    
    # Weather at time of creation
    weather_temp = db.Column(db.Float, nullable=True)
    weather_humidity = db.Column(db.Float, nullable=True)
    weather_condition = db.Column(db.String(100), nullable=True)
    
    # Location for weather updates
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    user_timezone = db.Column(db.String(64), nullable=True, default='UTC')
    reminder_time = db.Column(db.String(16), nullable=True, default='07:00')
    
    # Status tracking
    reminder_enabled = db.Column(db.Boolean, default=True)
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', backref=db.backref('watering_reminders', lazy=True, cascade='all, delete-orphan'))
    plant = db.relationship('GardenPlant', backref=db.backref('watering_reminder', lazy=True, uselist=False, cascade='all, delete-orphan'))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reminder to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plant_id': self.plant_id,
            'calendar_event_id': self.calendar_event_id,
            'interval_days': self.interval_days,
            'weather': {
                'temp': self.weather_temp,
                'humidity': self.weather_humidity,
                'condition': self.weather_condition
            },
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'timezone': self.user_timezone
            },
            'reminder_time': self.reminder_time,
            'reminder_enabled': self.reminder_enabled,
            'last_reminder_sent': self.last_reminder_sent.isoformat() if self.last_reminder_sent else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f'<WateringReminder plant_id={self.plant_id} interval={self.interval_days}d>'
