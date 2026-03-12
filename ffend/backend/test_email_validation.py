#!/usr/bin/env python3
"""Test email validation for registration"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

# Test cases
test_cases = [
    # Valid emails
    {'email': 'john@gmail.com', 'should_pass': True, 'description': 'Valid Gmail'},
    {'email': 'user@company.com', 'should_pass': True, 'description': 'Valid company email'},
    {'email': 'alice.smith@university.edu', 'should_pass': True, 'description': 'Valid university email'},
    {'email': 'john.doe123@outlook.com', 'should_pass': True, 'description': 'Valid Outlook email'},
    
    # Invalid/Fake emails
    {'email': 'test@test.com', 'should_pass': False, 'description': 'Fake: test@test.com'},
    {'email': 'abc@abc.com', 'should_pass': False, 'description': 'Fake: abc@abc.com'},
    {'email': 'demo@demo.org', 'should_pass': False, 'description': 'Fake: demo@demo.org'},
    {'email': 'temp@temporary.com', 'should_pass': False, 'description': 'Fake: temp@temporary.com'},
    {'email': 'fake@fake.com', 'should_pass': False, 'description': 'Fake: fake@fake.com'},
    {'email': 'test123@test.com', 'should_pass': False, 'description': 'Fake: test123@test.com'},
    {'email': 'aaaa@aaa.com', 'should_pass': False, 'description': 'Fake: aaaa@aaa.com'},
    {'email': 'user@mailinator.com', 'should_pass': False, 'description': 'Fake: Mailinator domain'},
    {'email': 'test@10minutemail.com', 'should_pass': False, 'description': 'Fake: 10 minute mail'},
]

print("=" * 70)
print("EMAIL VALIDATION TEST SUITE")
print("=" * 70)

passed = 0
failed = 0

for test in test_cases:
    email = test['email']
    should_pass = test['should_pass']
    description = test['description']
    
    # Send registration request
    response = requests.post(
        f'{BASE_URL}/auth/register',
        json={
            'name': 'Test User',
            'email': email,
            'phone': '1234567890',
            'password': 'TestPass123'
        }
    )
    
    result = response.json()
    is_success = result.get('success', False)
    
    # Check if test passed
    if should_pass:
        if is_success or response.status_code == 409:  # 409 means email already registered (still valid email format)
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            print(f"{status} | {description}")
            print(f"       Email: {email}")
            print(f"       Expected: Should accept | Got: {result.get('message')}")
    else:
        if not is_success and response.status_code != 409:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            print(f"{status} | {description}")
            print(f"       Email: {email}")
            print(f"       Expected: Should reject | Got: Success={is_success}")

print("\n" + "=" * 70)
print(f"Results: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("✅ All email validation tests passed!")
else:
    print(f"❌ {failed} test(s) failed")
