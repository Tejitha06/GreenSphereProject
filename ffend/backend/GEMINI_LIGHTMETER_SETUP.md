# LightMeter with Gemini API Integration

## What Changed

The LightMeter system has been updated to **use Google Gemini API for determining optimal grayscale values** instead of using hardcoded plant database values. This means the system now:

- **Queries Gemini AI** whenever a plant is identified to fetch its ideal light requirements
- **Gets dynamic, accurate data** instead of relying on static database entries
- **Scales better** - supports any plant species, not just the 20 predefined ones

## How It Works Now

### Old Flow (Hardcoded Database)
```
Plant Identified → Look up in PLANT_DATABASE → Get min/max grayscale → Compare
```

### New Flow (Gemini API)
```
Plant Identified → Query Gemini API → Get min/max grayscale from AI → Compare
```

## Setup Instructions

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Click "Create API Key"
3. Choose your project or create a new one
4. Copy the generated API key

### Step 2: Configure Your API Key

Open `backend.py` and find this line:
```python
GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'  # Replace with your actual Gemini API key
```

Replace `'YOUR_GEMINI_API_KEY_HERE'` with your actual API key:
```python
GEMINI_API_KEY = 'your-actual-api-key-here'
```

⚠️ **Security Note**: Never commit your API key to version control! Consider using environment variables:

```python
import os
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')
```

Then set the environment variable before running:
```bash
# Windows
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY=your-api-key-here

# Then run
python backend.py
```

### Step 3: Verify Installation

Run the validation script:
```bash
python validate_integration.py
```

You should see:
```
✓ Gemini API Key configured
✓ Plant identification functions available
✓ All validations passed!
```

## Functions Overview

### `get_plant_info_from_gemini(plant_name)`
Queries Gemini API for a specific plant's light requirements.

**Parameters:**
- `plant_name` (str): Name of the plant

**Returns:**
```python
{
    'name': 'monstera',
    'data': {
        'min': 80,
        'max': 200,
        'ideal': 'Medium to Bright',
        'is_low_light': False
    },
    'reasoning': 'Monstera is a tropical plant...'
}
```

### `get_plant_info(plant_name)`
Updated function that uses Gemini API. First normalizes plant name using aliases, then queries Gemini.

**Flow:**
1. Clean up plant name (remove qualifiers like "variegated", "dwarf", etc.)
2. Check PLANT_ALIASES for normalized name
3. Query Gemini API for light requirements
4. Return plant info with optimal grayscale range

## Example Query

When a user identifies a "Monstera":

1. **Frontend sends**: Image + "monstera" to backend
2. **Backend calls**: `get_plant_info("monstera")`
3. **Gemini responds**:
   ```json
   {
       "plant_name": "Monstera",
       "min": 80,
       "max": 200,
       "ideal": "Medium to Bright",
       "is_low_light": false,
       "reasoning": "Monstera deliciosa is a tropical plant that prefers bright, indirect light..."
   }
   ```
4. **Backend compares**: Current grayscale (e.g., 120) against Gemini's range (80-200) → "Perfect Light ✓"

## Integration Points

### When Grayscale Values Are Used

1. **Plant Comparison** (`compare_plant_light()`)
   - Compares detected grayscale against Gemini's min/max values
   - Returns status: "🔴 Too Dark", "🟢 Perfect Light", "🔴 Too Bright"

2. **Suggestions** (`generate_suggestions()`)
   - Uses detected light level to generate tips:
     - Low Light (<70): "Move closer to window"
     - Medium Light (70-160): "Perfect conditions"
     - Bright Light (>160): "Filter direct sunlight"

3. **Smart Recommendations**
   - Watering frequency
   - Humidity adjustments
   - Fertilizing schedule
   - Based on detected light level

## Benefits Over Hardcoded Database

| Aspect | Hardcoded DB | Gemini API |
|--------|--------------|-----------|
| Plant Coverage | 20 plants | Unlimited |
| Flexibility | Fixed values | Dynamic AI responses |
| Accuracy | Pre-defined | Current knowledge |
| Updates | Manual code updates | Automatic via AI |
| Reasoning | None | Gemini explains why |

## Troubleshooting

### Issue: "Gemini API error"

**Cause**: Invalid API key or rate limiting

**Fix**:
1. Verify API key is correct in `backend.py`
2. Check [Google AI Studio](https://aistudio.google.com/app/apikeys) that key is active
3. Wait a moment if you've made many requests (rate limit is generous)

### Issue: "Could not parse JSON from Gemini response"

**Cause**: Gemini returned unexpected format

**Fix**:
1. Check console output for full Gemini response
2. Try rephrasing by checking the prompt in `get_plant_info_from_gemini()`
3. Ensure model name `'gemini-pro'` is correct

### Issue: Plant light requirements seem wrong

**Cause**: Gemini may need context clarification

**Fix**: Provide full plant name:
- ❌ "fern" (too generic)
- ✅ "Boston fern" (more specific)

## Caching Recommendation

For production, consider caching Gemini responses to reduce API calls:

```python
PLANT_CACHE = {}

def get_plant_info_from_gemini(plant_name):
    # Check cache first
    if plant_name in PLANT_CACHE:
        return PLANT_CACHE[plant_name]
    
    # ... existing Gemini query code ...
    
    # Cache the result
    PLANT_CACHE[plant_name] = result
    return result
```

## Next Steps

1. ✅ Install google-generativeai (already in requirements.txt)
2. ✅ Add your Gemini API key to `backend.py`
3. ✅ Run `validate_integration.py` to verify
4. ✅ Start the server: `python backend.py`
5. ✅ Test LightMeter at `http://127.0.0.1:5000`

## Questions?

Check these files for more context:
- [backend.py](backend.py) - Main Flask backend
- [PLANT_VALIDATION_API.md](PLANT_VALIDATION_API.md) - Original plant API info
- [GEMINI_SETUP.md](GEMINI_SETUP.md) - Gemini setup details
