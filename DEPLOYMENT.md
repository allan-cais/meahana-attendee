# Deployment Guide

## API Configuration

The application has been updated to work with the new hosting URL: `https://js-cais-dev-97449-u35829.vm.elestio.app/`

### Environment Variables

To configure the API URL for different environments, you can set the `REACT_APP_API_URL` environment variable:

```bash
# For development
REACT_APP_API_URL=http://localhost:8000

# For production/testing
REACT_APP_API_URL=https://js-cais-dev-97449-u35829.vm.elestio.app
```

**⚠️ IMPORTANT:** Do NOT include `/api` at the end of the `REACT_APP_API_URL`. The application automatically appends the correct API endpoints.

**❌ Incorrect:**
```bash
REACT_APP_API_URL=https://js-cais-dev-97449-u35829.vm.elestio.app/api
```

**✅ Correct:**
```bash
REACT_APP_API_URL=https://js-cais-dev-97449-u35829.vm.elestio.app
```

### Default Configuration

If no environment variable is set, the application will default to the production URL: `https://js-cais-dev-97449-u35829.vm.elestio.app`

## Changes Made

1. **Removed Mock Data**: All mock data and simulation functionality has been removed from the API service
2. **Updated API Base URL**: Changed from localhost to the new hosting URL
3. **Pure API Reliance**: The application now relies entirely on backend API calls
4. **Fixed Double /api/ Issue**: Automatically prevents duplicate `/api/` paths in API URLs

## Building for Production

```bash
npm run build
```

The built application will be in the `build/` directory and can be deployed to any static hosting service.

## API Endpoints

The application expects the following API endpoints to be available:

- `POST /api/v1/bots/` - Create a new meeting bot
- `GET /meeting/{id}/report` - Get meeting report
- `GET /meeting/{id}/transcripts` - Get meeting transcripts

## Notes

- The application no longer falls back to mock data if the API is unavailable
- All API calls will fail gracefully with proper error handling
- Ensure your backend API is running and accessible at the configured URL
- The application now automatically fixes any URL construction issues to prevent duplicate `/api/` paths
