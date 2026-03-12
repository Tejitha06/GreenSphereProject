"""
PlantID v3 API Service
Handles integration with Plant.ID API for plant identification and disease detection
"""

import requests
import logging
from typing import Dict, Optional, List
from flask import current_app
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class PlantIDService:
    """Service to interact with PlantID v3 API with automatic key rotation support"""
    
    def __init__(self, api_key: str = None, api_url: str = None, api_key_backup: str = None):
        """Initialize PlantID service with API credentials and automatic key rotation"""
        self.api_url = api_url or current_app.config.get('PLANTID_API_URL')
        self._current_key_idx = 0
        
        # Prefer multiple keys from PLANTID_API_KEYS, fallback to legacy keys
        api_keys = current_app.config.get('PLANTID_API_KEYS', [])
        if isinstance(api_keys, str):
            api_keys = [k.strip() for k in api_keys.split(',') if k.strip()]
        else:
            api_keys = [k.strip() for k in api_keys if k.strip()] if api_keys else []
        
        # Fallback to legacy single/backup keys if no rotation keys configured
        if not api_keys:
            legacy_key = api_key or current_app.config.get('PLANTID_API_KEY')
            legacy_backup = api_key_backup or current_app.config.get('PLANTID_API_KEY_BACKUP')
            api_keys = [k for k in [legacy_key, legacy_backup] if k and k.strip()]
        
        if not api_keys:
            raise ValueError("PlantID API keys not configured. Please set PLANTID_API_KEYS in environment variables.")
        
        self.api_keys = api_keys
        self.session = requests.Session()
        logger.info(f'PlantIDService initialized with {len(self.api_keys)} API keys for automatic rotation')
    
    def _rotate_keys(self):
        """Yield API keys in rotation (round-robin)"""
        for i in range(len(self.api_keys)):
            idx = (self._current_key_idx + i) % len(self.api_keys)
            yield self.api_keys[idx]
        # Move to next key for next request
        self._current_key_idx = (self._current_key_idx + 1) % len(self.api_keys)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Make API request with automatic key rotation
        
        Args:
            method: HTTP method ('get' or 'post')
            endpoint: API endpoint URL
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object if successful, None if all keys failed
        """
        last_error = None
        
        for attempt, api_key in enumerate(self._rotate_keys(), 1):
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'Api-Key': api_key
                }
                
                if method.lower() == 'post':
                    response = self.session.post(endpoint, headers=headers, **kwargs)
                elif method.lower() == 'get':
                    response = self.session.get(endpoint, headers=headers, **kwargs)
                else:
                    raise ValueError(f'Unsupported HTTP method: {method}')
                
                # Check for errors
                if response.status_code == 200:
                    logger.info(f'PlantID API request successful (Key #{attempt}/{len(self.api_keys)})')
                    return response
                elif response.status_code == 401:
                    # Invalid API key
                    logger.warning(f'PlantID API key #{attempt}/{len(self.api_keys)} is invalid (401). Rotating to next key...')
                    last_error = f'Invalid API key (attempt {attempt})'
                    continue
                elif response.status_code == 429:
                    # Rate limited
                    logger.warning(f'PlantID API key #{attempt}/{len(self.api_keys)} rate limited (429). Rotating to next key...')
                    last_error = f'Rate limited (attempt {attempt})'
                    continue
                elif response.status_code >= 500:
                    # Server error - try next key
                    logger.warning(f'PlantID API returned {response.status_code}. Rotating to next key...')
                    last_error = f'Server error {response.status_code}'
                    continue
                else:
                    # Other error
                    logger.error(f'PlantID API returned {response.status_code}')
                    return response
            
            except requests.exceptions.Timeout:
                logger.warning(f'PlantID API key #{attempt}/{len(self.api_keys)} timed out. Rotating to next key...')
                last_error = f'Timeout (attempt {attempt})'
                continue
            except requests.exceptions.ConnectionError:
                logger.warning(f'PlantID API key #{attempt}/{len(self.api_keys)} connection error. Rotating to next key...')
                last_error = f'Connection error (attempt {attempt})'
                continue
            except Exception as e:
                logger.warning(f'PlantID API key #{attempt}/{len(self.api_keys)} error: {str(e)}. Rotating to next key...')
                last_error = f'Error: {str(e)}'
                continue
        
        # All keys exhausted
        logger.error(f'All PlantID API keys exhausted ({len(self.api_keys)} keys tried). Last error: {last_error}')
        return None
    
    def get_plant_details(self, entity_id: str) -> Optional[Dict]:
        """
        Get detailed information about a plant using its entity_id with fallback key support
        
        Args:
            entity_id: The PlantID entity identifier
            
        Returns:
            Dictionary with plant details or None if failed
        """
        try:
            # Call Plant.ID API for plant details - use only documented fields
            # Note: Some fields like best_watering, best_light_condition, etc. may require different API access
            endpoint = f'{self.api_url}/kb/plants/{entity_id}?details=common_names,url,description,taxonomy,rank,gbif_id,inaturalist_id,image,synonyms,edible_parts,watering,propagation_methods&lang=en'
            logger.info(f'Fetching plant details: {endpoint}')
            
            response = self._make_request('get', endpoint, timeout=15)
            
            if response is None:
                logger.error('Failed to get plant details - all keys exhausted')
                return None
            
            result = response.json()
            logger.info(f'Plant details fetched successfully: {result}')
            return result
            
        except Exception as e:
            logger.error(f'Error fetching plant details: {str(e)}')
            return None
    
    def identify_plant(self, image_data: bytes, file_name: str = 'plant.jpg') -> Optional[Dict]:
        """
        Identify a plant from an image with fallback key support
        
        Args:
            image_data: Binary image data
            file_name: Name of the image file
            
        Returns:
            Dictionary with plant identification results or None if failed
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request payload for Plant Identification
            payload = {
                'images': [image_base64],
                'similar_images': True
            }
            
            # Query parameters to request detailed plant information
            params = {
                'details': 'common_names,url,description,taxonomy,rank,gbif_id,inaturalist_id,image,synonyms,edible_parts,propagation_methods,watering,best_watering,best_light_condition,best_soil_type,common_uses,toxicity,cultural_significance'
            }
            
            # Call Plant.ID API for identification with fallback
            endpoint = f'{self.api_url}/identification'
            logger.info(f'Calling PlantID API for identification: {endpoint}')
            
            response = self._make_request('post', endpoint, json=payload, params=params, timeout=45)
            
            if response is None:
                logger.error('PlantID identification failed - all keys exhausted')
                return None
            
            result = response.json()
            logger.info(f'PlantID identification successful')
            logger.info(f'PlantID raw response: {result}')
            
            # Parse and format the response
            return self._parse_identification_response(result)
            
        except requests.exceptions.Timeout:
            logger.error('PlantID API request timed out (45s)')
            return None
        except requests.exceptions.ConnectionError:
            logger.error('Failed to connect to PlantID API')
            return None
        except Exception as e:
            logger.error(f'Error during plant identification: {str(e)}')
            return None
    
    def detect_disease(self, image_data: bytes, file_name: str = 'plant.jpg') -> Optional[Dict]:
        """
        Detect diseases in a plant from an image with fallback key support
        
        Args:
            image_data: Binary image data
            file_name: Name of the image file
            
        Returns:
            Dictionary with disease detection results or None if failed
        """
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare request payload - PlantID v3 health assessment
            payload = {
                'images': [image_base64],
                'health': 'only'  # Focus on health/disease assessment
            }
            
            # Query params to get disease details in response
            # Only use valid Plant.ID v3 API parameters
            params = {
                'details': 'common_names,description,image,taxonomy,url,toxicity'
            }
            
            # Call Plant.ID API for health/disease detection with fallback
            endpoint = f'{self.api_url}/identification'
            logger.info(f'Calling PlantID API for disease detection: {endpoint}')
            
            response = self._make_request('post', endpoint, json=payload, params=params, timeout=30)
            
            if response is None:
                logger.error('PlantID disease detection failed - all keys exhausted')
                return None
            
            result = response.json()
            logger.info(f'PlantID disease detection successful')
            
            # Parse and format the response
            return self._parse_disease_response(result)
            
        except requests.exceptions.Timeout:
            logger.error('PlantID API request timed out')
            return None
        except requests.exceptions.ConnectionError:
            logger.error('Failed to connect to PlantID API')
            return None
        except Exception as e:
            logger.error(f'Error during disease detection: {str(e)}')
            return None
    
    def _parse_identification_response(self, response: Dict) -> Optional[Dict]:
        """
        Parse PlantID identification response and format for frontend
        
        When using ?details=... query params, details come back inside each suggestion
        """
        try:
            # PlantID v3 uses result.classification.suggestions
            result = response.get('result', {})
            classification = result.get('classification', {})
            suggestions = classification.get('suggestions', [])
            
            if not suggestions:
                logger.warning('No plant identification results found')
                return None
            
            # Get the top result - details are now embedded in the suggestion
            top_result = suggestions[0]
            details = top_result.get('details', {})
            
            logger.info(f'Plant details from suggestion: {details}')
            
            # Extract common names
            common_names = details.get('common_names', [])
            if common_names and isinstance(common_names, list):
                display_name = common_names[0]
            else:
                display_name = top_result.get('name', 'Unknown')
            
            # Extract watering info
            watering = details.get('watering', {})
            if isinstance(watering, dict) and watering:
                water_info = f"Moisture level: Min {watering.get('min', 'N/A')} - Max {watering.get('max', 'N/A')}"
            else:
                water_info = None
            
            # Extract edible parts
            edible_parts = details.get('edible_parts', [])
            if edible_parts and isinstance(edible_parts, list):
                purposes = [f'Edible parts: {", ".join(edible_parts)}']
            else:
                purposes = ['Ornamental']
            
            # Extract propagation methods
            propagation = details.get('propagation_methods', [])
            if propagation and isinstance(propagation, list):
                purposes.append(f'Propagation: {", ".join(propagation)}')
            
            # Extract toxicity info - it's a string paragraph from API
            toxicity_data = details.get('toxicity', None)
            if toxicity_data and isinstance(toxicity_data, str):
                toxicity_lower = toxicity_data.lower()
                if 'toxic' in toxicity_lower or 'poisonous' in toxicity_lower or 'harmful' in toxicity_lower:
                    toxicity_status = 'toxic'
                elif 'safe' in toxicity_lower or 'non-toxic' in toxicity_lower or 'edible' in toxicity_lower:
                    toxicity_status = 'safe'
                else:
                    toxicity_status = 'caution'
                toxicity_info = toxicity_data
            else:
                toxicity_status = 'unknown'
                toxicity_info = 'Toxicity information not available - please research before handling'
            
            # Extract care information - all are string paragraphs
            best_light = details.get('best_light_condition', None)
            best_soil = details.get('best_soil_type', None)
            best_watering = details.get('best_watering', None)
            common_uses = details.get('common_uses', None)
            cultural_significance = details.get('cultural_significance', None)
            synonyms = details.get('synonyms', [])
            
            # Extract description - can be dict with 'value' or direct string
            description_data = details.get('description', None)
            if isinstance(description_data, dict):
                description = description_data.get('value', 'Plant identified using AI analysis')
            elif isinstance(description_data, str):
                description = description_data
            else:
                description = 'Plant identified using AI analysis'
            
            # Extract image
            image_data = details.get('image', {})
            if isinstance(image_data, dict):
                image_url = image_data.get('value', None)
            elif isinstance(image_data, str):
                image_url = image_data
            else:
                image_url = None
            
            # Build response
            identified_plant = {
                'success': True,
                'confidence': round(top_result.get('probability', 0) * 100, 2),
                'name': display_name,
                'scientific': top_result.get('name', 'Unknown'),
                'common_names': common_names if isinstance(common_names, list) else [],
                'synonyms': synonyms[:5] if isinstance(synonyms, list) and synonyms else [],
                'description': description,
                
                # Care information from API
                'purposes': purposes,
                'common_uses': common_uses if isinstance(common_uses, str) else None,
                'cultural_significance': cultural_significance if isinstance(cultural_significance, str) else None,
                'best_light': best_light if isinstance(best_light, str) else None,
                'best_soil': best_soil if isinstance(best_soil, str) else None,
                'water': best_watering if isinstance(best_watering, str) else water_info,
                'watering_details': watering if isinstance(watering, dict) else None,
                
                # Toxicity
                'toxicity': toxicity_status,
                'toxicityInfo': toxicity_info,
                
                # Additional metadata from API
                'similar_images': top_result.get('similar_images', []),
                'probability': top_result.get('probability'),
                'taxonomy': details.get('taxonomy', {}),
                'rank': details.get('rank', None),
                'image_url': image_url,
                'wiki_url': details.get('url', None),
                'gbif_id': details.get('gbif_id', None),
                'inaturalist_id': details.get('inaturalist_id', None)
            }
            
            return identified_plant
            
        except Exception as e:
            logger.error(f'Error parsing identification response: {str(e)}')
            return None
    
    def _parse_disease_response(self, response: Dict) -> Optional[Dict]:
        """
        Parse PlantID health assessment response and format for frontend
        
        When using health='only', response structure is:
        {
            "result": {
                "is_healthy": {"binary": true/false, "probability": 0.95},
                "disease": {
                    "suggestions": [
                        {
                            "name": "Disease Name",
                            "probability": 0.95,
                            "details": {
                                "local_name": "...",
                                "description": "...",
                                "url": "...",
                                "treatment": {...},
                                "classification": {...},
                                "common_names": [...]
                            }
                        }
                    ]
                }
            }
        }
        """
        try:
            result = response.get('result', {})
            
            # Check if plant is healthy
            is_healthy_data = result.get('is_healthy', {})
            is_healthy = is_healthy_data.get('binary', True)
            health_probability = is_healthy_data.get('probability', 0)
            
            if is_healthy:
                return {
                    'success': True,
                    'isHealthy': True,
                    'message': 'Your plant appears to be healthy!',
                    'confidence': round(health_probability * 100, 2),
                    'title': 'Healthy Plant',
                    'description': 'No diseases or health issues detected in the image.'
                }
            
            # Get disease suggestions
            disease_data = result.get('disease', {})
            suggestions = disease_data.get('suggestions', [])
            
            if not suggestions:
                return {
                    'success': True,
                    'isHealthy': True,
                    'message': 'No specific diseases detected',
                    'title': 'Unknown Issue',
                    'description': 'Plant may have some issues but no specific disease was identified.'
                }
            
            # Get the top disease suggestion
            top_disease = suggestions[0]
            details = top_disease.get('details', {})
            
            logger.info(f'Disease details from API: {details}')
            
            # Extract treatment info
            treatment = details.get('treatment', {})
            biological_treatment = treatment.get('biological', []) if isinstance(treatment, dict) else []
            chemical_treatment = treatment.get('chemical', []) if isinstance(treatment, dict) else []
            prevention_tips = treatment.get('prevention', []) if isinstance(treatment, dict) else []
            
            # Build home remedies from biological treatments
            home_remedies = biological_treatment if biological_treatment else self._get_home_remedies(top_disease.get('name', ''))
            
            # Build pesticide recommendations from chemical treatments
            pesticides = chemical_treatment if chemical_treatment else self._get_pesticide_recommendations(top_disease.get('name', ''))
            
            # Get prevention tips
            prevention = prevention_tips if prevention_tips else self._get_prevention_tips(top_disease.get('name', ''))
            
            detected_disease = {
                'success': True,
                'isHealthy': False,
                'title': top_disease.get('name', 'Unknown Disease'),
                'name': details.get('local_name', top_disease.get('name', 'Unknown Disease')),
                'scientific_name': top_disease.get('name', ''),
                'common_names': details.get('common_names', []),
                'probability': round(top_disease.get('probability', 0) * 100, 2),
                'description': details.get('description', 'No description available'),
                'severity': self._estimate_severity(top_disease.get('probability', 0)),
                
                # Treatment information from API
                'causes': self._extract_causes(top_disease.get('name', '')),
                'symptoms': self._extract_symptoms(details.get('description', '')),
                'homeRemedies': home_remedies,
                'fertilizer': ['Apply balanced fertilizer', 'Boost plant health with nutrients'],
                'pesticide': pesticides,
                'prevention': prevention,
                
                # Additional metadata
                'treatment_details': treatment,
                'classification': details.get('classification', {}),
                'wiki_url': details.get('url', None),
                'similar_images': top_disease.get('similar_images', [])
            }
            
            return detected_disease
            
        except Exception as e:
            logger.error(f'Error parsing disease response: {str(e)}')
            return None
    
    # Helper methods to enrich API responses
    
    def _extract_purposes(self, details: Dict) -> List[str]:
        """Extract plant purposes from details"""
        purposes = []
        
        # Check for air purification capability
        if details.get('air_purification'):
            purposes.append('Air Purification')
        
        # Check for edibility
        if details.get('edible'):
            purposes.append('Edible')
        
        # Check for medicinal properties
        if details.get('medicinal_use'):
            purposes.append('Medicinal')
        
        # Add decorative (most plants)
        purposes.append('Decorative')
        
        # Add ease of care
        if details.get('care_level') == 'Easy':
            purposes.append('Low Maintenance')
        
        return purposes if purposes else ['Decorative']
    
    def _generate_suitability(self, plant_name: str) -> str:
        """Generate suitability text based on plant name and characteristics"""
        return f"Great for adding natural beauty to your space. A wonderful plant that can thrive in various indoor conditions. Perfect for plant enthusiasts and home decorators."
    
    def _format_climate(self, temp_data: Dict, humidity_data: Dict) -> str:
        """Format climate information"""
        climate_parts = []
        
        if temp_data:
            min_temp = temp_data.get('min', 'Variable')
            max_temp = temp_data.get('max', 'Variable')
            climate_parts.append(f"Temperature: {min_temp}-{max_temp}°C")
        
        climate_parts.append("Bright, indirect light preferred")
        
        if humidity_data:
            humidity_level = humidity_data.get('percentage', 'Moderate')
            climate_parts.append(f"Humidity: {humidity_level}%")
        
        return '. '.join(climate_parts) + '.'
    
    def _estimate_severity(self, probability: float) -> str:
        """Estimate disease severity based on probability"""
        if probability >= 0.8:
            return 'Very High'
        elif probability >= 0.6:
            return 'High'
        elif probability >= 0.4:
            return 'Moderate'
        else:
            return 'Low'
    
    def _extract_causes(self, disease_name: str) -> List[str]:
        """Extract disease causes - would normally come from database"""
        causes_map = {
            'powdery_mildew': ['High humidity', 'Poor air circulation', 'Warm temperatures'],
            'root_rot': ['Overwatering', 'Poor drainage', 'Cold soil'],
            'leaf_spot': ['High humidity', 'Wet foliage', 'Poor air circulation'],
            'mold': ['High humidity', 'Poor ventilation', 'Dense foliage'],
        }
        
        for key, causes in causes_map.items():
            if key.lower() in disease_name.lower():
                return causes
        
        return ['Environmental stress', 'Poor plant care', 'Pathogens']
    
    def _extract_symptoms(self, description: str) -> List[str]:
        """Extract symptoms from disease description"""
        # This is a simplified extraction - in production, use a database
        if not description:
            return ['Visible signs of disease']
        
        # Create a basic list of common symptoms
        symptom_keywords = {
            'spots': 'Brown or black spots on leaves',
            'rot': 'Soft, mushy tissue',
            'mold': 'Fuzzy growth on plant',
            'wilting': 'Drooping and wilting',
            'yellowing': 'Yellow leaves',
            'curl': 'Curled or distorted leaves'
        }
        
        symptoms = []
        for keyword, symptom in symptom_keywords.items():
            if keyword.lower() in description.lower():
                symptoms.append(symptom)
        
        return symptoms if symptoms else ['Check plant health status']
    
    def _get_home_remedies(self, disease_name: str) -> List[str]:
        """Get home remedies for disease"""
        remedies = [
            'Remove affected leaves and plant parts',
            'Improve air circulation around the plant',
            'Adjust watering practices',
            'Isolate infected plant from others'
        ]
        return remedies
    
    def _get_pesticide_recommendations(self, disease_name: str) -> List[str]:
        """Get pesticide recommendations"""
        recommendations = [
            'Consult local agricultural extension office',
            'Use approved fungicides or bactericides',
            'Follow product instructions carefully',
            'Repeat treatments as recommended'
        ]
        return recommendations
    
    def _get_prevention_tips(self, disease_name: str) -> List[str]:
        """Get prevention tips"""
        prevention = [
            'Maintain proper watering practices',
            'Ensure good air circulation',
            'Remove dead or diseased plant material',
            'Sanitize tools between uses',
            'Choose disease-resistant varieties'
        ]
        return prevention


# Global service instance
_plantid_service = None


def get_plantid_service() -> PlantIDService:
    """Get or create PlantID service instance (lazy-load to ensure Flask context exists)"""
    global _plantid_service
    try:
        if _plantid_service is None:
            logger.info('Initializing PlantIDService...')
            _plantid_service = PlantIDService()
            logger.info(f'PlantIDService initialized successfully with {len(_plantid_service.api_keys)} keys')
        return _plantid_service
    except Exception as e:
        logger.error(f'Failed to initialize PlantIDService: {str(e)}', exc_info=True)
        raise
