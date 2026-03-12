# Gemini API Setup Guide for Prakriti Chatbot

## Overview
Prakriti is the garden assistant chatbot in GreenSphere, powered by Google's Gemini API. It provides intelligent plant care advice, gardening tips, and personalized recommendations.

## Setup Instructions

### 1. Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API key"
3. Copy your API key (keep it safe!)

### 2. Add API Key to Your Backend

Navigate to your backend folder and create/update your `.env` file:

```bash
cd backend
```

Add the following line to your `.env` file:

```
GEMINI_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key.

### 3. Install Dependencies

Install the Gemini Python package:

```bash
pip install -r requirements.txt
```

This will install `google-generativeai==0.3.0` along with other dependencies.

### 4. Restart Your Backend

Stop any running Flask servers and restart:

```bash
python app.py
```

or 

```bash
python run.py
```

### 5. Test the Chatbot

1. Open your application in the browser
2. Go to "My Garden" page
3. Click the green leaf button (🍃) in the bottom right corner
4. Type a question about your plants and press Send

## Features

Prakriti can help with:
- 🌱 Plant care advice
- 💧 Watering schedules
- 🌞 Sunlight requirements
- 🦠 Disease identification and treatment
- 🌱 Soil recommendations
- 🔍 Plant identification basics
- 📅 Garden planning
- 🌿 General gardening tips

## API Endpoints

### Single Message
```
POST /api/chatbot/ask
Content-Type: application/json

{
  "message": "How do I care for my Tulsi plant?"
}

Response:
{
  "success": true,
  "message": "Congratulations on your Tulsi plant!..."
}
```

### Multi-turn Conversation
```
POST /api/chatbot/multi-turn
Content-Type: application/json

{
  "conversation": [
    {"role": "user", "content": "How often should I water my plants?"},
    {"role": "assistant", "content": "Most indoor plants need watering..."},
    {"role": "user", "content": "What about succulents?"}
  ]
}
```

### Health Check
```
GET /api/chatbot/health
```

## Troubleshooting

### "Gemini API key not configured"
- Check that your `.env` file is in the `backend` folder
- Verify the API key is correct
- Make sure the backend server is restarted after adding the key

### "Connection error"
- Check if Flask backend is running (should be on http://localhost:5000)
- Look at the browser console for error details
- Check Flask server logs for backend errors

### Rate Limiting
- Google Gemini has free tier limits
- If you exceed limits, consider upgrading to a paid plan
- Add error handling in your frontend as needed

## Customization

### Change the Chatbot Personality

Edit the `PRAKRITI_SYSTEM_PROMPT` in `routes/chatbot_routes.py`:

```python
PRAKRITI_SYSTEM_PROMPT = """You are Prakriti, a helpful garden and plant care assistant..."""
```

### Use Different Gemini Models

Update the model name in `chatbot_routes.py`:

```python
model = genai.GenerativeModel(
    model_name='gemini-pro',  # or 'gemini-pro-vision' for image analysis
    system_instruction=PRAKRITI_SYSTEM_PROMPT
)
```

## Security Notes

- Never commit your `.env` file with the API key to git
- Add `.env` to your `.gitignore`
- Keep your API key confidential
- Monitor your API usage on the Google Cloud console

## Support

For issues with:
- **Gemini API**: Check [Google AI Documentation](https://ai.google.dev/)
- **Flask Backend**: Review `routes/chatbot_routes.py` and error logs
- **Frontend**: Check browser console for JavaScript errors
