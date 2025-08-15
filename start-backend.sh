#!/bin/bash

# Start Meeting Bot Backend
echo "🚀 Starting Meeting Bot Backend..."

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements-compatible.txt
fi

# Start the backend server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API documentation will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
