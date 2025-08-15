# Meeting Bot Dashboard

A full-stack application for managing meeting bots with real-time transcription and AI-powered reporting.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + PostgreSQL + Redis
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis for session management
- **Real-time**: WebSocket support for live updates

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- Docker and Docker Compose
- PostgreSQL and Redis (or use Docker)

### Option 1: Full-Stack with Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd meahana-frontend

# Copy environment template
cp env.example .env

# Edit .env with your API keys
nano .env

# Start all services (frontend + backend + database + redis)
docker-compose up --build
```

This will start:
- Frontend on http://localhost:3000
- Backend API on http://localhost:8000
- PostgreSQL on localhost:5432
- Redis on localhost:6379

### Option 2: Development Mode (Frontend + Backend)

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
npm run backend:install

# Start both frontend and backend
npm run dev
```

### Option 3: Backend Only with Docker

```bash
# Start only backend services (backend + database + redis)
npm run backend:docker
```

## 🔧 Development

### Frontend Development

```bash
# Start React development server
npm start

# Build for production
npm run build
```

### Backend Development

```bash
# Start FastAPI development server
npm run backend

# Run with Docker
npm run backend:docker

# Install Python dependencies
npm run backend:install
```

### Database Management

```bash
# Start database services
docker-compose up db redis

# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"
```

## 🌐 API Endpoints

The backend provides the following API endpoints:

- `POST /api/v1/bots/` - Create a new meeting bot
- `GET /meeting/{id}/report` - Get meeting report
- `GET /meeting/{id}/transcripts` - Get meeting transcripts
- `GET /docs` - Interactive API documentation (Swagger UI)

## 🔑 Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Frontend
REACT_APP_API_URL=http://localhost:8000

# Backend
ATTENDEE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
WEBHOOK_SECRET=your_secret_here
NGROK_AUTH_TOKEN=your_ngrok_token_here
```

## 🐳 Docker Commands

```bash
# Start all services (frontend + backend + database + redis)
docker-compose up --build

# Start in background
docker-compose up -d

# Start only backend services (backend + database + redis)
docker-compose up --build backend db redis

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
docker-compose logs -f redis

# Rebuild specific service
docker-compose up --build backend
```

## 📁 Project Structure

```
meahana-frontend/
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
├── Dockerfile.frontend    # Frontend container
└── package.json          # Node.js dependencies
```

## 📊 Monitoring

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (user: user, password: password)
- **Redis**: localhost:6379

## 🚀 Production Deployment

### Build All Services

```bash
npm run build:all
```

### Deploy with Docker

```bash
# Build and push images
docker-compose -f docker-compose.prod.yml up --build

# Or deploy to cloud platform
docker-compose -f docker-compose.prod.yml push
```

## 🐛 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 8000, 5432, and 6379 are available
2. **Database connection**: Wait for PostgreSQL to be ready (10-15 seconds)
3. **API errors**: Check backend logs with `docker-compose logs backend`
4. **Frontend not loading**: Verify backend is running on port 8000

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `npm run dev`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 