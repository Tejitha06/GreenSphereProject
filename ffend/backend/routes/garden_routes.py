"""
Routes for managing user garden plants
"""
from flask import Blueprint, request, jsonify
from models import db, GardenPlant, User, PlantProgress
import json
from datetime import datetime, timezone

garden_bp = Blueprint('garden', __name__)


@garden_bp.route('/garden/save', methods=['POST'])
def save_garden_plant():
    """
    Save a plant to user's garden
    Expected JSON:
    {
        "user_id": int,
        "plant_name": string,
        "scientific_name": string,
        "watering_capacity": string,
        "soil_type": string,
        "sunlight_requirements": string,
        "temperature_range": string,
        "humidity_level": string,
        "fertilizer_needs": string,
        "plant_info": string (JSON),
        "image_base64": string (optional - base64 encoded image),
        "image_filename": string (optional - filename)
    }
    """
    try:
        import base64
        
        data = request.get_json()
        
        # Validate required fields
        user_id = data.get('user_id')
        plant_name = data.get('plant_name')
        
        if not user_id or not plant_name:
            return jsonify({
                'success': False,
                'message': 'user_id and plant_name are required'
            }), 400
        
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Check if plant already in garden
        existing_plant = GardenPlant.query.filter_by(
            user_id=user_id,
            plant_name=plant_name
        ).first()
        
        if existing_plant:
            return jsonify({
                'success': False,
                'message': 'Plant already in your garden'
            }), 409
        
        # Convert base64 image to binary
        image_data = None
        if data.get('image_base64'):
            try:
                # Remove data URI prefix if present
                image_base64 = data.get('image_base64')
                if image_base64.startswith('data:'):
                    image_base64 = image_base64.split(',')[1]
                
                image_data = base64.b64decode(image_base64)
            except Exception as e:
                print(f'Error decoding image: {e}')
                image_data = None
        
        # Create new garden plant
        garden_plant = GardenPlant(
            user_id=user_id,
            plant_name=plant_name,
            scientific_name=data.get('scientific_name'),
            preferred_name=data.get('preferred_name'),
            age=data.get('age'),
            watering_capacity=data.get('watering_capacity'),
            soil_type=data.get('soil_type'),
            sunlight_requirements=data.get('sunlight_requirements'),
            temperature_range=data.get('temperature_range'),
            humidity_level=data.get('humidity_level'),
            fertilizer_needs=data.get('fertilizer_needs'),
            image_data=image_data,
            image_filename=data.get('image_filename'),
            plant_info=data.get('plant_info')
        )
        
        db.session.add(garden_plant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plant added to garden successfully',
            'data': garden_plant.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'Error saving garden plant: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error saving plant: {str(e)}'
        }), 500


@garden_bp.route('/garden/user/<int:user_id>', methods=['GET'])
def get_user_garden(user_id):
    """
    Get all plants in user's garden
    Supports pagination: ?limit=10&offset=0
    """
    try:
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get pagination parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Query garden plants
        query = GardenPlant.query.filter_by(user_id=user_id).order_by(
            GardenPlant.added_at.desc()
        )
        
        total_count = query.count()
        plants = query.limit(limit).offset(offset).all()
        
        return jsonify({
            'success': True,
            'data': [plant.to_dict() for plant in plants],
            'total': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        print(f'Error fetching garden plants: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error fetching garden: {str(e)}'
        }), 500


@garden_bp.route('/garden/recent/<int:user_id>', methods=['GET'])
def get_recent_garden_plants(user_id):
    """
    Get recent plants added to garden
    Supports count parameter: ?count=4
    """
    try:
        # Verify user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        count = request.args.get('count', 4, type=int)
        
        query = GardenPlant.query.filter_by(user_id=user_id).order_by(
            GardenPlant.added_at.desc()
        )
        
        total_count = query.count()
        plants = query.limit(count).all()
        
        return jsonify({
            'success': True,
            'data': [plant.to_dict() for plant in plants],
            'total': total_count
        }), 200
        
    except Exception as e:
        print(f'Error fetching recent garden plants: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error fetching recent plants: {str(e)}'
        }), 500


@garden_bp.route('/garden/<int:plant_id>', methods=['GET'])
def get_garden_plant(plant_id):
    """
    Get a specific garden plant details
    """
    try:
        plant = GardenPlant.query.get(plant_id)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': plant.to_dict()
        }), 200
        
    except Exception as e:
        print(f'Error fetching garden plant: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error fetching plant: {str(e)}'
        }), 500


@garden_bp.route('/garden/<int:plant_id>', methods=['DELETE'])
def delete_garden_plant(plant_id):
    """
    Remove a plant from user's garden
    """
    try:
        plant = GardenPlant.query.get(plant_id)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            }), 404
        
        db.session.delete(plant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plant removed from garden successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f'Error deleting garden plant: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error deleting plant: {str(e)}'
        }), 500


@garden_bp.route('/garden/<int:plant_id>', methods=['PUT'])
def update_garden_plant(plant_id):
    """
    Update a plant in user's garden
    """
    try:
        plant = GardenPlant.query.get(plant_id)
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided (but NOT scientific_name - it's immutable)
        if 'plant_name' in data:
            plant.plant_name = data['plant_name']
        if 'preferred_name' in data:
            plant.preferred_name = data['preferred_name']
        if 'age' in data:
            plant.age = data['age']
        if 'watering_capacity' in data:
            plant.watering_capacity = data['watering_capacity']
        if 'soil_type' in data:
            plant.soil_type = data['soil_type']
        if 'sunlight_requirements' in data:
            plant.sunlight_requirements = data['sunlight_requirements']
        if 'temperature_range' in data:
            plant.temperature_range = data['temperature_range']
        if 'humidity_level' in data:
            plant.humidity_level = data['humidity_level']
        if 'fertilizer_needs' in data:
            plant.fertilizer_needs = data['fertilizer_needs']
        if 'plant_info' in data:
            plant.plant_info = data['plant_info']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Plant updated successfully',
            'data': plant.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f'Error updating garden plant: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error updating plant: {str(e)}'
        }), 500


@garden_bp.route('/garden/health', methods=['GET'])
def garden_health():
    """Health check endpoint for garden API"""
    try:
        return jsonify({
            'success': True,
            'message': 'Garden API is healthy',
            'timestamp': db.func.now()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Health check failed: {str(e)}'
        }), 500



@garden_bp.route('/garden/<int:plant_id>/progress', methods=['GET'])
def get_plant_progress(plant_id):
    """
    Get health progress history for a plant
    Supports pagination: ?limit=10&offset=0
    """
    try:
        plant = GardenPlant.query.get(plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            }), 404
        
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Query progress records
        query = PlantProgress.query.filter_by(garden_plant_id=plant_id).order_by(
            PlantProgress.recorded_at.desc()
        )

        total_count = query.count()
        records = query.limit(limit).offset(offset).all()

        # Calculate trend if we have data
        trend = None
        if len(records) >= 2:
            sorted_records = sorted(records, key=lambda x: x.recorded_at)
            scores = [r.health_score for r in sorted_records if r.health_score is not None]
            if len(scores) >= 2:
                change = scores[-1] - scores[0]
                trend = {
                    'direction': 'improving' if change > 0 else 'declining' if change < 0 else 'stable',
                    'change': change,
                    'start_score': scores[0],
                    'end_score': scores[-1]
                }

        # Build frontend-friendly progress records with both date and time
        def format_progress_record(r):
            d = r.to_dict()
            # Add both date and time fields for timeline
            dt = d.get('recorded_at')
            if dt:
                from datetime import datetime
                try:
                    parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    d['date'] = parsed.strftime('%Y-%m-%d')
                    d['time'] = parsed.strftime('%H:%M:%S')
                except Exception:
                    d['date'] = dt
                    d['time'] = ''
            else:
                d['date'] = ''
                d['time'] = ''
            # Flatten key health/size/leaf fields for frontend
            d['health_score'] = d.get('health_score', None)
            d['health_status'] = d.get('health_status', None)
            d['green_percentage'] = d.get('green_percentage', None)
            d['yellowing_percentage'] = d.get('yellowing_percentage', None)
            d['estimated_leaf_count'] = d.get('leaves', {}).get('estimated_count', None) if d.get('leaves') else None
            d['height_cm'] = d.get('size', {}).get('height_cm', None) if d.get('size') else None
            d['width_cm'] = d.get('size', {}).get('width_cm', None) if d.get('size') else None
            d['area_cm2'] = d.get('size', {}).get('area_cm2', None) if d.get('size') else None
            return d

        return jsonify({
            'success': True,
            'data': {
                'plant_name': plant.plant_name,
                'progress_records': [format_progress_record(r) for r in records],
                'total': total_count,
                'trend': trend
            }
        }), 200
        
    except Exception as e:
        print(f'Error fetching plant progress: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error fetching progress: {str(e)}'
        }), 500


@garden_bp.route('/garden/user/<int:user_id>/comparison', methods=['GET'])
def compare_user_plants(user_id):
    """
    Compare all plants in user's garden
    Returns ranking and health analysis
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Get latest health score for each plant
        plants = GardenPlant.query.filter_by(user_id=user_id).all()
        
        plants_data = []
        for plant in plants:
            # Get latest progress record
            latest_progress = PlantProgress.query.filter_by(
                garden_plant_id=plant.id
            ).order_by(PlantProgress.recorded_at.desc()).first()
            
            plants_data.append({
                'id': plant.id,
                'plant_name': plant.plant_name,
                'preferred_name': plant.preferred_name or plant.plant_name,
                'health_score': latest_progress.health_score if latest_progress else 0,
                'health_status': latest_progress.health_status if latest_progress else 'unknown'
            })
        
        # Sort plants by health score (descending) for comparison
        ranked_plants = sorted(plants_data, key=lambda x: x['health_score'] or 0, reverse=True)
        comparison = {
            'ranked_plants': ranked_plants,
            'total_plants': len(ranked_plants),
            'healthiest': ranked_plants[0] if ranked_plants else None,
            'needs_attention': [p for p in ranked_plants if (p['health_score'] or 0) < 60]
        }
        
        return jsonify({
            'success': True,
            'data': comparison
        }), 200
        
    except Exception as e:
        print(f'Error comparing plants: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error comparing plants: {str(e)}'
        }), 500


@garden_bp.route('/garden/<int:plant_id>/recommendations', methods=['GET'])
def get_plant_recommendations(plant_id):
    """
    Get AI-powered care recommendations based on latest SAM analysis
    Returns health metrics and actionable recommendations from the SAM pipeline
    """
    try:
        plant = GardenPlant.query.get(plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Plant not found'
            }), 404
        
        # Get latest progress record
        latest_progress = PlantProgress.query.filter_by(
            garden_plant_id=plant_id
        ).order_by(PlantProgress.recorded_at.desc()).first()
        
        if not latest_progress:
            return jsonify({
                'success': True,
                'data': {
                    'recommendations': [
                        'ðŸ“¸ Take a photo to analyze plant health',
                        'ðŸ’§ Follow the plant care guidelines below',
                        'â° Monitor plant regularly for changes'
                    ],
                    'care_info': {
                        'watering': plant.watering_capacity,
                        'sunlight': plant.sunlight_requirements,
                        'soil': plant.soil_type,
                        'temperature': plant.temperature_range
                    }
                }
            }), 200
        
        # Parse analysis data from SAM pipeline
        try:
            analysis = json.loads(latest_progress.analysis_data) if latest_progress.analysis_data else {}
        except:
            analysis = {}
        
        # Extract recommendations from the SAM pipeline results
        recommendations = analysis.get('recommendations', [])
        if not recommendations:
            # Fallback recommendations based on health status
            health_status = latest_progress.health_status or 'good'
            if health_status == 'excellent':
                recommendations = [
                    'âœ… Plant is thriving! Continue current care routine',
                    'ðŸ“¸ Monitor for any changes in leaf coloration',
                    'ðŸ’š Consider propagating or repotting if needed'
                ]
            elif health_status == 'good':
                recommendations = [
                    'âœ… Plant health is good. Maintain current routine',
                    'ðŸ’§ Water as scheduled based on soil moisture',
                    'â˜€ï¸ Ensure consistent sunlight exposure'
                ]
            elif health_status == 'fair':
                recommendations = [
                    'âš ï¸ Plant shows signs of stress. Check soil moisture',
                    'ðŸ’§ Adjust watering frequency if needed',
                    'â˜€ï¸ Review sunlight exposure and adjust if needed'
                ]
            elif health_status == 'poor':
                recommendations = [
                    'âš ï¸ Plant is struggling. Assess all care factors',
                    'ðŸ’§ Check for proper drainage and avoid overwatering',
                    'ðŸŒ¡ï¸ Verify temperature and humidity levels'
                ]
            else:  # critical
                recommendations = [
                    'ðŸš¨ Plant requires urgent attention',
                    'ðŸ’§ Revisit all care parameters immediately',
                    'ðŸ“ž Consider consulting plant care resources'
                ]
        
        # Build scale calibration info if available
        scale_info = {}
        if latest_progress.height_cm or latest_progress.width_cm:
            scale_info = {
                'height_cm': latest_progress.height_cm,
                'width_cm': latest_progress.width_cm,
                'area_cm2': latest_progress.area_cm2,
                'measurement_method': 'SAM segmentation with reference object calibration'
            }
        
        return jsonify({
            'success': True,
            'data': {
                'health_score': latest_progress.health_score,
                'health_status': latest_progress.health_status,
                'recommendations': recommendations,
                'segmentation_confidence': analysis.get('segmentation', {}).get('confidence'),
                'scale_calibration': scale_info,
                'care_info': {
                    'watering': plant.watering_capacity,
                    'sunlight': plant.sunlight_requirements,
                    'soil': plant.soil_type,
                    'humidity': plant.humidity_level,
                    'temperature': plant.temperature_range,
                    'fertilizer': plant.fertilizer_needs
                },
                'latest_analysis': {
                    'recorded_at': latest_progress.recorded_at.isoformat(),
                    'green_percentage': latest_progress.green_percentage,
                    'yellowing_percentage': latest_progress.yellowing_percentage,
                    'vibrancy_score': latest_progress.vibrancy_score,
                    'leaf_density': latest_progress.leaf_density,
                    'estimated_leaf_count': latest_progress.estimated_leaf_count,
                    'foliage_coverage': latest_progress.foliage_coverage,
                    'pixels': {
                        'height': latest_progress.height_pixels,
                        'width': latest_progress.width_pixels,
                        'area': latest_progress.area_pixels
                    }
                }
            }
        }), 200
        
    except Exception as e:
        print(f'Error getting recommendations: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error getting recommendations: {str(e)}'
        }), 500


@garden_bp.route('/garden/user/<int:user_id>/garden-health-summary', methods=['GET'])
def get_garden_health_summary(user_id):
    """
    Get overall garden health summary
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        plants = GardenPlant.query.filter_by(user_id=user_id).all()
        total_plants = len(plants)
        
        health_stats = {
            'excellent': 0,
            'good': 0,
            'fair': 0,
            'poor': 0,
            'critical': 0,
            'unanalyzed': 0
        }
        
        all_scores = []
        
        for plant in plants:
            latest_progress = PlantProgress.query.filter_by(
                garden_plant_id=plant.id
            ).order_by(PlantProgress.recorded_at.desc()).first()
            
            if latest_progress and latest_progress.health_status:
                status = latest_progress.health_status
                if status in health_stats:
                    health_stats[status] += 1
                if latest_progress.health_score:
                    all_scores.append(latest_progress.health_score)
            else:
                health_stats['unanalyzed'] += 1
        
        average_health = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Determine garden status
        if health_stats['critical'] > 0:
            garden_status = 'critical'
        elif health_stats['poor'] > 0:
            garden_status = 'needs_attention'
        elif health_stats['excellent'] > (total_plants * 0.7):
            garden_status = 'thriving'
        else:
            garden_status = 'good'
        
        return jsonify({
            'success': True,
            'data': {
                'total_plants': total_plants,
                'average_health_score': round(average_health, 1),
                'garden_status': garden_status,
                'health_breakdown': health_stats,
                'needs_attention': health_stats['critical'] + health_stats['poor']
            }
        }), 200
        
    except Exception as e:
        print(f'Error getting garden summary: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Error getting garden summary: {str(e)}'
        }), 500
