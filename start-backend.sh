#!/bin/bash

# Start Meeting Bot Backend
echo "🚀 Starting Meeting Bot Backend..."

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Creating one..."
    /usr/local/bin/python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment activation failed. Using system Python..."
    PYTHON_CMD="/usr/local/bin/python3"
    PIP_CMD="/usr/local/bin/pip3"
else
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

# Check if dependencies are installed
if ! $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    $PIP_CMD install -r requirements-compatible.txt
fi

# Start the backend server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API documentation will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
