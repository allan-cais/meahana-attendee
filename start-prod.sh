#!/bin/bash

# Production startup script for Meahana Attendee
# This script builds the frontend and starts both frontend and backend in production mode

set -e

echo "🚀 Starting Meahana Attendee in Production Mode"
echo "================================================"

# Check if dependencies are installed
echo "📦 Checking dependencies..."

if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not found. Installing..."
    npm run frontend:install
fi

if [ ! -d "backend/venv" ] && [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend environment not set up. Please:"
    echo "   1. Create a Python virtual environment in backend/"
    echo "   2. Install dependencies with: npm run backend:install"
    echo "   3. Set up your backend/.env file with Supabase credentials"
    exit 1
fi

# Build frontend
echo "🏗️  Building frontend..."
npm run frontend:build

# Start both services
echo "🎬 Starting production services..."
echo "   - Frontend: http://localhost:3000"
echo "   - Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both services"

npm run prod