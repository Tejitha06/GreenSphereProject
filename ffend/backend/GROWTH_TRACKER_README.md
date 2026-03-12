# Plant Growth Tracking System

A unified, efficient plant growth tracking system integrating multiple technologies for comprehensive plant analysis.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PlantGrowthTracker                           │
│                    (Main Orchestrator)                          │
├──────────────────┬──────────────────┬──────────────────┬───────┤
│  RembgSegmenter  │  PlantCVAnalyzer │   PlantIDClient  │Gemini │
│  (Fast BG Remove)│  (Measurements)  │   (Species ID)   │Report │
├──────────────────┼──────────────────┼──────────────────┼───────┤
│  ✓ U2Net model   │  ✓ PlantCV lib   │  ✓ Plant.id API  │✓ AI   │
│  ✓ Color fallback│  ✓ OpenCV backup │  ✓ Key rotation  │Reports│
└──────────────────┴──────────────────┴──────────────────┴───────┘
```

## Features

### 1. Rembg Segmentation (Background Removal)
- **Primary**: Uses U2Net neural network for precise plant extraction
- **Fallback**: Color-based HSV segmentation when Rembg unavailable
- **Alpha matting**: Smooth edges on complex foliage

### 2. PlantCV Measurements (Scientific Analysis)
- **Primary**: PlantCV library for research-grade measurements
- **Fallback**: OpenCV-based analysis
- **Metrics**:
  - Height, width, area, perimeter
  - Leaf count estimation (watershed + distance transform)
  - Greenness index
  - Health score (0-100)
  - Color histogram analysis
  - Solidity, convex hull, aspect ratio

### 3. Plant.id Integration (Species Identification)
- Automatic species identification
- Confidence scoring
- Care information extraction
- Dual API key support with automatic failover

### 4. Gemini AI Reports (Intelligent Analysis)
- AI-generated health summaries
- Personalized care recommendations
- Growth forecasting
- Issue detection
- Template fallback when API unavailable

## API Endpoints

### Full Analysis
```http
POST /api/growth/analyze
Content-Type: multipart/form-data

image: <file>
plant_name: "My Plant" (optional)
pixels_per_cm: 10.5 (optional - for real measurements)
skip_species: false (optional)
skip_ai: false (optional)
```

### Quick Health Check (No API Calls)
```http
POST /api/growth/quick-check
Content-Type: multipart/form-data

image: <file>
```

### Compare Two Images
```http
POST /api/growth/compare
Content-Type: application/json

{
    "current_image": "base64...",
    "previous_image": "base64...",
    "plant_name": "optional"
}
```

### Track Plant Over Time
```http
POST /api/growth/track/<plant_id>
Content-Type: multipart/form-data

image: <file>
```

### Get Growth History
```http
GET /api/growth/history/<plant_id>?limit=20&offset=0
```

### Check System Status
```http
GET /api/growth/status
```

## Response Example

```json
{
    "success": true,
    "data": {
        "timestamp": "2026-03-09T10:30:00Z",
        "health_score": 85.5,
        "greenness_index": 0.72,
        "measurements": {
            "height_px": 450,
            "width_px": 320,
            "area_px": 98500,
            "leaf_count_estimate": 12,
            "advanced_metrics": {
                "solidity": 0.85,
                "aspect_ratio": 1.4
            }
        },
        "species": {
            "name": "Monstera deliciosa",
            "confidence": 0.95,
            "care_info": {
                "watering": "moderate",
                "sunlight": "indirect"
            }
        },
        "ai_summary": "Your Monstera is thriving with excellent health...",
        "ai_recommendations": [
            "Continue current watering schedule",
            "Consider fertilizing next month"
        ],
        "processing_time_ms": 1234,
        "components_used": ["rembg", "plantcv", "plant.id", "gemini"]
    }
}
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages:
# - rembg>=2.0.50 (background removal)
# - plantcv>=4.0.0 (plant analysis)
# - opencv-python>=4.8.0 (image processing)
# - onnxruntime>=1.16.0 (model inference)
```

## Configuration

### Environment Variables
```env
# Plant.id API (species identification)
PLANTID_API_KEY=your_key_here
PLANTID_API_KEY_BACKUP=backup_key_here
PLANTID_API_URL=https://plant.id/api/v3

# Gemini API (AI reports)
GEMINI_API_KEYS=key1,key2,key3
```

## Python Usage

```python
from plant_growth_tracker import PlantGrowthTracker, analyze_plant, quick_health_check

# Full analysis
tracker = PlantGrowthTracker(
    pixels_per_cm=10.0,  # Optional: for real-world measurements
    enable_species_id=True,
    enable_ai_reports=True
)

report = tracker.analyze(
    image="path/to/plant.jpg",
    plant_name="My Monstera"
)

print(f"Health: {report.measurements.health_score}/100")
print(f"Species: {report.species.name}")
print(f"AI Summary: {report.ai_summary}")

# Quick functions
result = quick_health_check("plant.jpg")
print(f"Quick health: {result['health_score']}")

# One-shot analysis
data = analyze_plant("plant.jpg", plant_name="Fern")
```

## Efficiency Features

1. **Lazy Loading**: Components only initialize when first used
2. **Singleton Pattern**: Single tracker instance reused across requests
3. **Caching**: Results cached by image hash
4. **Graceful Degradation**: Falls back to simpler methods when advanced features unavailable
5. **Key Rotation**: API keys automatically rotated on failure
6. **Parallel Ready**: Independent components can run in parallel

## Error Handling

All components have comprehensive error handling:
- Network errors → retry with backup keys
- Missing dependencies → fallback to simpler algorithms
- Invalid images → clear error messages
- API failures → template-based fallback responses

## File Structure

```
backend/
├── plant_growth_tracker.py    # Main unified tracking system
├── routes/
│   └── growth_routes.py       # API endpoints
├── requirements.txt           # Updated with rembg, plantcv
└── app.py                     # Blueprint registration
```
