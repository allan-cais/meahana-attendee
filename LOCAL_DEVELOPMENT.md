# Local Development Guide

This guide explains how to run the Meeting Bot Dashboard backend locally without Docker.

## 🐍 Python Requirements

- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **pip** (Python package installer)
- **virtualenv** or **venv** (for isolated environments)

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
cd backend
python setup_local.py
```

This script will:
- Check Python version
- Create a virtual environment
- Guide you through dependency installation
- Provide setup options

### Option 2: Manual Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 📦 Dependencies

The backend requires these Python packages:

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy** - Database ORM
- **Alembic** - Database migrations
- **asyncpg** - PostgreSQL async driver
- **Redis** - Redis client
- **Pydantic** - Data validation
- **OpenAI** - AI API client
- **ngrok** - Tunnel service

## 🗄️ Database Setup

### Option 1: Local PostgreSQL + Redis

1. **Install PostgreSQL**:
   ```bash
   # macOS (using Homebrew)
   brew install postgresql
   brew services start postgresql
   
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   
   # Windows: Download from https://www.postgresql.org/download/windows/
   ```

2. **Install Redis**:
   ```bash
   # macOS
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # Windows: Download from https://redis.io/download
   ```

3. **Create Database**:
   ```bash
   # Connect to PostgreSQL
   psql postgres
   
   # Create database and user
   CREATE DATABASE meeting_bot_db;
   CREATE USER user WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE meeting_bot_db TO user;
   \q
   ```

### Option 2: Docker for Database Only

```bash
# Start only database services
docker-compose up db redis -d

# This will start:
# - PostgreSQL on localhost:5432
# - Redis on localhost:6379
```

## ⚙️ Environment Configuration

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   ```bash
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/meeting_bot_db
   REDIS_URL=redis://localhost:6379/0
   
   # API Keys
   ATTENDEE_API_KEY=your_attendee_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   WEBHOOK_SECRET=your_webhook_secret_here
   
   # Environment
   ENVIRONMENT=development
   DEBUG=true
   ```

## 🗃️ Database Migrations

```bash
# Make sure you're in the backend directory
cd backend

# Run migrations
alembic upgrade head

# Create new migration (if you modify models)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🚀 Running the Backend

### Development Mode (with auto-reload)

```bash
# From the backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🌐 Access Points

Once running, you can access:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔍 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   # Check dependencies
   python check_deps.py
   
   # Reinstall if needed
   pip install -r requirements.txt --force-reinstall
   ```

2. **Database Connection**:
   ```bash
   # Check PostgreSQL status
   brew services list | grep postgresql  # macOS
   sudo systemctl status postgresql      # Linux
   
   # Check Redis status
   brew services list | grep redis       # macOS
   sudo systemctl status redis-server    # Linux
   ```

3. **Port Conflicts**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   
   # Kill process if needed
   kill -9 <PID>
   ```

4. **Virtual Environment Issues**:
   ```bash
   # Deactivate and reactivate
   deactivate
   source venv/bin/activate
   
   # Or recreate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Dependency Issues

```bash
# Upgrade pip
pip install --upgrade pip

# Install with specific versions
pip install -r requirements.txt --no-cache-dir

# Check for conflicts
pip check
```

## 🧪 Testing

```bash
# Run tests (if available)
python -m pytest

# Check API health
curl http://localhost:8000/health

# Test database connection
python -c "
import asyncio
from app.core.database import engine
async def test():
    try:
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
asyncio.run(test())
"
```

## 📚 Next Steps

1. **Start the backend**: `uvicorn app.main:app --reload`
2. **Check API docs**: http://localhost:8000/docs
3. **Test endpoints**: Use the interactive Swagger UI
4. **Run frontend**: `npm start` (from project root)
5. **Full-stack**: Use `npm run dev` to run both

## 🆘 Getting Help

- Check the logs for error messages
- Verify all dependencies are installed
- Ensure database services are running
- Check environment variables are set correctly
- Use `python check_deps.py` to verify setup
