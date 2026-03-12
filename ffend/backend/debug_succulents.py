#!/usr/bin/env python
"""Debug test for succulents matching"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backend

# Test succulents specifically
print("Testing 'succulents' plant matching:\n")

# Check if succulents is in database
print(f"'succulents' in PLANT_DATABASE: {'succulents' in backend.PLANT_DATABASE}")
print(f"PLANT_DATABASE['succulents']: {backend.PLANT_DATABASE.get('succulents')}\n")

# Check aliases
print(f"'succulents' in PLANT_ALIASES: {'succulents' in backend.PLANT_ALIASES}\n")

# Test get_plant_info
print("Calling get_plant_info('succulents'):")
result = backend.get_plant_info('succulents')
print(f"Result: {result}\n")

# Check if it matches aloe vera by mistake
if result:
    print(f"Returned data: {result['data']}")
    aloe_data = backend.PLANT_DATABASE.get('aloe vera')
    succulents_data = backend.PLANT_DATABASE.get('succulents')
    print(f"Aloe vera data: {aloe_data}")
    print(f"Same as aloe vera? {result['data'] == aloe_data}")
    print(f"Same as succulents? {result['data'] == succulents_data}")
