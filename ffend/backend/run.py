"""
Run the Flask application
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

if __name__ == '__main__':
    app = create_app('development')
    
    print("""
============================================================
GreenSphere Backend Server
============================================================
Server: http://localhost:5000
Press Ctrl+C to stop the server

LIGHTMETER ENDPOINTS AVAILABLE:
  POST   /analyze                 - Analyze plant in image for light requirements
  GET    /analyze                 - Get health check
  GET    /get-location-by-ip      - Get user location from IP
  GET    /get-weather-by-coords   - Get weather data by coordinates
  GET    /api/health             - Health check endpoint

NOTE: First debug visualization request will initialize SAM model
      (may take 10-30 seconds depending on hardware)

GEMINI API: Optional (uses fallback plant database if not configured)
============================================================""")
    # threaded=False prevents issues with SAM model
    # use_reloader=False prevents double-loading the model
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False, use_reloader=False)
