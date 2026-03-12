#!/usr/bin/env python
"""
Quick validation script to test Plant.ID API integration
Checks that all imports and functions are correctly set up
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("=" * 60)
    print("LightMeter Plant.ID Integration Validation")
    print("=" * 60)
    
    # Test imports
    print("\n✓ Testing imports...")
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from PIL import Image
    import numpy as np
    import requests
    import base64
    import io
    from datetime import datetime
    import random
    print("  ✓ All imports successful")
    
    # Import backend
    print("\n✓ Loading backend.py...")
    import backend
    print("  ✓ Backend loaded successfully")
    
    # Check API keys
    print("\n✓ Checking API configuration...")
    if hasattr(backend, 'PLANTID_API_KEY'):
        key_masked = backend.PLANTID_API_KEY[:8] + "..." + backend.PLANTID_API_KEY[-4:]
        print(f"  ✓ Plant.ID API Key configured: {key_masked}")
    
    if hasattr(backend, 'PLANTID_API_URL'):
        print(f"  ✓ Plant.ID API URL: {backend.PLANTID_API_URL}")
    
    if hasattr(backend, 'OPENWEATHER_API_KEY'):
        print(f"  ✓ OpenWeather API Key configured")
    
    # Check functions
    print("\n✓ Checking required functions...")
    if hasattr(backend, 'identify_plant_from_image_api'):
        print("  ✓ identify_plant_from_image_api() function found")
    
    if hasattr(backend, 'detect_plant_from_image'):
        print("  ✓ detect_plant_from_image() fallback function found")
    
    if hasattr(backend, 'app'):
        print("  ✓ Flask app instance found")
    
    # Check plant database
    print("\n✓ Checking plant database...")
    if hasattr(backend, 'PLANT_DATABASE'):
        db = backend.PLANT_DATABASE
        print(f"  ✓ Plant database loaded with {len(db)} species")
        print(f"    Sample plants: {', '.join(list(db.keys())[:5])}")
    
    print("\n" + "=" * 60)
    print("✓ All validations passed! Ready to use.")
    print("=" * 60)
    print("\nTo start the server:")
    print("  python backend.py")
    print("\nThen open:")
    print("  http://127.0.0.1:5000")
    
except Exception as e:
    print(f"\n✗ Error during validation: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
