# 🌱 MY GARDEN - Plant Analysis Implementation Guide

## 🎯 Overview

Your "my garden" feature now includes **AI-powered plant health tracking** using computer vision analysis. This allows users to:

✅ Analyze plant health from photos  
✅ Track growth and health trends over time  
✅ Compare plants in their garden  
✅ Get intelligent care recommendations  
✅ Monitor plant conditions with historical data  

---

## 📦 What's New

### Backend Files Created

1. **`plant_analysis.py`** - Core analysis engine
   - `PlantHealthAnalyzer` - Analyzes images for health metrics
   - `PlantProgressTracker` - Tracks growth over time

2. **Updated `models.py`**
   - New `PlantProgress` model for tracking health history

3. **Updated `garden_routes.py`**
   - 6 new API endpoints for plant analysis

---

## 🚀 Installation & Setup (5 minutes)

### Step 1: Install Required Package

```bash
# Your existing requirements.txt likely has these, but ensure:
pip install opencv-python numpy

# Full list needed:
pip install flask flask-sqlalchemy opencv-python numpy
```

### Step 2: Update Database

```bash
# Run migrations or restart Flask app to create PlantProgress table
# The model will auto-create the table on first run
```

### Step 3: Test the API

```bash
# Health check
curl http://localhost:5000/garden/health
```

---

## 📡 API Endpoints

### 1️⃣ Analyze Plant Image

**Endpoint**: `POST /garden/<plant_id>/analyze`

**Purpose**: Analyze a plant photo and save health metrics

**Request**:
```json
{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAA...",
    "image_filename": "plant_photo_001.jpg",
    "notes": "Plant looks droopy today"
}
```

**Response**:
```json
{
    "success": true,
    "message": "Plant analyzed successfully",
    "data": {
        "analysis": {
            "timestamp": "2026-03-07T10:30:45.123Z",
            "health": {
                "score": 78.5,
                "status": "good",
                "green_percentage": 65.2,
                "yellowing_detected": 8.3,
                "vibrancy": 72.1
            },
            "leaf_metrics": {
                "estimated_leaf_count": 14,
                "foliage_coverage": 62.5,
                "leaf_density": "dense"
            },
            "color_analysis": {
                "dominant_colors": [
                    {"rgb": [76, 175, 80], "percentage": 45.2},
                    {"rgb": [200, 180, 100], "percentage": 28.1}
                ]
            },
            "recommendations": [
                "✅ Plant looks healthy - maintain current care",
                "📊 Continue monitoring plant growth"
            ]
        },
        "progress_record": {
            "id": 42,
            "health_score": 78.5,
            "recorded_at": "2026-03-07T10:30:45.123Z"
        }
    }
}
```

---

### 2️⃣ Get Plant Progress History

**Endpoint**: `GET /garden/<plant_id>/progress?limit=10&offset=0`

**Purpose**: Retrieve health history with trend analysis

**Response**:
```json
{
    "success": true,
    "data": {
        "plant_name": "Monstera Deliciosa",
        "progress_records": [
            {
                "id": 42,
                "health_score": 78.5,
                "health_status": "good",
                "recorded_at": "2026-03-07T10:30:45Z",
                "green_percentage": 65.2,
                "leaf_density": "dense",
                "notes": "Plant looks droopy today"
            }
        ],
        "total": 15,
        "trend": {
            "trend": "improving",
            "trend_percentage": 12.5,
            "health_improvement": 8.3,
            "measurements": 15
        }
    }
}
```

**Trend values**: `improving`, `declining`, `stable`

---

### 3️⃣ Compare All User Plants

**Endpoint**: `GET /garden/user/<user_id>/comparison`

**Purpose**: Rank plants and identify which needs attention

**Response**:
```json
{
    "success": true,
    "data": {
        "total_plants": 5,
        "average_health": 72.4,
        "healthiest": {
            "id": 12,
            "plant_name": "Pothos",
            "health_score": 90.2
        },
        "needs_attention": {
            "id": 8,
            "plant_name": "Succulents",
            "health_score": 45.1
        },
        "ranking": [
            {"rank": 1, "name": "Pothos", "health_score": 90.2},
            {"rank": 2, "name": "Monstera", "health_score": 78.5},
            {"rank": 3, "name": "Snake Plant", "health_score": 65.0},
            {"rank": 4, "name": "Peace Lily", "health_score": 58.3},
            {"rank": 5, "name": "Succulents", "health_score": 45.1}
        ]
    }
}
```

---

### 4️⃣ Get Care Recommendations

**Endpoint**: `GET /garden/<plant_id>/recommendations`

**Purpose**: AI-powered care advice based on latest analysis

**Response**:
```json
{
    "success": true,
    "data": {
        "health_score": 78.5,
        "health_status": "good",
        "recommendations": [
            "✅ Plant looks healthy - maintain current care",
            "💧 Yellow leaves detected - may indicate nutrient deficiency"
        ],
        "care_info": {
            "watering": "Water when soil is dry, 2-3 times per week",
            "sunlight": "6-8 hours of indirect bright light",
            "soil": "Well-draining potting soil",
            "humidity": "50-70% relative humidity",
            "temperature": "18-25°C (65-77°F)",
            "fertilizer": "Monthly during growing season"
        },
        "latest_analysis": {
            "recorded_at": "2026-03-07T10:30:45Z",
            "green_percentage": 65.2,
            "yellowing_percentage": 8.3,
            "leaf_density": "dense"
        }
    }
}
```

---

### 5️⃣ Get Garden Health Summary

**Endpoint**: `GET /garden/user/<user_id>/garden-health-summary`

**Purpose**: Overview of entire garden status

**Response**:
```json
{
    "success": true,
    "data": {
        "total_plants": 5,
        "average_health_score": 72.4,
        "garden_status": "good",
        "health_breakdown": {
            "excellent": 1,
            "good": 2,
            "fair": 1,
            "poor": 1,
            "critical": 0,
            "unanalyzed": 0
        },
        "needs_attention": 1
    }
}
```

**Garden status values**: `thriving`, `good`, `needs_attention`, `critical`

---

## 🎨 Frontend Integration

### Example: Add Analysis Button to Plant Card

```html
<!-- In my-garden.html -->
<button class="btn btn-primary" onclick="analyzePlant(plantId)">
    📸 Analyze Health
</button>
```

### JavaScript Handler

```javascript
async function analyzePlant(plantId) {
    // Get image from camera or upload
    const imageBase64 = await getImageFromUser();
    
    if (!imageBase64) return;
    
    const response = await fetch(`/garden/${plantId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            image_base64: imageBase64,
            image_filename: 'plant_photo.jpg',
            notes: 'Regular check-in'
        })
    });
    
    const result = await response.json();
    
    if (result.success) {
        const analysis = result.data.analysis;
        displayHealthScore(analysis.health.score);
        showRecommendations(analysis.recommendations);
    }
}

function displayHealthScore(score) {
    const status = score > 80 ? 'Excellent' :
                   score > 60 ? 'Good' :
                   score > 40 ? 'Fair' :
                   score > 20 ? 'Poor' : 'Critical';
    
    document.getElementById('healthStatus').innerHTML = `
        <div class="health-badge ${status.toLowerCase()}">
            #{status}: {score.toFixed(1)}/100
        </div>
    `;
}
```

---

## 📊 Health Score Calculation

The health score (0-100) is based on:

| Factor | Weight | What it Measures |
|--------|--------|------------------|
| **Green Content** | 40% | Amount of green pixels (healthy foliage) |
| **Vibrancy** | 30% | Color intensity and saturation |
| **Yellowing** | 30% | Brown/yellow discoloration (negative) |

**Score Ranges**:
- 🟢 **80-100**: Excellent
- 🟡 **60-80**: Good
- 🟠 **40-60**: Fair
- 🔴 **20-40**: Poor
- ⚫ **0-20**: Critical

---

## 💾 Database Schema

### PlantProgress Table

```sql
CREATE TABLE plant_progress (
    id INTEGER PRIMARY KEY,
    garden_plant_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    
    -- Health metrics
    health_score FLOAT,           -- 0-100
    health_status VARCHAR(50),    -- excellent, good, fair, poor, critical
    green_percentage FLOAT,
    yellowing_percentage FLOAT,
    vibrancy_score FLOAT,
    
    -- Size metrics
    height_pixels INTEGER,
    width_pixels INTEGER,
    area_pixels INTEGER,
    height_cm FLOAT,              -- For future calibration
    width_cm FLOAT,
    area_cm2 FLOAT,
    
    -- Leaf metrics
    estimated_leaf_count INTEGER,
    foliage_coverage FLOAT,       -- Percentage
    leaf_density VARCHAR(50),     -- sparse, moderate, dense
    
    -- Media & analysis
    image_data BLOB,
    image_filename VARCHAR(255),
    analysis_data TEXT,           -- Full JSON analysis
    
    -- Metadata
    recorded_at DATETIME,
    notes TEXT,
    
    FOREIGN KEY (garden_plant_id) REFERENCES garden_plants(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🔄 Complete Workflow

### For End Users:

1. **Add Plant to Garden**
   ```
   User takes plant photo → Uses Plant.id to identify → Saves to "My Garden"
   ```

2. **Analyze Plant Health** (Weekly/Monthly)
   ```
   User takes new photo → System analyzes → Shows health score & recommendations
   ```

3. **Track Growth Over Time**
   ```
   Week 1: Health: 65 → Week 2: Health: 72 → Week 3: Health: 80
   Result: "Improving +15% ✅"
   ```

4. **Compare & Compete** (Optional Gamification)
   ```
   "Your Monstera is healthier than 78% of other plants!"
   ```

---

## 🛠️ Advanced Features (Optional Additions)

### 1. Add Photo with Reference Object (For Real Measurements)

```python
# Future enhancement: Detect coins/reference objects for actual cm measurements
def detect_reference_object(image):
    """Detect US quarter (24mm) or other reference in image"""
    pass
```

### 2. AI Insights Agent Integration

```python
# Connect with your n8n agent
def get_ai_recommendations(plant_data):
    """
    Send plant data to AI agent for advanced insights
    - Pest/disease detection
    - Nutrient deficiency analysis
    - Custom care plans
    """
```

### 3. Growth Timeline Visualization

```javascript
// Show plant growth over time with charts
function displayGrowthChart(progressHistory) {
    const dates = progressHistory.map(r => r.recorded_at);
    const scores = progressHistory.map(r => r.health_score);
    // Use Chart.js to visualize
}
```

---

## 🐛 Troubleshooting

### Issue: "Image analysis returns low scores"
- **Cause**: Poor lighting or plant not in focus
- **Solution**: Ensure good natural lighting, fill 60% of frame with plant

### Issue: "Leaf count seems inaccurate"
- **Cause**: Complex leaves or overlapping foliage
- **Solution**: This is an estimate; users should provide manual count via notes

### Issue: "OpenCV errors on Linux"
- **Cause**: Missing system libraries
- **Solution**: 
  ```bash
  sudo apt-get install libopencv-dev python3-opencv
  ```

---

## 📝 Example Usage

### Complete Flow: Add Plant & Analyze

```javascript
// Step 1: Add plant to garden (existing)
await addPlantToGarden({
    user_id: 1,
    plant_name: "Monstera Deliciosa",
    scientific_name: "Monstera deliciosa",
    image_base64: cameraImage,
    watering_capacity: "Water when soil is dry"
});

// Step 2: Take analysis photo
const analysisImage = await getPhotoFromCamera();

// Step 3: Analyze
const analysis = await analyzeGardenPlant(plantId, analysisImage);

// Step 4: Display results
console.log(analysis.health.score);           // 78.5
console.log(analysis.leaf_metrics);           // { "estimated_leaf_count": 14 }
console.log(analysis.recommendations);        // ["✅ Plant looks healthy"]

// Step 5: Get history
const history = await getPlantProgress(plantId);
console.log(history.trend);                   // { "trend": "improving", "trend_percentage": 12.5 }

// Step 6: Compare with other plants
const comparison = await compareUserPlants(userId);
console.log(comparison.ranking);              // [{ rank: 1, name: "Pothos", ... }]
```

---

## 📚 Next Steps

1. **Update UI** - Add analysis buttons to plant cards
2. **Add Camera** - Integrate device camera for photos
3. **Create Dashboard** - Show garden health overview
4. **Gamification** - Leaderboards and achievements
5. **AI Agent** - Connect to n8n for advanced insights
6. **Alerts** - Notify when plants need attention

---

## ✅ Feature Checklist

- [x] Plant health scoring from images
- [x] Health status classification
- [x] Leaf count estimation
- [x] Progress tracking over time
- [x] Growth trend calculation
- [x] Plant comparison & ranking
- [x] Care recommendations
- [x] Garden health summary
- [ ] Photo storage with compres
- [ ] Growth timeline charts
- [ ] Reference object calibration
- [ ] Disease detection
- [ ] Pest identification
- [ ] AI agent integration

---

## 🎓 Health Metrics Explained

### Green Percentage
- **Meaning**: Amount of plant foliage that is healthy green
- **Good Range**: 50-80%
- **Indicates**: Overall leaf health

### Yellowing Detected
- **Meaning**: Brown/yellow discoloration percentage
- **Good Range**: 0-15%
- **Indicates**: Nutrient deficiency or watering issues

### Vibrancy Score
- **Meaning**: Color intensity and saturation (0-100)
- **Good Range**: 60-100
- **Indicates**: Plant vibrancy and health

### Foliage Coverage
- **Meaning**: Percentage of image covered by plant foliage
- **Good Range**: 40-80% (depends on plant)
- **Indicates**: Plant size and bushiness

### Leaf Density
- **Categories**: Sparse, Moderate, Dense
- **Meaning**: How densely packed the leaves are
- **Indicates**: Plant growth and bushiness level

---

## 🔗 Integration Points

This plant analysis system integrates with:

1. **Garden Routes** (`/garden/`)
2. **Existing GardenPlant Model**
3. **Plant.id API** (for identification)
4. **N8N Agent** (for AI insights) - coming soon
5. **Email Alerts** (when plants need attention) - optional

---

Questions? Check the existing implementation files:
- `plant_analysis.py` - Core analysis logic
- `models.py` - PlantProgress model
- `garden_routes.py` - API endpoints
