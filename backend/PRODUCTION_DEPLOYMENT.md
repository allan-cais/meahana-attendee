# Production Deployment Guide

This guide covers deploying the Meeting Bot Service to the production environment at `https://js-cais-dev-97449-u35829.vm.elestio.app/`.

## Environment Configuration

### 1. Create Production Environment File

Copy the example configuration and update with your values:

```bash
cp production.env.example .env.production
```

### 2. Required Environment Variables

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Production Base URL
PRODUCTION_BASE_URL=https://js-cais-dev-97449-u35829.vm.elestio.app

# Webhook Configuration
WEBHOOK_BASE_URL=https://js-cais-dev-97449-u35829.vm.elestio.app
WEBHOOK_SECRET=your_secure_webhook_secret_here

# Disable ngrok auto-start in production
AUTO_START_NGROK=false

# Database (update with your production database details)
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/meeting_bot_db

# Redis (update with your production redis details)
REDIS_URL=redis://redis:6379/0

# API Keys (required)
ATTENDEE_API_KEY=your_attendee_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Deployment Steps

### 1. Update Docker Compose

Ensure your `docker-compose.yml` includes the production environment variables:

```yaml
environment:
  - ENVIRONMENT=production
  - PRODUCTION_BASE_URL=https://js-cais-dev-97449-u35829.vm.elestio.app
  - WEBHOOK_BASE_URL=https://js-cais-dev-97449-u35829.vm.elestio.app
  - AUTO_START_NGROK=false
```

### 2. Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d --build

# Check logs
docker-compose logs -f web
```

### 3. Verify Deployment

Check the application status:

```bash
# Health check
curl https://js-cais-dev-97449-u35829.vm.elestio.app/health

# Root endpoint (should show production environment)
curl https://js-cais-dev-97449-u35829.vm.elestio.app/
```

Expected response:
```json
{
  "message": "Meeting Bot Service API",
  "version": "1.0.0",
  "environment": "production",
  "base_url": "https://js-cais-dev-97449-u35829.vm.elestio.app",
  "webhook_url": "https://js-cais-dev-97449-u35829.vm.elestio.app/webhook/"
}
```

## Key Changes for Production

### 1. Ngrok Disabled
- `AUTO_START_NGROK=false` prevents ngrok from starting automatically
- The application uses the production URL for webhook handling

### 2. Production Environment Detection
- `ENVIRONMENT=production` enables production-specific behavior
- Webhook URLs are automatically configured using the production base URL

### 3. Webhook Configuration
- All webhook endpoints will use the production URL
- External services can send webhooks to `https://js-cais-dev-97449-u35829.vm.elestio.app/webhook/`

## Monitoring and Maintenance

### 1. Check Application Status
```bash
# Application health
curl https://js-cais-dev-97449-u35829.vm.elestio.app/health

# Webhook URL status
curl https://js-cais-dev-97449-u35829.vm.elestio.app/ngrok/webhook-url
```

### 2. View Logs
```bash
docker-compose logs -f web
```

### 3. Database Migrations
```bash
# Run migrations if needed
docker-compose exec web alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Webhooks not working**: Ensure `WEBHOOK_SECRET` is set and matches your external service configuration
2. **Database connection issues**: Verify `DATABASE_URL` is correct and database is accessible
3. **API key errors**: Ensure `ATTENDEE_API_KEY` and `OPENAI_API_KEY` are valid

### Debug Mode
If you need to enable debug mode temporarily:
```bash
DEBUG=true
```

Remember to disable debug mode in production after troubleshooting.

## Security Considerations

1. **Webhook Secret**: Use a strong, unique webhook secret
2. **API Keys**: Keep API keys secure and rotate regularly
3. **Database**: Use strong passwords and limit database access
4. **HTTPS**: Ensure your production environment uses HTTPS (already configured in your URL)

## Support

For deployment issues, check:
1. Application logs: `docker-compose logs -f web`
2. Environment variables: Ensure all required variables are set
3. Network connectivity: Verify database and Redis connections
4. API endpoints: Test health check and root endpoints
