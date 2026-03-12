"""
Test plant identification endpoint
"""
import requests
import base64
from pathlib import Path

# Test with a sample image
test_image_path = Path(__file__).parent.parent / 'disease pics' / 'Leaf Curl.jfif'

if not test_image_path.exists():
    print(f"Test image not found: {test_image_path}")
    # Try finding any jpg/jpeg file
    import glob
    images = glob.glob('**/*.jpg', recursive=True) + glob.glob('**/*.jpeg', recursive=True) + glob.glob('**/*.jfif', recursive=True)
    if images:
        test_image_path = images[0]
        print(f"Using image: {test_image_path}")
    else:
        print("No test images found!")
        exit(1)

print(f"Testing plant identification with: {test_image_path}")

# Read image
with open(test_image_path, 'rb') as f:
    image_data = f.read()

# Test 1: Send as multipart/form-data
print("\n=== Test 1: Multipart Form Data ===")
try:
    files = {'image': ('test.jpg', image_data, 'image/jpeg')}
    response = requests.post('http://localhost:5000/api/plants/identify', files=files, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Send as base64
print("\n=== Test 2: Base64 JSON ===")
try:
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    payload = {
        'image': f'data:image/jpeg;base64,{image_base64}',
        'filename': 'test.jpg'
    }
    response = requests.post('http://localhost:5000/api/plants/identify/base64', json=payload, timeout=60)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\nTest completed!")
