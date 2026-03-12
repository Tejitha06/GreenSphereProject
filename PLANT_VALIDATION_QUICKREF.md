# 🌱 Plant Validation - Quick Reference

## Endpoint

**POST** `/api/plants/validate`

```bash
# Test it
curl -X POST http://localhost:5000/api/plants/validate \
  -H "Content-Type: application/json" \
  -d '{"plant_name": "Tomato"}'
```

## Request
```json
{
  "plant_name": "Rose"
}
```

## Response (Valid)
```json
{
  "success": true,
  "data": {
    "valid": true,
    "message": "Rose is recognized as a valid plant.",
    "suggestions": []
  }
}
```

## Response (Invalid)
```json
{
  "success": true,
  "data": {
    "valid": false,
    "message": "Dog does not appear to be a plant name.",
    "suggestions": []
  }
}
```

## Frontend Usage

```javascript
// In my-garden.html, line ~1083
const response = await fetch('/api/plants/validate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ plant_name: "Rose" })
});

const data = await response.json();
if (data.success && data.data.valid) {
  // Plant is valid, proceed with adding
  addPlantToGarden(email, plantData);
} else {
  // Plant is invalid, show error
  showAlert(`"Rose" is not a valid plant name`, 'warning');
}
```

## Validation Layers

1. **Common Plants** - 150+ hardcoded plant names (< 1ms)
2. **Non-Plant Filter** - Rejects keywords like "dog", "car", "rock" (< 1ms)
3. **Heuristic** - Checks name length ≥2 and has letters (< 1ms)

## Files

| File | Purpose | Location |
|------|---------|----------|
| plant_routes.py | Backend endpoint | routes/plant_routes.py:253-358 |
| my-garden.html | Frontend validation | my-garden.html:1077-1150 |
| test-validation.html | Interactive tests | /test-validation.html |
| test_validate_plant.py | Backend tests | backend/test_validate_plant.py |

## Testing

```bash
# Run backend tests
python backend/test_validate_plant.py

# Open frontend tests in browser
http://localhost:5000/test-validation.html

# Manual test in My Garden page
# Try adding: Rose (✓), Dog (✗), Basil (✓), Car (✗)
```

## Console Logs

Look for `[validatePlantName]` prefix:
```javascript
[validatePlantName] Checking if plant exists: Rose
[validatePlantName] Backend validation response: {...}
[validatePlantName] Result: VALID - Rose is recognized as a valid plant.
```

## Common Plant Names (Sample)

**Flowers:** rose, tulip, lily, daisy, sunflower, lavender, orchid, hibiscus, peony
**Herbs:** basil, mint, rosemary, thyme, oregano, parsley, cilantro, sage
**Vegetables:** tomato, lettuce, spinach, carrot, broccoli, cucumber, pepper
**Houseplants:** monstera, pothos, snake plant, peace lily, spider plant, ficus
**Trees:** oak, maple, birch, pine, cedar, elm, ash
**Fruits:** apple, banana, orange, strawberry, blueberry, grape

**See full list:** `/ffend/backend/routes/plant_routes.py` line 256-281

## Adding New Plants

To add more plants to the database:

1. Edit `/ffend/backend/routes/plant_routes.py`
2. Find `common_plants_list` (line ~256)
3. Add plant name to appropriate category list:
   ```python
   common_plants_list = [
       # Flowers
       'rose', 'tulip', 'lily',
       'new_flower_name',  # ← Add here
       
       # Herbs
       'basil', 'mint',
       'new_herb_name',  # ← Or here
       
       ...
   ]
   ```
4. Also update frontend fallback in `/ffend/my-garden.html` line ~1100

## Blocking Non-Plants

The `non_plant_keywords` list (line ~302 in plant_routes.py) contains:
- Animals: animal, cat, dog, bird, fish, insect, spider
- Objects: car, house, rock, stone, water, plastic, metal, paper, wood, glass, toy, phone, computer, book

To block more non-plants, add keywords to this list.

## Error Handling

- Missing plant_name: HTTP 400 with error message
- Server error: HTTP 500 with error message
- All errors caught and logged
- Frontend falls back to local validation if backend down

## Performance

- Common plant match: < 1ms (in-memory lookup)
- Non-plant keyword check: < 1ms (string matching)
- Heuristic validation: < 1ms (regex)
- Total response: ~100ms with network
- Fallback response: < 5ms (no network)

## Debugging

1. **Check console:**
   ```javascript
   // Open browser DevTools (F12 → Console)
   // Look for [validatePlantName] logs
   ```

2. **Check Flask logs:**
   ```bash
   # Terminal where Flask is running
   # Look for POST /api/plants/validate requests
   ```

3. **Run test suite:**
   ```bash
   python backend/test_validate_plant.py
   ```

4. **Enable verbose logging:**
   ```python
   # In plant_routes.py, change to
   logger.debug(f"Plant validation: {plant_name} → {result}")
   ```

## Integration Example

```javascript
// In handleAddPlant() - my-garden.html
async function handleAddPlant() {
  const name = plantNameInput.value.trim();
  
  // Validate plant name
  const isValidPlant = await validatePlantName(name);
  if (!isValidPlant) {
    showAlert(
      `"${name}" does not appear to be a real plant. ` +
      `Use our Identify Plants feature for accurate plant detection.`,
      'warning'
    );
    return;
  }
  
  // Plant is valid, save it
  const plantData = {
    name: name,
    dateAdded: new Date().toLocaleDateString(),
    watering_schedule: 'Regular watering'
  };
  
  addPlantToGarden(currentUser.email, plantData);
  plantNameInput.value = '';
  showAlert(`Added ${name} to your garden!`, 'success');
}
```

## API Examples

### Valid Plants (3 seconds each)
```bash
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "Rose"}'
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "Basil"}'
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "Tomato"}'
```

### Invalid Plants
```bash
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "Dog"}'
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "Car"}'
curl -X POST http://localhost:5000/api/plants/validate -H "Content-Type: application/json" -d '{"plant_name": "XYZ123"}'
```

## Validation Algorithm

```
Input: plantName

if length(plantName) == 0:
    return INVALID
    
if plantName in COMMON_PLANTS_LIST:
    return VALID
    
if plantName contains any NON_PLANT_KEYWORD:
    return INVALID
    
if length(plantName) >= 2 AND plantName contains letters:
    return VALID (heuristic pass)
    
return INVALID
```

## Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success (check data.valid) | plant validated |
| 400 | Bad request (missing field) | no plant_name provided |
| 500 | Server error | unexpected exception |

## Documentation

| File | Purpose |
|------|---------|
| PLANT_VALIDATION_API.md | Full API reference |
| PLANT_VALIDATION_IMPLEMENTATION.md | Implementation details |
| PLANT_VALIDATION_CHECKLIST.md | Verification checklist |
| PLANT_VALIDATION_SUMMARY.md | Feature summary |
| This file | Quick reference |

## Support

**Having issues?** Check:
1. Flask backend running? `python backend/run.py`
2. Test script passes? `python backend/test_validate_plant.py`
3. Plant name in database? Check `common_plants_list` in plant_routes.py
4. Console logs? Open F12 → Console tab, look for `[validatePlantName]`

**Need to add/modify plants?** Edit line ~256-281 in `plant_routes.py`

**Want to change blocking rules?** Edit line ~302 in `plant_routes.py` (non_plant_keywords)
