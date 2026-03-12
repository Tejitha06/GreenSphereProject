"""
Chatbot Routes - Prakriti Garden Assistant using Google Gemini API
"""

import os
from flask import Blueprint, request, jsonify
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')
logger = logging.getLogger(__name__)

# Configure Gemini API with key rotation
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent'

class GeminiKeyRotator:
    """Manages multiple Gemini API keys and rotates on rate limit errors"""
    def __init__(self, api_keys_str):
        self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        self.current_index = 0
        if self.api_keys:
            logger.info(f'Initialized {len(self.api_keys)} Gemini API keys for rotation')
    
    def get_next_key(self):
        """Get the next API key in rotation"""
        if not self.api_keys:
            raise Exception('No Gemini API keys configured')
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        return key
    
    def rotate_on_error(self):
        """Move to next key after error"""
        if self.api_keys:
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            logger.warning(f'Rotating to API key #{self.current_index + 1}/{len(self.api_keys)}')

# Initialize key rotator
gemini_keys_str = os.getenv('GEMINI_API_KEYS', '')
key_rotator = GeminiKeyRotator(gemini_keys_str)

# System prompt for Prakriti chatbot
PRAKRITI_SYSTEM_PROMPT = """You are Prakriti, a helpful garden and plant care assistant.

SCOPE - You ONLY help with:
• Plant care advice and tips
• Watering schedules
• Plant identification
• Disease identification and treatment
• Soil types and fertilizers
• Sunlight requirements
• Garden planning and maintenance
• Common gardening problems

STRICT RESTRICTIONS - You MUST NOT:
• Answer mathematical questions or do calculations
• Provide personal preference advice (fashion, relationships, career, etc.)
• Answer general knowledge questions unrelated to plants
• Engage in casual conversation topics
• Answer ambiguous questions outside plant/gardening domain

IF USER ASKS ABOUT:
• Plant identification issues → Suggest: "For accurate plant identification, please visit our Plant Identification page where you can upload a photo for instant analysis."
• Plant disease diagnosis → Suggest: "For detailed disease analysis and treatment options, please visit our Disease Detection page where you can upload the affected leaf for diagnosis."
• Topics outside your scope → Politely decline and redirect to plant/gardening topics

RESPONSE GUIDELINES:
• Be friendly and encouraging
• Keep responses concise but informative
• Use emojis occasionally
• Format responses with clear line breaks between different points
• Do NOT use asterisks or underscores for formatting
• Start each new point on a new line

If a question is outside your scope, politely say something like:
"I'm specifically trained to help with plant care and gardening. That question is outside my expertise. Is there anything about your plants or garden I can help with?"

If user needs plant/disease identification, suggest the appropriate page."""


@chatbot_bp.route('/ask', methods=['POST'])
def ask_prakriti():
    """
    Chat endpoint for Prakriti garden assistant
    Expects JSON: {"message": "user question", "isFirstMessage": boolean}
    Automatically rotates through multiple API keys on rate limit errors
    """
    try:
        if not key_rotator.api_keys:
            return jsonify({
                'success': False,
                'error': 'Gemini API keys not configured. Please set GEMINI_API_KEYS in .env file'
            }), 400

        data = request.get_json()
        user_message = data.get('message', '').strip()
        is_first_message = data.get('isFirstMessage', False)

        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400

        # Prepare system prompt with optional greeting
        system_prompt = PRAKRITI_SYSTEM_PROMPT
        if is_first_message:
            system_prompt += "\n\nAs this is the start of our conversation, begin with a warm, brief greeting acknowledging the user's interest in gardening."
        else:
            system_prompt += "\n\nDo NOT include any greeting or introductory pleasantries. Get directly to answering the user's question."

        # Prepare request to Gemini API
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': [
                {
                    'parts': [
                        {
                            'text': system_prompt + '\n\nUser: ' + user_message
                        }
                    ]
                }
            ]
        }
        
        # Try with current key, rotate on failure
        max_retries = len(key_rotator.api_keys)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                api_key = key_rotator.get_next_key()
                
                # Call Gemini API
                response = requests.post(
                    f'{GEMINI_API_URL}?key={api_key}',
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        message_text = result['candidates'][0]['content']['parts'][0]['text']
                        logger.info(f'Chatbot response generated successfully with key #{attempt + 1}')
                        return jsonify({
                            'success': True,
                            'message': message_text
                        }), 200
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'No response from Gemini API'
                        }), 500
                
                # Check for rate limit / quota errors
                elif response.status_code in [429, 403, 500, 503]:
                    error_msg = response.text if response.text else f'HTTP {response.status_code}'
                    logger.warning(f'Gemini API key #{attempt + 1} returned {response.status_code}. {error_msg}. Rotating to next key...')
                    last_error = error_msg
                    key_rotator.rotate_on_error()
                    continue
                
                else:
                    error_msg = response.text if response.text else f'HTTP {response.status_code}'
                    logger.error(f"Gemini API error: {error_msg}")
                    return jsonify({
                        'success': False,
                        'error': f'Gemini API error: {error_msg}'
                    }), response.status_code
            
            except requests.exceptions.Timeout:
                logger.warning(f'API key #{attempt + 1} timed out. Rotating to next key...')
                last_error = 'Request timeout'
                key_rotator.rotate_on_error()
                continue
            
            except Exception as e:
                logger.warning(f'API key #{attempt + 1} failed: {str(e)}. Rotating to next key...')
                last_error = str(e)
                key_rotator.rotate_on_error()
                continue
        
        # All keys exhausted
        logger.error(f'All {max_retries} Gemini API keys exhausted. Last error: {last_error}')
        return jsonify({
            'success': False,
            'error': 'All API keys exhausted or unavailable',
            'message': 'Prakriti is currently unavailable. Please try again in a few moments.'
        }), 503

    except Exception as e:
        logger.error(f"Unexpected chatbot error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@chatbot_bp.route('/health', methods=['GET'])
def chatbot_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'gemini_configured': len(key_rotator.api_keys) > 0,
        'api_keys_available': len(key_rotator.api_keys),
        'current_key_index': key_rotator.current_index
    }), 200
