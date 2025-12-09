# Railway Deployment Guide

This application is a monorepo containing:
- **Frontend**: React app in `./src` (builds to `./build`)
- **Backend**: FastAPI app in `./backend`

The backend serves both the API and the static frontend files.

## Prerequisites

1. Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional but recommended)
3. Git repository connected to Railway

## Environment Variables

Set the following environment variables in your Railway project:

### Required Variables

```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
ATTENDEE_API_KEY=your_attendee_api_key
ATTENDEE_API_BASE_URL=https://app.attendee.dev
WEBHOOK_BASE_URL=https://your-app.up.railway.app
ENVIRONMENT=production
APP_NAME=Meeting Bot Service
DEBUG=false
```

### Optional Variables

```
REDIS_URL=redis://localhost:6379/0
```

## Deployment Steps

### Option 1: Deploy via Railway Dashboard

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will auto-detect the configuration from `railway.toml` and `nixpacks.toml`
6. Add environment variables in the project settings
7. Click "Deploy"

### Option 2: Deploy via Railway CLI

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize project:
   ```bash
   railway init
   ```

4. Set environment variables:
   ```bash
   railway variables set SUPABASE_URL=your_value
   railway variables set SUPABASE_ANON_KEY=your_value
   # ... set all other required variables
   ```

5. Deploy:
   ```bash
   railway up
   ```

## Important Notes

1. **WEBHOOK_BASE_URL**: After your first deployment, update this variable with your Railway app URL (e.g., `https://your-app.up.railway.app`)

2. **Frontend API URL**: The React app is configured to use the same origin for API calls in production (via `.env.production`). No need to set `REACT_APP_API_URL` in Railway.

3. **Database**: This app uses Supabase for the database. Make sure your Supabase instance is accessible from Railway.

4. **Redis**: If you need Redis, add the Redis plugin in Railway or use an external Redis service and set the `REDIS_URL` variable.

5. **Port**: Railway automatically sets the `PORT` environment variable. The app is configured to use this via the Procfile.

6. **Health Check**: Railway will use the `/health` endpoint to check if your app is running.

7. **Build Directory**: The React build outputs to `./build` and the backend serves it from there.

## Troubleshooting

### Build Failures

- Check Railway logs for detailed error messages
- Ensure all dependencies are listed in `backend/requirements.txt`
- Verify Python version compatibility (app uses Python 3.10)

### Runtime Errors

- Check environment variables are set correctly
- Verify Supabase connection is working
- Check logs: `railway logs`

### API Not Responding

- Verify the port configuration
- Check CORS settings in `backend/app/main.py`
- Ensure health check endpoint is accessible

## Post-Deployment

1. Test the deployment:
   ```bash
   curl https://your-app.up.railway.app/health
   ```

2. Update webhook URLs in your Attendee.dev settings to point to your Railway URL

3. Monitor logs:
   ```bash
   railway logs
   ```

## How It Works

1. **Build Phase** (via `nixpacks.toml`):
   - Installs Node.js dependencies
   - Builds React frontend to `./build` directory
   - Installs Python dependencies

2. **Runtime** (via `Procfile`):
   - Starts FastAPI backend which serves both:
     - API endpoints at `/api/v1/*`, `/meeting/*`, `/webhook/*`
     - Static React frontend for all other routes

3. **Single Service**: One Railway service serves everything on one port

## Files Created for Railway

- `railway.toml` - Railway platform configuration
- `nixpacks.toml` - Build and runtime configuration (Node.js + Python)
- `Procfile` - Process definition (starts backend which serves frontend)
- `backend/.env.example` - Environment variable template
- `backend/app/main.py` - Updated to serve static frontend files

## Architecture Notes

- The backend uses FastAPI's `StaticFiles` to serve the React build
- API routes are prefixed to avoid conflicts with frontend routing
- The frontend build is served at the root path (`/`)
- All client-side routes are handled by React Router (SPA behavior)
