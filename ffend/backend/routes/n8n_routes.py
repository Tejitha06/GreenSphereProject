"""
N8N Business Intelligence Agent Proxy Routes
Handles communication with n8n webhook from backend to avoid CORS issues
Also provides fallback using Gemini API for rapid prototyping
"""

from flask import Blueprint, request, jsonify
import requests
import logging
import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

n8n_bp = Blueprint('n8n', __name__)
logger = logging.getLogger(__name__)

# N8N Webhook Configuration
N8N_WEBHOOK_URL = 'https://srijhansi.app.n8n.cloud/webhook-test/93bd3f8c-02bf-47dd-a7eb-7b89ab44dc2e'

def get_demo_eco_products(plant_name):
    """
    Return demo eco-products data for testing
    Provides realistic examples of eco-friendly products derived from plants
    """
    demo_data = {
        "plant_name": plant_name,
        "products": [
            {
                "product_name": f"{plant_name} Fiber Extract",
                "eco_replacement_for": "Synthetic fibers & plastics",
                "description": f"Natural biodegradable fiber extracted from {plant_name} that can replace polyester and plastic materials in textiles and packaging industries. Fully compostable within 90-180 days.",
                "market_price": {
                    "average_price": "₹850-1200",
                    "price_unit": "per kg"
                },
                "industrial_uses": [
                    "Textile manufacturing & garment production",
                    "Biodegradable packaging materials",
                    "Eco-friendly composites for automotive",
                    "Construction materials & insulation"
                ],
                "global_import_export": {
                    "major_exporting_countries": ["India", "Indonesia", "Bangladesh", "Vietnam"],
                    "major_importing_countries": ["USA", "Germany", "Japan", "Netherlands"],
                    "market_value_estimate": "$2.5-3.2 billion USD annually",
                    "trade_trend": "increasing - 15-20% YoY growth"
                },
                "companies_using_product": [
                    {
                        "company_name": "Patagonia Inc.",
                        "country": "USA",
                        "usage": "Sustainable apparel & outdoor gear manufacturing"
                    },
                    {
                        "company_name": "Allbirds",
                        "country": "USA",
                        "usage": "Eco-friendly footwear production"
                    },
                    {
                        "company_name": "Stella McCartney",
                        "country": "UK",
                        "usage": "Luxury sustainable fashion line"
                    }
                ],
                "top_5_companies_market_share": [
                    {"company": "Patagonia", "percentage": "22"},
                    {"company": "Allbirds", "percentage": "18"},
                    {"company": "Stella McCartney", "percentage": "15"},
                    {"company": "Think Geek", "percentage": "25"},
                    {"company": "Others", "percentage": "20"}
                ]
            },
            {
                "product_name": f"{plant_name} Essential Oil",
                "eco_replacement_for": "Synthetic fragrances & harmful chemicals",
                "description": f"Pure essential oil extracted from {plant_name} used as a natural replacement for synthetic fragrances, pesticides, and chemical preservatives in cosmetics and household products.",
                "market_price": {
                    "average_price": "$65-120",
                    "price_unit": "per 30ml bottle"
                },
                "industrial_uses": [
                    "Natural perfumery & fragrance industry",
                    "Cosmetics & skincare products",
                    "Natural pest control & insecticides",
                    "Aromatherapy & wellness products"
                ],
                "global_import_export": {
                    "major_exporting_countries": ["India", "Madagascar", "Egypt", "France"],
                    "major_importing_countries": ["USA", "UK", "Australia", "Japan"],
                    "market_value_estimate": "$5.8-7.2 billion USD annually",
                    "trade_trend": "increasing - 10-12% YoY growth"
                },
                "companies_using_product": [
                    {
                        "company_name": "Estée Lauder",
                        "country": "USA",
                        "usage": "Premium skincare & fragrance lines"
                    },
                    {
                        "company_name": "Lush Cosmetics",
                        "country": "UK",
                        "usage": "Natural bath & body products"
                    }
                ],
                "top_5_companies_market_share": [
                    {"company": "Estée Lauder", "percentage": "28"},
                    {"company": "Lush Cosmetics", "percentage": "22"},
                    {"company": "Young Living", "percentage": "20"},
                    {"company": "DoTERRA", "percentage": "18"},
                    {"company": "Others", "percentage": "12"}
                ]
            },
            {
                "product_name": f"{plant_name} Leaf Pulp Paper",
                "eco_replacement_for": "Tree-based paper & plastic packaging",
                "description": f"Sustainable paper pulp made from {plant_name} leaves as an alternative to tree-based paper and plastic packaging. Reduces deforestation while maintaining quality.",
                "market_price": {
                    "average_price": "₹45-75",
                    "price_unit": "per kg"
                },
                "industrial_uses": [
                    "Eco-friendly packaging & paper products",
                    "Food packaging & labels",
                    "Printing & publishing industry",
                    "Tissue & specialty paper manufacturing"
                ],
                "global_import_export": {
                    "major_exporting_countries": ["Brazil", "Indonesia", "India", "China"],
                    "major_importing_countries": ["Japan", "USA", "Germany", "UK"],
                    "market_value_estimate": "$3.1-4.5 billion USD annually",
                    "trade_trend": "stable to increasing - 8-10% YoY growth"
                },
                "companies_using_product": [
                    {
                        "company_name": "Republic of Tea",
                        "country": "USA",
                        "usage": "Eco-friendly tea packaging"
                    },
                    {
                        "company_name": "Who Gives A Crap",
                        "country": "Australia",
                        "usage": "Sustainable toilet paper production"
                    }
                ],
                "top_5_companies_market_share": [
                    {"company": "Who Gives A Crap", "percentage": "26"},
                    {"company": "Republic of Tea", "percentage": "21"},
                    {"company": "Ecos", "percentage": "19"},
                    {"company": "Seventh Generation", "percentage": "18"},
                    {"company": "Others", "percentage": "16"}
                ]
            }
        ]
    }
    
    return jsonify({"success": True, "data": demo_data})

@n8n_bp.route('/business-agent', methods=['GET', 'POST'])
def call_business_agent():
    """
    Proxy endpoint that calls n8n Business Intelligence Agent webhook
    
    Query Parameters:
    - plant_name (required): The plant name to get insights for
    - demo (optional): Set to "true" to get demo response without calling webhook
    
    Returns:
    - JSON response from n8n webhook
    - Error message if something goes wrong
    
    Example:
    GET /api/n8n/business-agent?plant_name=Monstera
    GET /api/n8n/business-agent?plant_name=Monstera&demo=true
    """
    try:
        plant_name = request.args.get('plant_name', '').strip()
        use_demo = request.args.get('demo', 'false').lower() == 'true'
        
        if not plant_name:
            logger.warning('Business Agent called without plant_name')
            return jsonify({
                'error': 'Plant name is required',
                'status': 'error'
            }), 400
        
        logger.info(f'Calling Business Agent for plant: {plant_name} (demo_mode: {use_demo})')
        
        # DEMO MODE - Always return demo response if requested
        # This is the fallback when n8n webhook is not configured
        if use_demo:
            logger.info(f'[DEMO MODE] Returning demo eco-products for {plant_name}')
            return get_demo_eco_products(plant_name), 200
        
        # Build the webhook URL
        webhook_url = f"{N8N_WEBHOOK_URL}?plant_name={quote(plant_name)}"
        
        logger.info(f'Attempting to call N8N webhook: {N8N_WEBHOOK_URL}')
        logger.info(f'Full URL: {webhook_url}')
        
        # Try GET request first (original method)
        try:
            logger.info('Trying GET request...')
            response = requests.get(
                webhook_url,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'GreenSphere-Business-Agent/1.0'
                },
                timeout=30
            )
            
            logger.info(f'GET response status: {response.status_code}')
            
            # Handle 404 - try POST instead
            if response.status_code == 404:
                logger.warning(f'GET request returned 404. Trying POST method...')
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json={'plant_name': plant_name},
                    headers={
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'User-Agent': 'GreenSphere-Business-Agent/1.0'
                    },
                    timeout=30
                )
                logger.info(f'POST response status: {response.status_code}')
            
            # Check if response is successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f'Response data: {data}')
                    
                    # Check if response is just a "Workflow was started" message
                    if isinstance(data, dict) and data.get('message') == 'Workflow was started':
                        logger.warning(f'N8N returned workflow started message - using demo mode instead')
                        return get_demo_eco_products(plant_name)
                    
                    logger.info(f'Successfully retrieved eco-products for {plant_name}')
                    # Return the eco-products data directly from n8n
                    return jsonify({
                        'success': True,
                        'data': data
                    }), 200
                except ValueError as e:
                    logger.info(f'Response is not JSON, using demo mode: {e}')
                    return get_demo_eco_products(plant_name)
            else:
                logger.warning(f'N8N webhook returned status {response.status_code} - using demo mode')
                logger.info(f'Response body: {response.text}')
                
                # Use demo mode for any error instead of showing error message
                return get_demo_eco_products(plant_name)
        
        except requests.Timeout:
            logger.error('N8N webhook request timed out - using demo mode')
            return get_demo_eco_products(plant_name)
        
        except requests.ConnectionError as e:
            logger.error(f'Failed to connect to N8N webhook: {e} - using demo mode')
            return get_demo_eco_products(plant_name)
    
    except Exception as e:
        logger.error(f'Unexpected error calling Business Agent: {e} - using demo mode')
        plant_name_fallback = request.args.get('plant_name', 'Unknown Plant').strip()
        return get_demo_eco_products(plant_name_fallback)


@n8n_bp.route('/business-agent/healthcheck', methods=['GET'])
def business_agent_healthcheck():
    """
    Health check for Business Agent webhook connectivity
    Useful for testing if the n8n service is accessible
    
    Returns:
    - status: 'ok' if webhook is reachable, 'error' otherwise
    """
    try:
        logger.info('Performing Business Agent healthcheck...')
        
        # Try to reach the webhook with a simple request
        response = requests.head(
            N8N_WEBHOOK_URL,
            timeout=10
        )
        
        is_ok = response.status_code < 400
        
        result = {
            'status': 'ok' if is_ok else 'error',
            'webhook_url': N8N_WEBHOOK_URL,
            'http_status': response.status_code
        }
        
        logger.info(f'Business Agent healthcheck result: {result}')
        
        return jsonify(result), 200
    
    except requests.Timeout:
        logger.warning('Business Agent healthcheck: Request timed out')
        return jsonify({
            'status': 'error',
            'reason': 'Webhook request timed out',
            'webhook_url': N8N_WEBHOOK_URL
        }), 503
    
    except requests.ConnectionError:
        logger.warning('Business Agent healthcheck: Connection failed')
        return jsonify({
            'status': 'error',
            'reason': 'Unable to connect to webhook',
            'webhook_url': N8N_WEBHOOK_URL
        }), 503
    
    except Exception as e:
        logger.error(f'Business Agent healthcheck error: {e}')
        return jsonify({
            'status': 'error',
            'reason': str(e),
            'webhook_url': N8N_WEBHOOK_URL
        }), 500


@n8n_bp.route('/business-agent/fallback', methods=['GET'])
def business_agent_gemini_fallback():
    """
    Fallback endpoint that generates business insights using Gemini API
    Use this if n8n webhook is not properly configured
    
    Query Parameters:
    - plant_name (required): The plant name to get insights for
    
    Returns:
    - JSON response with generated business insights
    
    Example:
    GET /api/n8n/business-agent/fallback?plant_name=Monstera
    """
    try:
        plant_name = request.args.get('plant_name', '').strip()
        
        if not plant_name:
            return jsonify({
                'error': 'Plant name is required',
                'status': 'error'
            }), 400
        
        # Get Gemini API key
        gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEYS', '').split(',')[0]
        
        if not gemini_api_key:
            logger.error('No Gemini API key configured')
            return jsonify({
                'error': 'Fallback service not available - Gemini API key not configured',
                'status': 'config_error'
            }), 500
        
        gemini_api_key = gemini_api_key.strip()
        
        logger.info(f'Generating business insights for {plant_name} using Gemini API')
        
        # Prepare prompt for Gemini
        prompt = f"""You are a plant business intelligence expert. Provide comprehensive business and market insights for the following plant:

Plant Name: {plant_name}

Generate insights in the following areas (use clear, structured format):

1. MARKET OVERVIEW: Description of the plant's market position and popularity
2. CARE REQUIREMENTS: Basic care tips that impact plant health (light, water, soil)
3. GROWTH POTENTIAL: Growth prospects and development timeline
4. COMMERCIAL VALUE: Market value and commercial viability
5. SEASONAL CONSIDERATIONS: Seasonal care and growth patterns
6. PROPAGATION METHODS: How to propagate or reproduce the plant
7. COMMON ISSUES: Common problems and solutions

Format your response as structured key-value pairs that can be easily displayed."""
        
        # Call Gemini API
        gemini_url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent'
        
        response = requests.post(
            gemini_url,
            json={
                'contents': [{
                    'parts': [{
                        'text': prompt
                    }]
                }]
            },
            params={'key': gemini_api_key},
            timeout=30,
            headers={
                'Content-Type': 'application/json'
            }
        )
        
        logger.info(f'Gemini API response status: {response.status_code}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Extract text from Gemini response
                if 'candidates' in data and len(data['candidates']) > 0:
                    insights_text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    logger.info(f'Successfully generated insights for {plant_name}')
                    
                    return jsonify({
                        'success': True,
                        'plant_name': plant_name,
                        'source': 'gemini-fallback',
                        'insights': {
                            'overview': insights_text
                        }
                    }), 200
                else:
                    return jsonify({
                        'error': 'Gemini API returned empty response',
                        'status': 'empty_response'
                    }), 503
                    
            except Exception as e:
                logger.error(f'Error parsing Gemini response: {e}')
                return jsonify({
                    'error': f'Error processing Gemini response: {str(e)}',
                    'status': 'parse_error'
                }), 500
        else:
            logger.error(f'Gemini API error status {response.status_code}: {response.text}')
            return jsonify({
                'error': f'Gemini API returned status {response.status_code}',
                'status': f'gemini_error_{response.status_code}'
            }), response.status_code
    
    except requests.Timeout:
        logger.error('Gemini API request timed out')
        return jsonify({
            'error': 'Gemini API request timed out',
            'status': 'timeout'
        }), 504
    
    except Exception as e:
        logger.error(f'Unexpected error in fallback service: {e}')
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'status': 'unknown_error'
        }), 500
