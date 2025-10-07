# Railway Quick Start Checklist

## ⚠️ CRITICAL: Required Environment Variables

Your deployment is failing because **required environment variables are not set**. The app crashes on startup without these.

### 1. Add PostgreSQL Database (If not already added)
```
Railway Dashboard → New → Database → PostgreSQL
```
This automatically sets `DATABASE_URL`

### 2. Set SECRET_KEY (REQUIRED)
```bash
# Generate a secret key:
openssl rand -hex 32

# Then in Railway:
Variables tab → New Variable:
  Name: SECRET_KEY
  Value: <paste your generated key>
```

### 3. Set ALLOWED_ORIGINS (Recommended)
```
Variables tab → New Variable:
  Name: ALLOWED_ORIGINS  
  Value: https://your-frontend-domain.com
```

## Expected Deployment Flow After Fix

1. ✅ Build completes successfully
2. ✅ Container starts
3. ✅ Startup script validates environment variables
4. ✅ Database migrations run (if enabled)
5. ✅ Server starts on Railway's PORT
6. ✅ `/health` endpoint responds
7. ✅ Healthcheck passes
8. ✅ Deployment successful!

## What Was Fixed

### Before (Why it Failed)
- ❌ App crashed on import if DATABASE_URL or SECRET_KEY missing
- ❌ Hardcoded port 8000 instead of Railway's PORT
- ❌ No error messages explaining what went wrong
- ❌ Broken healthcheck in Dockerfile

### After (Current)
- ✅ Startup script validates environment variables first
- ✅ Clear error messages if variables are missing
- ✅ Uses Railway's PORT environment variable
- ✅ Railway's healthcheck properly configured
- ✅ Logs show exactly what's wrong

## Verify Deployment

After setting environment variables and redeploying, check logs for:

```
✅ Environment variables validated
📊 Configuration:
  - Database: postgresql://***
  - Port: 8000
🔄 Running database migrations...
🌐 Starting uvicorn server...
🚀 BDD Property Tracker API starting up...
```

Then test the health endpoint:
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "BDD Property Tracker",
  "version": "1.0.0"
}
```

## Next Steps After Deployment

1. Update frontend environment variables with new backend URL
2. Test API connectivity from frontend
3. Run a test property submission
4. Verify file uploads work (if Cloudinary configured)

## Need Help?

Check the comprehensive guide: `docs/RAILWAY_DEPLOYMENT_GUIDE.md`

