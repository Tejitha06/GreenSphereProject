#!/usr/bin/env python
"""
Test script to verify plant name matching works correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backend

def test_plant_matching():
    """Test the plant matching logic with various plant name variations"""
    
    print("\n" + "="*70)
    print("Testing Plant Name Matching Logic")
    print("="*70 + "\n")
    
    # Test cases: (input_name, expected_matched_plant)
    test_cases = [
        # Exact matches
        ("snake plant", "snake plant"),
        ("monstera", "monstera"),
        ("spider plant", "spider plant"),
        
        # Scientific names (from API)
        ("sansevieria", "snake plant"),
        ("sanseviera", "snake plant"),
        ("monstera deliciosa", "monstera"),
        ("ficus lyrata", "fiddle leaf fig"),
        ("spathiphyllum wallisii", "peace lily"),
        ("celadon pothos", "pothos"),
        ("swiss cheese plant", "monstera"),
        ("dypsis lutescens", "areca palm"),
        
        # Common variations
        ("red rubber plant", "rubber plant"),
        ("white peace lily", "peace lily"),
        ("golden pothos", "pothos"),
        ("variegated spider plant", "spider plant"),
        ("dwarf jade plant", "jade plant"),
        
        # Fuzzy matches (similar but not exact)
        ("garden spider plant", "spider plant"),
        ("golden snake plant", "snake plant"),
        ("rubber tree", "rubber plant"),
        
        # With plural
        ("orchids", "orchid"),
        ("succulents", "succulents"),
    ]
    
    print(f"Running {len(test_cases)} test cases:\n")
    
    passed = 0
    failed = 0
    
    for i, (input_name, expected) in enumerate(test_cases, 1):
        result = backend.get_plant_info(input_name)
        
        if result:
            matched_plant = None
            for db_name, data in backend.PLANT_DATABASE.items():
                if data == result['data']:
                    matched_plant = db_name
                    break
            
            success = matched_plant == expected
            status = "✓ PASS" if success else "✗ FAIL"
            
            print(f"{i:2d}. {status}: '{input_name}' → '{matched_plant}' (expected: '{expected}')")
            
            if success:
                passed += 1
            else:
                failed += 1
        else:
            print(f"{i:2d}. ✗ FAIL: '{input_name}' → NO MATCH (expected: '{expected}')")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*70 + "\n")
    
    return failed == 0

def test_grayscale_values():
    """Test that correct grayscale values are returned"""
    
    print("\n" + "="*70)
    print("Testing Grayscale Light Requirements")
    print("="*70 + "\n")
    
    test_plants = [
        "monstera",
        "orchid", 
        "snake plant",
        "aloe vera",
        "peace lily"
    ]
    
    print("Plant grayscale requirements:\n")
    
    for plant in test_plants:
        info = backend.get_plant_info(plant)
        if info:
            data = info['data']
            print(f"  {plant.upper():20} → Min: {data['min']:3d} - Max: {data['max']:3d}  ({data['ideal']})")
    
    print("\n" + "="*70 + "\n")

if __name__ == '__main__':
    success = test_plant_matching()
    test_grayscale_values()
    
    if success:
        print("✓ All plant name matching tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed - see above for details")
        sys.exit(1)
