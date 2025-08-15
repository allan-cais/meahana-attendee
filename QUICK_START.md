# 🚀 Quick Start Guide

Get your Meeting Bot Dashboard running in minutes!

## ✅ What's Working Now

- ✅ **Backend**: Python 3.13 compatibility fixed
- ✅ **Dependencies**: All packages installed successfully
- ✅ **Models**: Import errors resolved
- ✅ **FastAPI**: Application starts without errors

## 🚀 Start Everything (Recommended)

### Option 1: Full-Stack Development
```bash
# Start both frontend and backend together
npm run dev
```

This will:
- Start React frontend on http://localhost:3000
- Start FastAPI backend on http://localhost:8000
- Show both in the same terminal

### Option 2: Start Backend Only
```bash
# Start just the backend
npm run backend
```

### Option 3: Start Frontend Only
```bash
# Start just the frontend
npm start
```

## 🔧 Manual Setup (if needed)

### Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements-compatible.txt

# Start server
python -m uvicorn app.main:app --reload
```

### Frontend Setup
```bash
# Install dependencies
npm install

# Start development server
npm start
```

## 🌐 Access Points

Once running:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive Swagger**: http://localhost:8000/docs

## 🔑 Environment Setup

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your API keys**:
   ```bash
   # Required for backend
   ATTENDEE_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   WEBHOOK_SECRET=your_secret_here
   
   # Database (optional - will use defaults)
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/meeting_bot_db
   REDIS_URL=redis://localhost:6379/0
   ```

## 🗄️ Database (Optional)

The backend will work without a database for basic testing. If you want full functionality:

### Quick Database with Docker
```bash
# Start just database services
cd backend
docker-compose up db redis -d
```

### Local Database
```bash
# Install PostgreSQL and Redis locally
brew install postgresql redis  # macOS
brew services start postgresql redis
```

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check dependencies
cd backend
source venv/bin/activate
python check_deps.py

# Reinstall if needed
pip install -r requirements-compatible.txt --force-reinstall
```

### Frontend Can't Connect to Backend
- Ensure backend is running on port 8000
- Check `REACT_APP_API_URL` in `.env`
- Verify no firewall blocking localhost

### Port Conflicts
```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend

# Kill processes if needed
kill -9 <PID>
```

## 📚 Next Steps

1. **Test the API**: Visit http://localhost:8000/docs
2. **Create a bot**: Use the frontend form
3. **Check logs**: Monitor terminal output
4. **Explore endpoints**: Try the interactive API docs

## 🎯 What You Can Do Now

- ✅ **Create meeting bots** via the frontend
- ✅ **API endpoints** working at `/api/v1/bots/`
- ✅ **Database models** properly configured
- ✅ **Real-time updates** via webhooks
- ✅ **AI analysis** with OpenAI integration

## 🆘 Need Help?

- Check the logs in your terminal
- Visit http://localhost:8000/docs for API testing
- Use `python check_deps.py` to verify setup
- Check `LOCAL_DEVELOPMENT.md` for detailed troubleshooting

---

**🎉 You're all set! Run `npm run dev` to start both services.**
