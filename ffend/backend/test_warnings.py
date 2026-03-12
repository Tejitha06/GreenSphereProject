#!/usr/bin/env python
"""
Test the warning display behavior
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backend

print("\n" + "="*70)
print("Testing Warning Display Behavior")
print("="*70 + "\n")

# Test different light conditions
test_cases = [
    ("Low Light", "Too dark - should show warning"),
    ("Medium Light", "Ideal - should NOT show warning"),
    ("Bright Light", "Too bright - should show warning"),
]

for light_level, description in test_cases:
    suggestion_data = backend.generate_suggestions(light_level, 50, "Test Location")
    has_warning = bool(suggestion_data['warning'])
    
    print(f"Light Level: {light_level}")
    print(f"  Description: {description}")
    print(f"  Warning Message: '{suggestion_data['warning']}'")
    print(f"  Has Warning: {has_warning}")
    print(f"  Display Box: {'✓ YES' if has_warning else '✗ NO'}")
    print()

print("="*70)
print("\nExpected behavior:")
print("  ✓ Low Light → Warning shown (problem)")
print("  ✗ Medium Light → Warning hidden (ideal)")
print("  ✓ Bright Light → Warning shown (problem)")
print("="*70 + "\n")
