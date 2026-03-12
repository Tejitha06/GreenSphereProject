#!/usr/bin/env python3
"""
Test script for plant validation endpoint
"""

import requests
import json

BASE_URL = 'http://localhost:5000/api/plants'

def test_validate_plant(plant_name):
    """Test plant validation"""
    url = f'{BASE_URL}/validate'
    payload = {'plant_name': plant_name}
    
    print(f"\nTesting: '{plant_name}'")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get('success') and data.get('data'):
                valid = data['data'].get('valid')
                message = data['data'].get('message')
                print(f"✓ Valid: {valid}")
                print(f"✓ Message: {message}")
            return data.get('data', {}).get('valid', False)
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("Plant Validation Endpoint Test")
    print("=" * 50)
    
    test_cases = [
        ('Rose', True),              # Should be valid
        ('Tomato', True),            # Should be valid
        ('Basil', True),             # Should be valid
        ('Dog', False),              # Should be invalid
        ('Cat', False),              # Should be invalid
        ('Car', False),              # Should be invalid
        ('Rock', False),             # Should be invalid
        ('XYZ123', False),           # Should be invalid
        ('', False),                 # Should be invalid (empty)
        ('A', False),                # Should be invalid (too short)
        ('Monstera', True),          # Should be valid
        ('Snake Plant', True),       # Should be valid
    ]
    
    results = {}
    for plant_name, expected in test_cases:
        result = test_validate_plant(plant_name)
        results[plant_name] = result
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{status} - Expected: {expected}, Got: {result}")
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    passed = sum(1 for plant, _ in test_cases if results[plant] == _[1])
    total = len(test_cases)
    print(f"Passed: {passed}/{total}")
