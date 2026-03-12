# Quick Reference - GreenSphere Backend

## 🚀 Start Backend

```bash
cd backend
python run.py
```

Server runs on: `http://localhost:5000`

## 📝 First Time Setup

```bash
cd backend

# Windows
setup.bat

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add API key
python run.py
```

## 📋 Prerequisites

1. **PlantID API Key** - Get from https://plant.id/
2. **Python 3.8+** - https://python.org
3. **Internet Connection** - For API calls

## 🔑 Get API Key (Free)

1. Go to https://plant.id/
2. Click "Sign Up"
3. Create account (takes 2 minutes)
4. Copy API key from dashboard
5. Add to `backend/.env`:
   ```
   PLANTID_API_KEY=your_key_here
   ```

## 📡 API Endpoints

```
Health:          GET  /api/health
Identify Plant:  POST /api/plants/identify
Detect Disease:  POST /api/diseases/detect
```

## 💻 Test Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Plant identification
curl -X POST -F "image=@plant.jpg" \
  http://localhost:5000/api/plants/identify

# Disease detection
curl -X POST -F "image=@plant.jpg" \
  http://localhost:5000/api/diseases/detect
```

## 🔗 Use in HTML

```html
<script src="api-client.js"></script>
<script src="identify-integration.js"></script>

<script>
  // Identify plant
  const result = await greensphereAPI.identifyPlantFromFile(file);
  console.log(result.data.name);
</script>
```

## 📁 File Locations

```
ffend/
├── backend/
│   ├── app.py              ← Main app
│   ├── plantid_service.py  ← API integration
│   ├── run.py              ← Start here
│   ├── .env                ← Add API key
│   └── requirements.txt
│
├── api-client.js           ← Add to HTML
├── identify-integration.js ← Add to identify.html
├── disease-integration.js  ← Add to disease.html
└── SETUP.md               ← Full guide
```

## ✅ Verify Setup

```bash
# Check health
curl http://localhost:5000/api/health

# Should return:
# {"status":"healthy","service":"GreenSphere API",...}
```

## 🐛 Common Fixes

| Issue | Fix |
|-------|-----|
| "API key not configured" | Edit .env, add key, restart |
| Module errors | `pip install -r requirements.txt` |
| Port already in use | Kill process or use different port |
| Import errors | Activate venv: `venv\Scripts\activate` |

## 📚 Full Documentation

- **SETUP.md** - Complete setup guide
- **INTEGRATION_GUIDE.html** - HTML integration steps
- **BACKEND_SUMMARY.md** - Detailed overview
- **backend/README.md** - Backend documentation

## 🆘 Emergency Help

1. Check that backend is running: `http://localhost:5000/api/health`
2. Check that API key is in `.env`
3. Check Python version: `python --version` (need 3.8+)
4. Check internet connection is working
5. Try with different image file

## 📞 Contact

- PlantID Support: https://plant.id/support
- Flask Help: https://flask.palletsprojects.com/

---

**Remember: Always test health endpoint first!**
