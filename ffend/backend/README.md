# GreenSphere Flask Backend

Complete Flask backend for plant identification and disease detection using PlantID v3 API.

## 📋 Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- pip package manager
- PlantID v3 API key (get from https://plant.id/)

### 2. Installation

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your PlantID API key
# PLANTID_API_KEY=your_api_key_here
```

### 4. Run the Backend

```bash
python run.py
```

The API will be available at: `http://localhost:5000`

## 📡 API Endpoints

### Health Check
```
GET /api/health
```

### Plant Identification
```
POST /api/plants/identify
Content-Type: multipart/form-data

Request:
- image: File (PNG, JPG, GIF, WebP)

Response:
{
    "success": true,
    "data": {
        "confidence": 95.5,
        "name": "Plant Name",
        "scientific": "Scientific name",
        "purposes": ["Air Purification", "Decorative"],
        "suitability": "...",
        "soil": "...",
        "water": "...",
        "climate": "...",
        "toxicity": "safe/toxic",
        "toxicityInfo": "...",
        "medical": "..."
    }
}
```

Alternative endpoint with base64:
```
POST /api/plants/identify/base64
Content-Type: application/json

Request:
{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "filename": "plant.jpg"
}
```

### Disease Detection
```
POST /api/diseases/detect
Content-Type: multipart/form-data

Request:
- image: File (PNG, JPG, GIF, WebP)

Response:
{
    "success": true,
    "data": {
        "isHealthy": false,
        "title": "Disease Name",
        "probability": 85.5,
        "description": "...",
        "severity": "High",
        "causes": ["Cause 1", "Cause 2"],
        "symptoms": ["Symptom 1"],
        "homeRemedies": ["Remedy 1"],
        "fertilizer": ["Recommendation"],
        "pesticide": ["Recommendation"],
        "prevention": ["Tip 1"]
    }
}
```

Alternative endpoint with base64:
```
POST /api/diseases/detect/base64
Content-Type: application/json

Request:
{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "filename": "plant.jpg"
}
```

## 🔗 Frontend Integration

### 1. Add API Client
Include in your HTML:
```html
<script src="api-client.js"></script>
```

### 2. Update identify.html
- Include the API client script
- Include `identify-integration.js` script
- The `identifyPlant()` function will now use the Flask backend

### 3. Update disease.html
- Include the API client script
- Include `disease-integration.js` script
- The `detectDisease()` function will now use the Flask backend

### Example Usage
```javascript
// Identify a plant
const result = await greensphereAPI.identifyPlantFromFile(fileObject);
if (result.success) {
    console.log('Plant:', result.data.name);
    console.log('Confidence:', result.data.confidence);
}

// Detect disease
const diseaseResult = await greensphereAPI.detectDiseaseFromFile(fileObject);
if (diseaseResult.success && !diseaseResult.data.isHealthy) {
    console.log('Disease:', diseaseResult.data.title);
    console.log('Severity:', diseaseResult.data.severity);
}
```

## 📝 Project Structure

```
backend/
├── app.py                 # Flask application factory
├── config.py             # Configuration management
├── plantid_service.py    # PlantID API integration
├── run.py                # Entry point
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
└── routes/
    ├── __init__.py
    ├── health_routes.py  # Health check endpoints
    ├── plant_routes.py   # Plant identification endpoints
    └── disease_routes.py # Disease detection endpoints
```

## 🔐 CORS Configuration

The backend is configured to accept requests from:
- http://localhost:5000
- http://localhost:3000
- http://127.0.0.1:5000

To add more origins, edit `.env`:
```
CORS_ALLOWED_ORIGINS=http://localhost:5000,http://localhost:3000,http://your-domain.com
```

## 🐛 Troubleshooting

### "PlantID API key is not configured"
- Ensure you have set `PLANTID_API_KEY` in `.env`
- Restart the Flask server

### CORS errors in browser
- Check that your frontend origin is in `CORS_ALLOWED_ORIGINS`
- Ensure request method matches allowed methods (GET, POST, OPTIONS)

### Timeout errors
- Check your internet connection
- Verify PlantID API is accessible
- Try with a smaller image file

### 500 Internal Server Error
- Check Flask logs in terminal
- Verify PlantID API key is valid
- Check image format is supported

## 📦 Dependencies

- Flask: Web framework
- Flask-CORS: CORS support
- requests: HTTP client
- python-dotenv: Environment variables
- Werkzeug: Utilities library

## 🚀 Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
   ```

3. Configure reverse proxy (nginx/Apache)
4. Use environment-specific `.env` file
5. Enable HTTPS

## 📞 Support

For issues with:
- Plant.ID API: https://plant.id/support
- Flask: https://flask.palletsprojects.com/
- CORS: Check browser console for detailed error messages

## 📄 License

This backend is part of the GreenSphere project.
