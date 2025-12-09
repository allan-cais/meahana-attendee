@echo off
REM Production startup script for Meahana Attendee (Windows)
REM This script builds the frontend and starts both frontend and backend in production mode

echo 🚀 Starting Meahana Attendee in Production Mode
echo ================================================

REM Check if dependencies are installed
echo 📦 Checking dependencies...

if not exist "frontend\node_modules" (
    echo ⚠️  Frontend dependencies not found. Installing...
    npm run frontend:install
)

if not exist "backend\venv" (
    echo ⚠️  Backend environment not set up. Please:
    echo    1. Create a Python virtual environment in backend/
    echo    2. Install dependencies with: npm run backend:install
    echo    3. Set up your backend/.env file with Supabase credentials
    pause
    exit /b 1
)

REM Build frontend
echo 🏗️  Building frontend...
npm run frontend:build

REM Start both services
echo 🎬 Starting production services...
echo    - Frontend: http://localhost:3000
echo    - Backend:  http://localhost:8000
echo.
echo Press Ctrl+C to stop both services

npm run prod