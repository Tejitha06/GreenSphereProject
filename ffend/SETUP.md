# GreenSphere Flask Backend - Complete Setup Guide

A complete Flask backend for plant identification and disease detection using **PlantID v3 API**.

## 🎯 What's Included

✅ **Flask Backend** - RESTful API server
✅ **Plant Identification** - Identify plants from images with 95%+ accuracy
✅ **Disease Detection** - Detect plant diseases with severity levels
✅ **CORS Enabled** - Works with frontend from any origin
✅ **Error Handling** - Comprehensive error handling and logging
✅ **Base64 Support** - Accept images as base64 (webcam ready)
✅ **Detailed Responses** - Rich data about plants, diseases, treatments

## 📋 Requirements

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **PlantID v3 API Key** - [Get free key](https://plant.id/)
- **Internet Connection** - For API calls
- **~500MB** - Disk space for dependencies

## 🚀 Quick Start (Windows)

### Step 1: Run Setup Script
```bash
cd backend
setup.bat
```
This will:
- Create virtual environment
- Install all dependencies
- Create `.env` file (you'll need to edit it)

### Step 2: Configure PlantID API Key
1. Get free API key from [plant.id](https://plant.id/)
2. Edit `backend/.env`:
   ```
   PLANTID_API_KEY=your_api_key_here
   ```

### Step 3: Start Backend
```bash
cd backend
venv\Scripts\activate
python run.py
```

You should see:
```
╔════════════════════════════════════════════════════╗
║       GreenSphere Backend Started                  ║
║                                                    ║
║  API Server: http://localhost:5000                ║
║  Health Check: http://localhost:5000/api/health   ║
║                                                    ║
║  Plant Identification: POST /api/plants/identify  ║
║  Disease Detection: POST /api/diseases/detect     ║
║                                                    ║
║  Press CTRL+C to stop the server                  ║
╚════════════════════════════════════════════════════╝
```

## 🚀 Quick Start (Mac/Linux)

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API key
nano .env  # or use your favorite editor

# Run the server
python run.py
```

## 📡 API Endpoints

### 1. Health Check
```
GET /api/health
```
Test if backend is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "GreenSphere API",
  "version": "1.0.0"
}
```

### 2. Plant Identification
```
POST /api/plants/identify
Content-Type: multipart/form-data

Form Data:
  image: <binary image file>
```

**Supported Formats:** PNG, JPG, JPEG, GIF, WebP (max 10MB)

**Response:**
```json
{
  "success": true,
  "data": {
    "confidence": 95.5,
    "name": "Monstera",
    "scientific": "Monstera deliciosa",
    "common_names": ["Swiss Cheese Plant"],
    "description": "...",
    "purposes": ["Decorative", "Air Purification"],
    "suitability": "Great for adding tropical vibes...",
    "soil": "Well-draining potting mix...",
    "water": "Water when top 2-3 inches of soil are dry...",
    "climate": "Temperature: 18-27°C...",
    "toxicity": "toxic",
    "toxicityInfo": "Toxic to pets and humans...",
    "medical": "Helps humidify air..."
  },
  "timestamp": "2024-01-26T10:30:00.000000"
}
```

### 3. Disease Detection
```
POST /api/diseases/detect
Content-Type: multipart/form-data

Form Data:
  image: <binary image file>
```

**Response (Disease Detected):**
```json
{
  "success": true,
  "data": {
    "isHealthy": false,
    "title": "Powdery Mildew",
    "probability": 85.5,
    "description": "Fungal disease causing white dusty coating...",
    "severity": "Moderate",
    "causes": ["High humidity", "Poor air circulation"],
    "symptoms": ["White dusty coating", "Leaf curling"],
    "homeRemedies": ["Remove infected leaves", "Apply baking soda spray"],
    "fertilizer": ["Use potassium-based fertilizers"],
    "pesticide": ["Apply copper-based fungicide"],
    "prevention": ["Water at base of plant", "Improve air flow"]
  }
}
```

**Response (Plant Healthy):**
```json
{
  "success": true,
  "data": {
    "isHealthy": true,
    "message": "Plant appears healthy",
    "confidence": 100
  }
}
```

### 4. Plant Identification (Base64)
```
POST /api/plants/identify/base64
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "filename": "plant.jpg"
}
```

### 5. Disease Detection (Base64)
```
POST /api/diseases/detect/base64
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "filename": "plant.jpg"
}
```

## 🔗 Frontend Integration

### Add API Client Script
Add to your HTML:
```html
<script src="api-client.js"></script>
```

### JavaScript Usage

#### Identify Plant
```javascript
const fileInput = document.getElementById('imageInput');
const file = fileInput.files[0];

try {
  const result = await greensphereAPI.identifyPlantFromFile(file);
  
  if (result.success) {
    console.log('Plant:', result.data.name);
    console.log('Confidence:', result.data.confidence);
    console.log('Care Info:', result.data.water);
  }
} catch (error) {
  console.error('Error:', error.message);
}
```

#### Detect Disease
```javascript
const fileInput = document.getElementById('imageInput');
const file = fileInput.files[0];

try {
  const result = await greensphereAPI.detectDiseaseFromFile(file);
  
  if (result.success) {
    if (result.data.isHealthy) {
      console.log('Plant is healthy!');
    } else {
      console.log('Disease:', result.data.title);
      console.log('Severity:', result.data.severity);
      console.log('Treatment:', result.data.homeRemedies);
    }
  }
} catch (error) {
  console.error('Error:', error.message);
}
```

#### Health Check
```javascript
const health = await greensphereAPI.getHealth();
console.log('API Status:', health.status); // 'healthy'
```

## 📁 Project Structure

```
ffend/
├── index.html
├── identify.html
├── disease.html
├── api-client.js                 ← Add to HTML
├── identify-integration.js        ← Add to HTML
├── disease-integration.js         ← Add to HTML
├── INTEGRATION_GUIDE.html
├── SETUP.md                       ← This file
│
└── backend/
    ├── app.py                     ← Main Flask app
    ├── config.py                  ← Configuration
    ├── plantid_service.py         ← PlantID API integration
    ├── run.py                     ← Entry point
    ├── setup.bat                  ← Windows setup script
    ├── requirements.txt
    ├── .env.example
    ├── .env                       ← Your config (not in git)
    ├── README.md
    │
    └── routes/
        ├── __init__.py
        ├── health_routes.py
        ├── plant_routes.py
        └── disease_routes.py
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# PlantID API Configuration
PLANTID_API_KEY=your_key_here
PLANTID_API_URL=https://api.plant.id/v3

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5000,http://localhost:3000
```

### Get PlantID API Key

1. Visit [plant.id](https://plant.id/)
2. Click "Sign Up" or "Get API Key"
3. Create free account
4. Go to Dashboard
5. Copy your API key
6. Add to `.env` file

## 🧪 Testing

### Test with cURL

```bash
# Test health
curl http://localhost:5000/api/health

# Test plant identification
curl -X POST -F "image=@test_plant.jpg" http://localhost:5000/api/plants/identify

# Test disease detection
curl -X POST -F "image=@test_plant.jpg" http://localhost:5000/api/diseases/detect
```

### Test with Postman

1. Create new POST request
2. URL: `http://localhost:5000/api/plants/identify`
3. Body → form-data → Add key "image" (type: File)
4. Select image file
5. Send

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError"
```
Solution: Activate virtual environment and install requirements
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Error: "PlantID API key is not configured"
```
Solution: 
1. Check .env file exists
2. Add: PLANTID_API_KEY=your_key
3. Restart server
```

### Error: CORS error in browser
```
Solution:
1. Check backend is running
2. Check CORS_ALLOWED_ORIGINS in .env
3. Include your frontend URL
CORS_ALLOWED_ORIGINS=http://localhost:5000,http://yoursite.com
```

### Error: 500 Internal Server Error
```
Solution:
1. Check Flask console for error message
2. Verify image file format
3. Check PlantID API key is valid
4. Try different image with better lighting
```

### Error: Request timeout
```
Solution:
1. Check internet connection
2. Try with smaller image (< 5MB)
3. Check PlantID API is accessible
4. Increase timeout in api-client.js
```

## 📊 Response Format

All API responses follow this format:

**Success Response:**
```json
{
  "success": true,
  "data": { /* response data */ },
  "timestamp": "ISO-8601 timestamp"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error Type",
  "message": "Human readable error message",
  "timestamp": "ISO-8601 timestamp"
}
```

## 🔐 Security Notes

- ✅ CORS is configured for frontend origins
- ✅ File upload size limited to 10MB
- ✅ Only image files allowed
- ✅ API key not exposed to frontend
- ⚠️ Keep `.env` file private (never commit to git)
- ⚠️ Use HTTPS in production

## 📈 Performance

- **Identification**: 2-5 seconds (depends on image and API)
- **Disease Detection**: 2-5 seconds
- **Throughput**: Handles multiple concurrent requests
- **Scalability**: Can be deployed with Gunicorn/uWSGI for production

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Using Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

### Environment for Production
```bash
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=random_secure_key
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

## 📞 Support

- **PlantID API Issues**: [PlantID Support](https://plant.id/support)
- **Flask Issues**: [Flask Documentation](https://flask.palletsprojects.com/)
- **Python Issues**: [Python Documentation](https://docs.python.org/)

## 📄 License

This project is part of GreenSphere.

## ✅ Checklist

- [ ] Python 3.8+ installed
- [ ] Backend directory exists
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] PlantID API key obtained
- [ ] `.env` file created with API key
- [ ] Backend starts without errors
- [ ] Health check endpoint responds
- [ ] Frontend files in place
- [ ] API client script linked
- [ ] identify.html updated
- [ ] disease.html updated
- [ ] Images upload successfully
- [ ] Results display correctly

## 🎉 Next Steps

1. Test plant identification with various images
2. Test disease detection
3. Integrate with "My Garden" feature
4. Add image preview
5. Add upload progress indicator
6. Add webcam capture
7. Create result history
8. Deploy to production

---

**Happy gardening! 🌱**
