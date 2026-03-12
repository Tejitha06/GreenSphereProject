"""
Plant Growth Tracking API Routes
=================================
REST API endpoints for the unified plant growth tracking system.

Endpoints:
- POST /api/growth/analyze - Full plant analysis
- POST /api/growth/quick-check - Fast health check
- POST /api/growth/compare - Compare two analyses
- POST /api/growth/track/<plant_id> - Track plant over time
- GET /api/growth/history/<plant_id> - Get growth history
"""

from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app
import logging
import base64
from datetime import datetime, timezone
from functools import wraps
import traceback

# Import the unified tracker
try:
    from plant_growth_tracker import (
        PlantGrowthTracker,
        analyze_plant,
        quick_health_check,
        GrowthReport,
        to_python_type
    )
    TRACKER_AVAILABLE = True
except (ImportError, NameError) as e:
    TRACKER_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Fallback to_python_type if import fails
    import numpy as np
    def to_python_type(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: to_python_type(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [to_python_type(item) for item in obj]
        return obj
    
    # Fallback GrowthReport class if import fails
    class GrowthReport:
        def __init__(self):
            self.success = False
            self.timestamp = datetime.now(timezone.utc).isoformat()
            self.error = "Growth tracker not available"
            self.components_used = []
            self.warnings = []
            self.total_processing_time_ms = None

# Import models
try:
    from models import db, GardenPlant, PlantProgress
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)
growth_bp = Blueprint('growth', __name__)

# Global tracker instance (singleton for efficiency)
_tracker_instance = None


def get_tracker():
    """Get or create singleton tracker instance"""
    global _tracker_instance
    if _tracker_instance is None and TRACKER_AVAILABLE:
        logger.info("🌱 Initializing PlantGrowthTracker...")
        _tracker_instance = PlantGrowthTracker(
            enable_species_id=True,
            enable_ai_reports=True,
            rembg_model="u2net"
        )
    return _tracker_instance


def handle_errors(f):
    """Error handling decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API Error: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    return decorated


def require_tracker(f):
    """Ensure tracker is available"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not TRACKER_AVAILABLE:
            return jsonify({
                'success': False,
                'error': f'Plant growth tracker not available: {IMPORT_ERROR}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 503
        return f(*args, **kwargs)
    return decorated


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@growth_bp.route('/growth/analyze', methods=['POST'])
@handle_errors
@require_tracker
def analyze_growth():
    """
    Full plant growth analysis.
    
    Request:
        Content-Type: multipart/form-data or application/json
        
        multipart/form-data:
            - image: Image file
            - plant_name: Optional plant name
            - pixels_per_cm: Optional scale factor
            - skip_species: Skip species identification (default: false)
            - skip_ai: Skip AI report (default: false)
        
        application/json:
            - image_base64: Base64 encoded image
            - plant_name: Optional
            - pixels_per_cm: Optional
            - skip_species: Optional
            - skip_ai: Optional
    
    Response:
        {
            "success": true,
            "data": {
                "timestamp": "ISO timestamp",
                "health_score": 85.5,
                "greenness_index": 0.72,
                "leaf_count": 12,
                "measurements": {...},
                "species": {...},
                "ai_summary": "...",
                "ai_recommendations": [...],
                "processing_time_ms": 1234
            }
        }
    """
    tracker = get_tracker()

    # Require plant_id to identify the garden plant
    plant_id = None
    image_data = None
    plant_name = None
    pixels_per_cm = None
    skip_species = False
    skip_ai = False

    if request.is_json:
        data = request.get_json()
        image_base64 = data.get('image_base64', '')
        if image_base64.startswith('data:'):
            image_base64 = image_base64.split(',')[1]
        image_data = image_base64
        plant_id = data.get('plant_id')
        plant_name = data.get('plant_name')
        pixels_per_cm = data.get('pixels_per_cm')
        skip_species = data.get('skip_species', False)
        skip_ai = data.get('skip_ai', False)
    elif request.files.get('image'):
        file = request.files['image']
        image_data = file.read()
        plant_id = request.form.get('plant_id')
        plant_name = request.form.get('plant_name')
        pixels_per_cm = request.form.get('pixels_per_cm')
        skip_species = request.form.get('skip_species', 'false').lower() == 'true'
        skip_ai = request.form.get('skip_ai', 'false').lower() == 'true'
        if pixels_per_cm:
            try:
                pixels_per_cm = float(pixels_per_cm)
            except ValueError:
                pixels_per_cm = None
    else:
        return jsonify({
            'success': False,
            'error': 'No image provided. Send as multipart/form-data with "image" field or JSON with "image_base64"'
        }), 400

    # Require plant_id and fetch garden plant
    if not plant_id:
        return jsonify({'success': False, 'error': 'plant_id is required for growth analysis.'}), 400
    plant = GardenPlant.query.get(plant_id) if MODELS_AVAILABLE else None
    if not plant:
        return jsonify({'success': False, 'error': f'Plant with ID {plant_id} not found.'}), 404

    # Use scientific name for verification: prefer value sent from frontend, fallback to DB
    expected_scientific = request.form.get('scientific_name') or (plant.scientific_name if plant else None)
    plant_display_name = plant.preferred_name or plant.plant_name

    # Update tracker scale if provided
    if pixels_per_cm:
        tracker._analyzer.pixels_per_cm = pixels_per_cm

    # Identify plant species from image before analysis
    species_result = None
    identified_scientific = None
    confidence = None
    if tracker._enable_species and tracker._species_client:
        img = tracker._load_image(image_data)
        if img is not None:
            species_result = tracker._species_client.identify(img)
            if species_result and species_result.success:
                identified_scientific = species_result.scientific_name.lower().strip() if species_result.scientific_name else None
                confidence = species_result.confidence
    # Compare scientific names before analysis
    if expected_scientific and identified_scientific:
        if expected_scientific.lower().strip() != identified_scientific:
            warning_msg = (
                f"Warning: Scientific name mismatch!\n"
                f"Expected: {expected_scientific or 'Unknown'}\n"
                f"Identified: {identified_scientific or 'Unknown'}\n"
                f"Confidence: {confidence if confidence is not None else 'N/A'}\n"
                f"Analysis aborted. Please upload a photo of your correct plant."
            )
            return jsonify({
                'success': False,
                'error': 'Scientific name mismatch. Please upload a photo of the correct plant.',
                'warning': warning_msg,
                'species_mismatch': True,
                'expected_species': expected_scientific,
                'identified_species': identified_scientific,
                'confidence': confidence
            }), 400

    # Run analysis only if scientific names match or not available
    report = tracker.analyze(
        image=image_data,
        plant_name=plant_display_name,
        expected_species=expected_scientific,
        skip_species=skip_species,
        skip_ai=skip_ai
    )

    response_data = _format_report(report)
    return jsonify({
        'success': report.success,
        'data': response_data,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@growth_bp.route('/growth/quick-check', methods=['POST'])
@handle_errors
@require_tracker
def quick_check():
    """
    Fast health check - no API calls, quick measurements only.
    
    Request:
        Same as /growth/analyze
    
    Response:
        {
            "success": true,
            "data": {
                "health_score": 85.5,
                "greenness_index": 0.72,
                "leaf_count": 12,
                "processing_time_ms": 234
            }
        }
    """
    # Get image
    image_data = None
    
    if request.is_json:
        data = request.get_json()
        image_base64 = data.get('image_base64', '')
        if image_base64.startswith('data:'):
            image_base64 = image_base64.split(',')[1]
        image_data = image_base64
    elif request.files.get('image'):
        image_data = request.files['image'].read()
    else:
        return jsonify({
            'success': False,
            'error': 'No image provided'
        }), 400
    
    # Quick check
    result = quick_health_check(image_data)
    
    return jsonify({
        'success': result.get('success', False),
        'data': result,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@growth_bp.route('/growth/compare', methods=['POST'])
@handle_errors
@require_tracker
def compare_growth():
    """
    Compare two plant images for growth tracking.
    
    Request (JSON):
        {
            "current_image": "base64...",
            "previous_image": "base64...",
            "plant_name": "optional"
        }
    
    Response:
        {
            "success": true,
            "data": {
                "current": {...},
                "previous": {...},
                "growth_delta": {
                    "area_change_pct": 15.2,
                    "height_change_pct": 8.5,
                    "health_change": 5.0
                }
            }
        }
    """
    tracker = get_tracker()
    data = request.get_json()
    
    current_image = data.get('current_image', '')
    previous_image = data.get('previous_image', '')
    plant_name = data.get('plant_name')
    
    if not current_image or not previous_image:
        return jsonify({
            'success': False,
            'error': 'Both current_image and previous_image are required'
        }), 400
    
    # Handle data URI prefix
    if current_image.startswith('data:'):
        current_image = current_image.split(',')[1]
    if previous_image.startswith('data:'):
        previous_image = previous_image.split(',')[1]
    
    # Analyze previous first (without AI to save time)
    previous_report = tracker.analyze(
        image=previous_image,
        plant_name=plant_name,
        skip_species=True,
        skip_ai=True
    )
    
    # Analyze current with comparison
    current_report = tracker.analyze(
        image=current_image,
        previous_report=previous_report,
        plant_name=plant_name,
        skip_species=False,
        skip_ai=False
    )
    
    return jsonify({
        'success': current_report.success,
        'data': {
            'current': _format_report(current_report),
            'previous': _format_report(previous_report),
            'growth_delta': current_report.growth_delta
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ============================================================================
# TRACKING ENDPOINTS (with database)
# ============================================================================

@growth_bp.route('/growth/track/<int:plant_id>', methods=['POST'])
@handle_errors
@require_tracker
def track_plant(plant_id: int):
    """
    Track plant growth over time - saves to database.
    
    Request:
        multipart/form-data or JSON with image
    
    Response:
        {
            "success": true,
            "data": {
                "analysis": {...},
                "growth_since_last": {...},
                "tracking_started": "ISO date",
                "measurements_count": 5
            }
        }
    """
    if not MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database models not available'
        }), 503
    
    tracker = get_tracker()
    
    # Get plant from database
    plant = GardenPlant.query.get(plant_id)
    if not plant:
        return jsonify({
            'success': False,
            'error': f'Plant with ID {plant_id} not found'
        }), 404
    
    # Get image
    image_data = None
    user_local_timestamp = None
    if request.is_json:
        data = request.get_json()
        image_base64 = data.get('image_base64', '')
        if image_base64.startswith('data:'):
            image_base64 = image_base64.split(',')[1]
        image_data = image_base64
        user_local_timestamp = data.get('user_local_timestamp')
    elif request.files.get('image'):
        image_data = request.files['image'].read()
        user_local_timestamp = request.form.get('user_local_timestamp')
    else:
        return jsonify({
            'success': False,
            'error': 'No image provided'
        }), 400
    
    # Get previous analysis for comparison
    previous_report = None
    previous_progress = PlantProgress.query.filter_by(
        garden_plant_id=plant_id
    ).order_by(PlantProgress.recorded_at.desc()).first()
    
    if previous_progress and previous_progress.analysis_data:
        # Reconstruct minimal previous report for comparison
        try:
            import json
            prev_data = json.loads(previous_progress.analysis_data)
            from plant_growth_tracker import MeasurementResult, GrowthReport
            
            prev_measurements = MeasurementResult(
                success=True,
                height_px=prev_data.get('measurements', {}).get('height_px', 0),
                width_px=prev_data.get('measurements', {}).get('width_px', 0),
                area_px=prev_data.get('measurements', {}).get('area_px', 0),
                health_score=prev_data.get('health_score', 50)
            )
            
            previous_report = GrowthReport(
                success=True,
                timestamp=previous_progress.recorded_at.isoformat() if previous_progress.recorded_at else '',
                measurements=prev_measurements
            )
        except Exception as e:
            logger.warning(f"Could not reconstruct previous report: {e}")
    
    # Fetch growth history for AI trend analysis (last 10 records)
    history_records = PlantProgress.query.filter_by(
        garden_plant_id=plant_id
    ).order_by(PlantProgress.recorded_at.desc()).limit(10).all()
    
    growth_history = []
    for rec in history_records:
        growth_history.append({
            'recorded_at': rec.recorded_at.isoformat() if rec.recorded_at else None,
            'height_px': rec.height_pixels,
            'width_px': rec.width_pixels,
            'area_px': rec.area_pixels,
            'height_cm': rec.height_cm,
            'width_cm': rec.width_cm,
            'area_cm2': rec.area_cm2,
            'health_score': rec.health_score,
            'health_status': rec.health_status,
            'green_percentage': rec.green_percentage,
            'leaf_count': rec.estimated_leaf_count,
            'species_verified': rec.species_verified,
            'notes': rec.notes
        })
    
    # Get expected species - use scientific name for verification
    plant_display_name = plant.preferred_name or plant.plant_name
    expected_scientific = plant.scientific_name  # Use scientific name for matching
    
    # Run analysis with history and species verification
    report = tracker.analyze(
        image=image_data,
        previous_report=previous_report,
        plant_name=plant_display_name,
        growth_history=growth_history,
        expected_species=expected_scientific,  # Pass scientific name for verification
        estimate_real_size=True
    )
    
    if not report.success:
        # Check if it's a species mismatch error
        if not report.species_verified and report.species_mismatch_reason:
            return jsonify({
                'success': False,
                'error': report.error or 'Wrong plant detected',
                'species_mismatch': True,
                'species_mismatch_reason': report.species_mismatch_reason,
                'detected_species': report.species.name if report.species else None,
                'detected_confidence': report.species.confidence if report.species else None,
                'expected_species': expected_scientific,
                'action_required': f'Please take a photo of your {plant_display_name} for progress tracking.',
                'warnings': report.warnings
            }), 400
        
        # Other errors
        return jsonify({
            'success': False,
            'error': report.error or 'Analysis failed'
        }), 500
    
    # Save to database
    import json
    analysis_dict = _format_report(report)
    
    progress = PlantProgress(
        garden_plant_id=plant_id,
        user_id=plant.user_id,
        health_score=report.measurements.health_score if report.measurements else None,
        health_status=_get_health_status(report.measurements.health_score) if report.measurements else None,
        green_percentage=report.measurements.greenness_index * 100 if report.measurements else None,
        height_pixels=int(report.measurements.height_px) if report.measurements else None,
        width_pixels=int(report.measurements.width_px) if report.measurements else None,
        area_pixels=int(report.measurements.area_px) if report.measurements else None,
        height_cm=report.measurements.height_cm if report.measurements else None,
        width_cm=report.measurements.width_cm if report.measurements else None,
        area_cm2=report.measurements.area_cm2 if report.measurements else None,
        estimated_leaf_count=report.measurements.leaf_count_estimate if report.measurements else None,
        # Species verification fields
        species_name=report.species.name if report.species else None,
        species_scientific=report.species.scientific_name if report.species else None,
        species_confidence=report.species.confidence if report.species else None,
        species_verified=report.species_verified,
        species_mismatch_reason=report.species_mismatch_reason,
        # AI fields
        ai_recommendations=json.dumps(report.ai_recommendations) if report.ai_recommendations else None,
        ai_issues_detected=json.dumps(report.ai_issues_detected) if report.ai_issues_detected else None,
        analysis_data=json.dumps(analysis_dict),
        notes=report.ai_summary,
        # Set recorded_at to user's local timestamp if provided, else analysis timestamp
        recorded_at=(datetime.fromisoformat(user_local_timestamp) if user_local_timestamp else datetime.fromisoformat(report.timestamp) if report.timestamp else datetime.now(timezone.utc))
    )
    
    # Store image - convert base64 to bytes if needed
    if isinstance(image_data, bytes):
        progress.image_data = image_data
    elif isinstance(image_data, str) and image_data:
        # Convert base64 string to bytes
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:'):
                image_data = image_data.split(',')[1]
            progress.image_data = base64.b64decode(image_data)
        except Exception as e:
            logger.warning(f"Could not decode base64 image: {e}")
    
    db.session.add(progress)
    
    # Update plant's last analysis date
    plant.last_analyzed = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # Get total measurement count
    measurement_count = PlantProgress.query.filter_by(garden_plant_id=plant_id).count()
    
    return jsonify({
        'success': True,
        'data': {
            'analysis': analysis_dict,
            'growth_since_last': report.growth_delta,
            'tracking_started': plant.added_at.isoformat() if plant.added_at else None,
            'measurements_count': measurement_count,
            'progress_id': progress.id,
            'garden_plant_id': plant_id,  # Use this for history lookup
            'species_verified': report.species_verified,
            'history_based_analysis': report.history_record_count > 0,
            'trend_analysis': report.ai_trend_analysis if report.ai_trend_analysis else None
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@growth_bp.route('/growth/history/<int:plant_id>', methods=['GET'])
@handle_errors
def get_growth_history(plant_id: int):
    """
    Get growth history for a plant.
    
    Query params:
        - limit: Max records (default 20)
        - offset: Pagination offset
    
    Response:
        {
            "success": true,
            "data": {
                "plant_name": "...",
                "history": [
                    {
                        "timestamp": "...",
                        "health_score": 85,
                        "height_px": 450,
                        ...
                    }
                ],
                "growth_trend": {
                    "health_trend": "improving",
                    "size_trend": "growing",
                    "avg_growth_rate": 5.2
                }
            }
        }
    """
    if not MODELS_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Database models not available'
        }), 503
    
    # Get plant
    plant = GardenPlant.query.get(plant_id)
    if not plant:
        return jsonify({
            'success': False,
            'error': f'Plant with ID {plant_id} not found'
        }), 404
    
    # Get pagination params
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Get history
    progress_records = PlantProgress.query.filter_by(
        garden_plant_id=plant_id
    ).order_by(PlantProgress.recorded_at.desc()).offset(offset).limit(limit).all()
    
    # Format history
    history = []
    for record in progress_records:
        # Convert image to base64 thumbnail if available
        image_thumbnail = None
        if record.image_data:
            try:
                image_thumbnail = base64.b64encode(record.image_data).decode('utf-8')
            except Exception:
                pass
        
        history.append({
            'id': record.id,
            'timestamp': record.recorded_at.isoformat() if record.recorded_at else None,
            'health_score': record.health_score,
            'health_status': record.health_status,
            'height_px': record.height_pixels,
            'width_px': record.width_pixels,
            'area_px': record.area_pixels,
            'green_percentage': record.green_percentage,
            'leaf_count': record.estimated_leaf_count,
            'notes': record.notes,
            'image': image_thumbnail
        })
    
    # Calculate trends
    growth_trend = _calculate_growth_trend(progress_records)
    
    return jsonify({
        'success': True,
        'data': {
            'plant_id': plant_id,
            'plant_name': plant.preferred_name or plant.plant_name,
            'history': history,
            'growth_trend': growth_trend,
            'total_records': PlantProgress.query.filter_by(garden_plant_id=plant_id).count()
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@growth_bp.route('/growth/status', methods=['GET'])
@handle_errors
def system_status():
    """
    Get system status and component availability.
    
    Response:
        {
            "success": true,
            "components": {
                "tracker": true,
                "rembg": true,
                "plantcv": false,
                "plant_id_api": true,
                "gemini_api": true,
                "database": true
            }
        }
    """
    status = {
        'tracker': TRACKER_AVAILABLE,
        'database': MODELS_AVAILABLE
    }
    
    if TRACKER_AVAILABLE:
        tracker = get_tracker()
        status['rembg'] = tracker._segmenter.rembg_available
        status['plantcv'] = tracker._analyzer.plantcv_available
        status['plant_id_api'] = bool(tracker._species_client and tracker._species_client.api_key)
        status['gemini_api'] = bool(tracker._reporter and tracker._reporter.api_keys)
    
    return jsonify({
        'success': True,
        'components': status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@growth_bp.route('/growth/clear-cache', methods=['POST'])
@handle_errors
@require_tracker
def clear_cache():
    """Clear the tracker cache"""
    tracker = get_tracker()
    tracker.clear_cache()
    
    return jsonify({
        'success': True,
        'message': 'Cache cleared',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_report(report: GrowthReport) -> dict:
    """Format GrowthReport for API response (JSON serializable)"""
    result = {
        'timestamp': report.timestamp,
        'success': report.success,
        'processing_time_ms': float(report.total_processing_time_ms) if report.total_processing_time_ms else 0,
        'components_used': report.components_used,
        'warnings': report.warnings
    }
    
    if report.error:
        result['error'] = report.error
    
    # Segmentation info
    if report.segmentation:
        result['segmentation'] = {
            'success': report.segmentation.success,
            'method': report.segmentation.method,
            'confidence': float(report.segmentation.confidence),
            'processing_time_ms': float(report.segmentation.processing_time_ms)
        }
    
    # Measurements - convert all numpy types
    if report.measurements and report.measurements.success:
        m = report.measurements
        result['measurements'] = {
            'height_px': float(m.height_px),
            'width_px': float(m.width_px),
            'area_px': float(m.area_px),
            'perimeter_px': float(m.perimeter_px),
            'height_cm': float(m.height_cm) if m.height_cm else None,
            'width_cm': float(m.width_cm) if m.width_cm else None,
            'area_cm2': float(m.area_cm2) if m.area_cm2 else None,
            'leaf_count_estimate': int(m.leaf_count_estimate),
            'advanced_metrics': to_python_type(m.advanced_metrics)
        }
        result['health_score'] = float(m.health_score)
        result['greenness_index'] = float(m.greenness_index)
        result['color_histogram'] = to_python_type(m.color_histogram)
    
    # Species
    if report.species and report.species.success:
        s = report.species
        result['species'] = {
            'name': s.name,
            'scientific_name': s.scientific_name,
            'confidence': float(s.confidence),
            'common_names': s.common_names,
            'care_info': to_python_type(s.care_info),
            'description': s.description
        }
    
    # Species verification
    result['species_verified'] = report.species_verified
    if report.species_mismatch_reason:
        result['species_mismatch_reason'] = report.species_mismatch_reason
    
    # AI insights
    if report.ai_summary:
        result['ai_summary'] = report.ai_summary
        result['ai_recommendations'] = report.ai_recommendations
        result['ai_growth_forecast'] = report.ai_growth_forecast
        result['ai_issues_detected'] = report.ai_issues_detected
        if report.ai_trend_analysis:
            result['ai_trend_analysis'] = report.ai_trend_analysis
        if report.ai_shape_analysis:
            result['ai_shape_analysis'] = report.ai_shape_analysis
        if report.ai_metrics_interpretation:
            result['ai_metrics_interpretation'] = report.ai_metrics_interpretation
    
    # Species-specific growth parameters
    if report.species_parameters:
        result['species_parameters'] = report.species_parameters
    
    # History context
    result['history_record_count'] = report.history_record_count
    
    # Growth delta
    if report.growth_delta:
        result['growth_delta'] = to_python_type(report.growth_delta)
    
    return result


def _get_health_status(score: float) -> str:
    """Convert health score to status string"""
    if score is None:
        return 'unknown'
    if score >= 80:
        return 'excellent'
    if score >= 60:
        return 'good'
    if score >= 40:
        return 'fair'
    if score >= 20:
        return 'poor'
    return 'critical'


def _calculate_growth_trend(records: list) -> dict:
    """Calculate growth trends from history records"""
    if len(records) < 2:
        return {
            'health_trend': 'stable',
            'size_trend': 'stable',
            'avg_growth_rate': 0
        }
    
    # Get valid records with health scores
    valid = [r for r in records if r.health_score is not None]
    
    if len(valid) < 2:
        return {
            'health_trend': 'stable',
            'size_trend': 'stable',
            'avg_growth_rate': 0
        }
    
    # Compare first and last
    newest = valid[0]
    oldest = valid[-1]
    
    # Health trend
    if newest.health_score > oldest.health_score + 5:
        health_trend = 'improving'
    elif newest.health_score < oldest.health_score - 5:
        health_trend = 'declining'
    else:
        health_trend = 'stable'
    
    # Size trend
    size_trend = 'stable'
    if newest.area_pixels and oldest.area_pixels:
        growth = (newest.area_pixels - oldest.area_pixels) / oldest.area_pixels * 100
        if growth > 5:
            size_trend = 'growing'
        elif growth < -5:
            size_trend = 'shrinking'
    
    # Average growth rate
    avg_growth = 0
    if newest.area_pixels and oldest.area_pixels and len(valid) > 1:
        total_growth = (newest.area_pixels - oldest.area_pixels) / oldest.area_pixels * 100
        avg_growth = total_growth / (len(valid) - 1)
    
    return {
        'health_trend': health_trend,
        'size_trend': size_trend,
        'avg_growth_rate': round(avg_growth, 2),
        'measurements_analyzed': len(valid)
    }
