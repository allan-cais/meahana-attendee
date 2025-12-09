# Meahana Attendee

A clean, minimal integration for managing meeting bots with real-time transcription and AI-powered reporting.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + Supabase + Redis
- **Database**: Supabase (REST API)
- **Cache**: Redis for session management

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Docker and Docker Compose

### Option 1: Full-Stack with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd meahana-attendee

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker-compose up --build
```

This will start:
- Frontend on http://localhost:3000
- Backend API on http://localhost:8000
- Redis on localhost:6379

**Note**: This setup uses Supabase REST API. Make sure to set your `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.

### Option 2: Development Mode

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd backend && pip install -r requirements.txt

# Start Redis service (required)
docker-compose up -d redis

# Start backend
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend in another terminal
npm start
```

## 🔧 Development

### Available Scripts

**Root Level (Monorepo):**
```bash
npm run dev              # Start both frontend + backend in development mode
npm run prod             # Start both frontend + backend in production mode
npm start                # Build frontend + start both in production mode
npm run build            # Build frontend for production
npm run install:all      # Install all dependencies (frontend + backend)
```

**Individual Services:**
```bash
# Frontend
npm run frontend:dev     # Start React development server
npm run frontend:build   # Build React app for production
npm run frontend:prod    # Serve built frontend (port 3000)

# Backend
npm run backend:dev      # Start FastAPI with hot reload
npm run backend:prod     # Start FastAPI in production mode
```

### Frontend Development

```bash
# Start React development server
cd frontend && npm start

# Build for production
cd frontend && npm run build
```

### Backend Development

```bash
# Start FastAPI development server
npm run backend:dev

# Run with Docker
npm run backend:docker
```

### Database Management

```bash
# Start Redis service
docker-compose up -d redis

# Reset database (clear all data)
./reset-db.sh

# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

**Important**: The backend uses Supabase REST API for all database operations, ensuring consistency between development and production environments.

## 🚀 Production Deployment

### Production Docker Compose

For production deployment, use the production-optimized compose file:

```bash
# Start production services
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Production Features

- **No development reload** - Stable, production-ready backend
- **Optimized logging** - Minimal, production-appropriate logging
- **Production environment** - Defaults to production mode
- **Health checks** - Built-in health monitoring endpoints
- **CORS configured** - Secure cross-origin request handling

## 🌐 API Endpoints

- `POST /api/v1/bots/` - Create a new meeting bot
- `GET /api/v1/bots/` - Get all bots
- `GET /api/v1/bots/{id}` - Get specific bot
- `DELETE /api/v1/bots/{id}` - Delete bot
- `POST /api/v1/bots/{id}/poll-status` - Poll bot status
- `GET /meeting/{id}/scorecard` - Get meeting scorecard
- `POST /meeting/{id}/trigger-analysis` - Trigger analysis

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```bash
# Backend
ATTENDEE_API_KEY=your_key_here
ATTENDEE_API_BASE_URL=https://app.attendee.dev
ENVIRONMENT=development

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

## 📁 Project Structure

```
meahana-attendee/
├── frontend/              # React frontend source
│   ├── src/               # React components/services/types
│   ├── package.json       # Frontend dependencies/scripts
│   └── Dockerfile         # Frontend container
├── backend/               # Python FastAPI backend
│   ├── app/               # FastAPI application
│   ├── alembic/           # Database migrations
│   ├── requirements.txt   # Backend dependencies
│   └── Dockerfile         # Backend container
├── docker-compose.yml     # Dev orchestration
├── docker-compose.prod.yml# Prod orchestration
└── package.json           # Monorepo scripts (frontend/backend runners)
```

## 📊 Features

- **Bot Management**: Create, monitor, and delete meeting bots
- **Real-time Status**: Live updates on bot status and meeting progress
- **AI Analysis**: Automated meeting insights and scorecards
- **Clean UI**: Modern, responsive interface built with Tailwind CSS
- **Type Safety**: Full TypeScript support for both frontend and backend

## 🚀 Production Deployment

```bash
# Build all services
npm run build

# Deploy with Docker
docker-compose -f docker-compose.prod.yml up --build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `npm run dev`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
# Meahana Attendee

A clean, minimal integration for managing meeting bots with real-time transcription and AI-powered reporting.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + Supabase + Redis
<<<<<<< HEAD
- **Database**: Supabase (PostgreSQL) with Alembic migrations
=======
- **Database**: Supabase (REST API)
>>>>>>> origin/main
- **Cache**: Redis for session management

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Docker and Docker Compose

### Option 1: Full-Stack with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd meahana-attendee

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Start all services
docker-compose up --build
```

This will start:
- Frontend on http://localhost:3000
- Backend API on http://localhost:8000
- Redis on localhost:6379

<<<<<<< HEAD
**Note**: This setup uses Supabase database. Make sure to set your `DATABASE_URL` in `backend/.env`.
=======
**Note**: This setup uses Supabase REST API. Make sure to set your `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.
>>>>>>> origin/main

### Option 2: Development Mode

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd backend && pip install -r requirements.txt

# Start Redis service (required)
docker-compose up -d redis

# Start backend
cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend in another terminal
npm start
```

<<<<<<< HEAD
## 🔧 Development

=======
### Option 3: Production Mode (Local)

```bash
# Install dependencies
npm run install:all

# Quick start with build + production servers
npm start

# OR use the startup scripts
./start-prod.sh          # Linux/macOS
start-prod.bat           # Windows

# OR run individual commands
npm run build            # Build frontend
npm run prod            # Start both production servers
```

This will start:
- Frontend on http://localhost:3000 (optimized production build)
- Backend API on http://localhost:8000 (production mode)
- Requires Redis running (use `docker-compose up -d redis`)

## 🔧 Development

### Available Scripts

**Root Level (Monorepo):**
```bash
npm run dev              # Start both frontend + backend in development mode
npm run prod             # Start both frontend + backend in production mode
npm start                # Build frontend + start both in production mode
npm run build            # Build frontend for production
npm run install:all      # Install all dependencies (frontend + backend)
```

**Individual Services:**
```bash
# Frontend
npm run frontend:dev     # Start React development server
npm run frontend:build   # Build React app for production
npm run frontend:prod    # Serve built frontend (port 3000)

# Backend
npm run backend:dev      # Start FastAPI with hot reload
npm run backend:prod     # Start FastAPI in production mode
```

>>>>>>> origin/main
### Frontend Development

```bash
# Start React development server
<<<<<<< HEAD
npm start

# Build for production
npm run build
=======
cd frontend && npm start

# Build for production
cd frontend && npm run build
>>>>>>> origin/main
```

### Backend Development

```bash
# Start FastAPI development server
<<<<<<< HEAD
npm run backend
=======
npm run backend:dev
>>>>>>> origin/main

# Run with Docker
npm run backend:docker
```

### Database Management

```bash
# Start Redis service
docker-compose up -d redis

# Reset database (clear all data)
./reset-db.sh

# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

<<<<<<< HEAD
**Important**: The backend connects to your local PostgreSQL database to ensure consistency between development and production environments.
=======
**Important**: The backend uses Supabase REST API for all database operations, ensuring consistency between development and production environments.
>>>>>>> origin/main

## 🚀 Production Deployment

### Production Docker Compose

For production deployment, use the production-optimized compose file:

```bash
# Start production services
docker-compose -f docker-compose.prod.yml up --build -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Production Features

- **No development reload** - Stable, production-ready backend
- **Optimized logging** - Minimal, production-appropriate logging
- **Production environment** - Defaults to production mode
- **Health checks** - Built-in health monitoring endpoints
- **CORS configured** - Secure cross-origin request handling

## 🌐 API Endpoints

- `POST /api/v1/bots/` - Create a new meeting bot
- `GET /api/v1/bots/` - Get all bots
- `GET /api/v1/bots/{id}` - Get specific bot
- `DELETE /api/v1/bots/{id}` - Delete bot
- `POST /api/v1/bots/{id}/poll-status` - Poll bot status
- `GET /meeting/{id}/scorecard` - Get meeting scorecard
- `POST /meeting/{id}/trigger-analysis` - Trigger analysis

## 🔑 Environment Variables

Create a `.env` file in the root directory:

```bash
# Backend
ATTENDEE_API_KEY=your_key_here
ATTENDEE_API_BASE_URL=https://app.attendee.dev
ENVIRONMENT=development

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

## 📁 Project Structure

```
meahana-attendee/
├── src/                    # React frontend source
│   ├── components/         # React components
│   ├── services/          # API services
│   └── types/             # TypeScript type definitions
├── backend/               # Python FastAPI backend
│   ├── app/              # FastAPI application
│   │   ├── models/       # Database models
│   │   ├── routers/      # API routes
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   ├── alembic/          # Database migrations
│   └── requirements.txt   # Python dependencies
├── docker-compose.yml     # Full-stack orchestration
└── package.json          # Node.js dependencies
```

## 📊 Features

- **Bot Management**: Create, monitor, and delete meeting bots
- **Real-time Status**: Live updates on bot status and meeting progress
- **AI Analysis**: Automated meeting insights and scorecards
- **Clean UI**: Modern, responsive interface built with Tailwind CSS
- **Type Safety**: Full TypeScript support for both frontend and backend

## 🚀 Production Deployment

```bash
# Build all services
npm run build

# Deploy with Docker
docker-compose -f docker-compose.prod.yml up --build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `npm run dev`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 