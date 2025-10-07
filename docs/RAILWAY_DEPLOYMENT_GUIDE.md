# Railway Deployment Guide

## Required Environment Variables

The following environment variables **MUST** be set in Railway for the application to start:

### 1. DATABASE_URL (Required)
**Automatically provided by Railway when you add a PostgreSQL database**
- Format: `postgresql://user:password@host:port/database`
- Railway provides this automatically when you provision a Postgres database

### 2. SECRET_KEY (Required)
**JWT token signing secret**
- Generate with: `openssl rand -hex 32`
- Example: `09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7`
- **Important**: Keep this secret and unique per environment

### 3. ALLOWED_ORIGINS (Optional but Recommended)
**CORS allowed origins**
- Format: Comma-separated list of URLs
- Example: `https://yourdomain.com,https://www.yourdomain.com`
- For development: Can be `*` but not recommended for production

### 4. CLOUDINARY_CLOUD_NAME (Optional - for file uploads)
**Cloudinary cloud name**
- Get from https://cloudinary.com/console

### 5. CLOUDINARY_API_KEY (Optional - for file uploads)
**Cloudinary API key**
- Get from https://cloudinary.com/console

### 6. CLOUDINARY_API_SECRET (Optional - for file uploads)
**Cloudinary API secret**
- Get from https://cloudinary.com/console

### 7. GOOGLE_MAPS_API_KEY (Optional - for geocoding)
**Google Maps API key**
- Get from https://console.cloud.google.com/

## How to Set Environment Variables in Railway

1. Go to your Railway project
2. Click on your service (bdd_server)
3. Go to the "Variables" tab
4. Click "New Variable"
5. Add each required variable

## Deployment Steps

### Step 1: Add PostgreSQL Database
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. This will automatically set `DATABASE_URL` in your service

### Step 2: Set Required Variables
```bash
# In Railway Variables tab, add:
SECRET_KEY=<generate with: openssl rand -hex 32>
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### Step 3: Optional Variables (for full functionality)
```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
GOOGLE_MAPS_API_KEY=your-google-maps-key
```

### Step 4: Deploy
1. Push to staging branch: `git push origin staging`
2. Railway will automatically deploy
3. Check deployment logs for any errors

## Health Check

Railway will check `/health` endpoint after deployment. The app must respond within 5 minutes or deployment fails.

**Common Healthcheck Failure Causes:**
- Missing `DATABASE_URL` - App crashes on startup
- Missing `SECRET_KEY` - App crashes on startup  
- Database connection fails - Check database is running
- Port binding issue - Should be fixed with current Dockerfile

## Checking Deployment Status

### View Logs
1. Go to Railway dashboard
2. Click on your service
3. Go to "Deployments" tab
4. Click on latest deployment
5. View logs to see startup messages

### Expected Logs on Successful Start
```
✅ Environment variables validated
📊 Configuration:
  - Database: postgresql://***
  - Port: 8000
  - Upload Directory: ./uploads
🔄 Running database migrations...
🌐 Starting uvicorn server...
🚀 BDD Property Tracker API starting up...
📁 Upload directory ready: ./uploads
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Troubleshooting

### Healthcheck Fails with "service unavailable"
- **Cause**: App not starting or crashing
- **Solution**: Check deployment logs for error messages
- **Common fixes**:
  - Verify all required environment variables are set
  - Check DATABASE_URL is correct and database is running
  - Verify SECRET_KEY is set

### Database Connection Error
- **Cause**: DATABASE_URL incorrect or database not running
- **Solution**: 
  1. Check database service is active
  2. Verify DATABASE_URL in variables
  3. Railway Postgres should auto-populate this

### Import Errors
- **Cause**: Missing dependencies
- **Solution**: Verify requirements.txt includes all needed packages

### Permission Denied
- **Cause**: User permissions issue
- **Solution**: Already handled in Dockerfile with proper chown

## Railway Configuration Files

### railway.toml
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300  # 5 minutes
restartPolicyType = "always"
```

### Dockerfile
- Uses Python 3.11-slim
- Installs gcc and libpq-dev for PostgreSQL
- Creates non-root user for security
- Binds to Railway's PORT environment variable
- Includes startup script with validation

## Production Checklist

- [ ] PostgreSQL database added and running
- [ ] DATABASE_URL environment variable set (auto)
- [ ] SECRET_KEY generated and set (unique per environment)
- [ ] ALLOWED_ORIGINS set to production domain(s)
- [ ] Cloudinary credentials set (if using file uploads)
- [ ] Google Maps API key set (if using geocoding)
- [ ] Health check endpoint responding
- [ ] Database migrations completed
- [ ] CORS configured correctly for frontend domain

## Connecting Frontend

After backend is deployed, update your frontend environment variables:

```bash
# In your frontend .env or Railway variables
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_API_BASE_URL=https://your-backend.railway.app/api/v1
```

## Monitoring

### View Application Logs
```bash
# In Railway dashboard
Deployments → Latest Deployment → Logs
```

### Check Health Endpoint
```bash
curl https://your-backend.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "BDD Property Tracker",
  "version": "1.0.0"
}
```

## Support

If deployment continues to fail:
1. Check Railway status page: https://railway.statuspage.io/
2. Review deployment logs for specific errors
3. Verify all required environment variables are set
4. Check database connection
5. Verify Dockerfile builds locally: `docker build -t bdd-server .`

## Date
October 7, 2025

