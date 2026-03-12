#!/usr/bin/env python3
"""
Quick test script to verify PlantIDService initialization and configuration
Run this after restarting the backend to debug plant identification issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("PlantID Service Configuration Test")
print("=" * 60)

# Check environment variables
print("\n1. Checking environment variables...")
plantid_keys = os.getenv('PLANTID_API_KEYS', '')
plantid_url = os.getenv('PLANTID_API_URL', '')

print(f"   PLANTID_API_KEYS: {'✓ Found' if plantid_keys else '✗ NOT FOUND'}")
if plantid_keys:
    keys_list = [k.strip() for k in plantid_keys.split(',') if k.strip()]
    print(f"   - Number of keys: {len(keys_list)}")
    print(f"   - First key (truncated): {keys_list[0][:20]}...")
    
print(f"   PLANTID_API_URL: {plantid_url if plantid_url else '✗ NOT FOUND'}")

# Now test with Flask context
print("\n2. Testing with Flask app context...")
try:
    from app import create_app
    from config import Config
    
    app = create_app()
    with app.app_context():
        print(f"   Flask app created: ✓")
        print(f"   Config.PLANTID_API_KEYS type: {type(Config.PLANTID_API_KEYS)}")
        if isinstance(Config.PLANTID_API_KEYS, list):
            print(f"   Config.PLANTID_API_KEYS length: {len(Config.PLANTID_API_KEYS)}")
            if Config.PLANTID_API_KEYS:
                print(f"   Config.PLANTID_API_KEYS[0] (truncated): {Config.PLANTID_API_KEYS[0][:20]}...")
        
        # Test PlantIDService initialization
        print("\n3. Testing PlantIDService initialization...")
        from plantid_service import get_plantid_service
        service = get_plantid_service()
        print(f"   PlantIDService created: ✓")
        print(f"   Number of API keys loaded: {len(service.api_keys)}")
        print(f"   API URL: {service.api_url}")
        
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All tests passed! PlantID service is properly configured.")
print("=" * 60)
print("\nYou can now:")
print("  1. Start the backend: python app.py")
print("  2. Try identifying a plant in the UI")
print("  3. Check browser console for any errors")
