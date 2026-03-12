#!/bin/bash
# Installation and Setup Checklist for GreenSphere Backend

echo "🌿 GreenSphere Backend - Installation Checklist"
echo "=============================================="
echo ""

# Check Python
echo "✓ Checking Python installation..."
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "✗ Python not found. Install from https://python.org"
    exit 1
fi

# Navigate to backend
echo ""
echo "✓ Navigating to backend directory..."
cd backend || exit 1

# Check if venv exists
echo ""
echo "✓ Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo ""
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo ""
echo "✓ Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if .env exists
echo ""
echo "✓ Checking .env file..."
if [ ! -f ".env" ]; then
    echo "  Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your PlantID API key"
    echo "   Get free key from: https://plant.id/"
    echo ""
    echo "   Edit: backend/.env"
    echo "   Add: PLANTID_API_KEY=your_key_here"
    exit 0
fi

# Test API key
if grep -q "PLANTID_API_KEY=your_plantid_api_key_here" .env; then
    echo "⚠️  WARNING: API key not configured in .env"
    echo "   Get key from: https://plant.id/"
    exit 0
fi

# Success
echo ""
echo "✅ All checks passed!"
echo ""
echo "To start the backend:"
echo "  python run.py"
echo ""
echo "Backend will run on: http://localhost:5000"
echo ""
