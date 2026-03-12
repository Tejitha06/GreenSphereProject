#!/usr/bin/env python3
"""Test garden plant save and retrieval"""
import requests
import json
import base64
from pathlib import Path

BASE_URL = 'http://localhost:5000/api'

# Test data
TEST_USER_ID = 1  # Assuming a user exists with ID 1
TEST_PLANT_DATA = {
    'user_id': TEST_USER_ID,
    'plant_name': 'Test Plant',
    'scientific_name': 'Plantus testicus',
    'watering_capacity': 'Weekly',
    'soil_type': 'Well-draining soil',
    'sunlight_requirements': 'Bright indirect light',
    'temperature_range': '18-25°C',
    'humidity_level': 'Moderate',
    'fertilizer_needs': 'Monthly',
    'plant_info': json.dumps({
        'description': 'Test plant',
        'toxicity': 'safe',
        'confidence': 95
    })
}

def test_save_garden_plant():
    """Test saving a plant to garden"""
    print("=" * 60)
    print("TEST 1: Save Garden Plant")
    print("=" * 60)
    
    response = requests.post(
        f'{BASE_URL}/garden/garden/save',
        json=TEST_PLANT_DATA,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.json() if response.status_code in [200, 201] else None

def test_fetch_user_gardens(user_id):
    """Test fetching all plants for a user"""
    print("\n" + "=" * 60)
    print("TEST 2: Fetch User's Garden Plants")
    print("=" * 60)
    
    response = requests.get(
        f'{BASE_URL}/garden/garden/user/{user_id}?limit=100'
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if result.get('success') and result.get('data'):
        print(f"\nTotal plants found: {len(result['data'])}")
        for i, plant in enumerate(result['data'], 1):
            print(f"{i}. {plant['plant_name']} ({plant['scientific_name']})")
    
    return result

def main():
    print("\n🌿 GARDEN PLANT TEST SUITE\n")
    
    # Test 1: Save a plant
    result = test_save_garden_plant()
    
    if result:
        print("\n✅ Plant saved successfully!")
    else:
        print("\n❌ Failed to save plant")
        return
    
    # Test 2: Fetch all user plants
    result = test_fetch_user_gardens(TEST_USER_ID)
    
    if result.get('success'):
        print("\n✅ Successfully fetched user's garden plants!")
    else:
        print("\n❌ Failed to fetch garden plants")

if __name__ == '__main__':
    main()
