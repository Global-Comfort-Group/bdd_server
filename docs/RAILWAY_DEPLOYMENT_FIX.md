# 🚂 Railway Deployment Fix

## ✅ Issue Resolved: ModuleNotFoundError

### Problem
Railway deployment was failing with:
```
ModuleNotFoundError: No module named 'jwt'
```

### Root Cause
Two issues found:

1. **Inconsistent JWT imports:**
   - `app/api/v1/auth.py` used: `import jwt` (requires PyJWT)
   - `app/core/security.py` used: `from jose import jwt` (uses python-jose)
   - `requirements.txt` only had `python-jose[cryptography]`

2. **Missing Cloudinary dependency:**
   - Code imports `cloudinary` but not in requirements.txt

### Solution Applied

#### 1. Fixed JWT Import (auth.py)
```python
# Before
import jwt
...
except jwt.PyJWTError:

# After
from jose import jwt
...
except jwt.JWTError:
```

#### 2. Added Cloudinary to requirements.txt
```python
# File handling
python-magic==0.4.27
pillow==10.1.0
openpyxl==3.1.2
cloudinary==1.36.0  # ← Added this
```

### Files Changed
- ✅ `app/api/v1/auth.py` - Fixed JWT import
- ✅ `requirements.txt` - Added cloudinary==1.36.0

### How to Deploy

```bash
cd /path/to/bdd_server

# 1. Pull latest changes (if needed)
git pull

# 2. Push to Railway
git push

# Railway will automatically:
# - Install updated requirements
# - Rebuild and redeploy
# - Use the corrected imports
```

---

## 🔍 How to Prevent This in the Future

### 1. Test Requirements Locally

Before deploying, test in a fresh virtual environment:

```bash
# Create fresh environment
python3 -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

# Install from requirements
pip install -r requirements.txt

# Try to run the server
uvicorn app.main:app --reload

# If it works, you're good to deploy!
deactivate
```

### 2. Use Dependency Checker

```bash
# Check for missing imports
pip install pipreqs
pipreqs . --force

# Compare with your requirements.txt
diff pipreqs_requirements.txt requirements.txt
```

### 3. Railway Pre-Deploy Checklist

Before pushing to Railway:

- [ ] All imports have matching packages in requirements.txt
- [ ] No `import xyz` that needs `pip install xyz`
- [ ] Version numbers specified (avoid `package==latest`)
- [ ] Test in clean virtual environment locally
- [ ] Check Railway logs after deployment

---

## 📋 Common Railway Deployment Issues

### Issue 1: ModuleNotFoundError
**Symptoms:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
1. Check the import: `import xyz` or `from xyz import abc`
2. Find the package name (might be different from import name)
3. Add to requirements.txt: `xyz==version`
4. Common examples:
   - `import jwt` → needs `PyJWT` **OR** use `from jose import jwt`
   - `import PIL` → needs `Pillow`
   - `import cv2` → needs `opencv-python`
   - `import cloudinary` → needs `cloudinary`

### Issue 2: Version Conflicts
**Symptoms:** `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed`

**Solution:**
1. Use specific versions in requirements.txt
2. Test locally with `pip install -r requirements.txt`
3. Use `pip list` to see what versions work locally
4. Copy those versions to requirements.txt

### Issue 3: Build Timeout
**Symptoms:** Build takes too long and times out

**Solution:**
1. Use binary packages when available (e.g., `psycopg2-binary` not `psycopg2`)
2. Remove unnecessary dev dependencies from requirements.txt
3. Use Railway's build cache (automatic)

### Issue 4: Environment Variables
**Symptoms:** `KeyError: 'DATABASE_URL'` or similar

**Solution:**
1. Go to Railway Dashboard → Your Service → Variables
2. Add all required environment variables:
   - `DATABASE_URL` (auto-provided if using Railway PostgreSQL)
   - `SECRET_KEY`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - etc.

### Issue 5: Port Binding
**Symptoms:** App starts but Railway shows unhealthy

**Solution:**
Railway expects your app to listen on `0.0.0.0:$PORT`

```python
# In your start command or code
import os
port = int(os.environ.get("PORT", 8000))

# Use in uvicorn
uvicorn.run("app.main:app", host="0.0.0.0", port=port)
```

Or in your start command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

---

## 🎯 Your Fixed Configuration

### requirements.txt (Updated)
```
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0

# Authentication
python-jose[cryptography]==3.3.0  # ← JWT support
passlib[bcrypt]==1.7.4
python-multipart==0.0.7

# File handling
python-magic==0.4.27
pillow==10.1.0
openpyxl==3.1.2
cloudinary==1.36.0  # ← Added for file uploads

# Utilities
python-decouple==3.8
httpx==0.25.2
geopy==2.4.0
fuzzywuzzy==0.18.0
python-levenshtein==0.23.0

# Development and testing (optional for production)
pytest==7.4.3
pytest-asyncio==0.21.1
playwright==1.40.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
```

### JWT Usage (Standardized)
```python
# Use this everywhere:
from jose import jwt

# Not this:
import jwt  # ❌ Requires PyJWT package
```

---

## 🚀 Next Steps

1. **Push Changes:**
   ```bash
   git push
   ```

2. **Monitor Railway Logs:**
   - Go to Railway Dashboard
   - Click your service
   - View "Deployments" → Latest deployment → "View Logs"
   - Should see successful startup

3. **Test Endpoints:**
   ```bash
   # Health check
   curl https://your-app.up.railway.app/health
   
   # Test auth
   curl -X POST https://your-app.up.railway.app/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   ```

4. **Set Environment Variables** (if not done):
   - Go to Railway → Variables
   - Add:
     - `SECRET_KEY` = your-secret-key
     - `CLOUDINARY_CLOUD_NAME` = your-cloud-name
     - `CLOUDINARY_API_KEY` = your-api-key
     - `CLOUDINARY_API_SECRET` = your-api-secret
     - `ALLOWED_ORIGINS` = your-frontend-url

---

## 📚 Resources

- [Railway Docs](https://docs.railway.app/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [Cloudinary Python SDK](https://cloudinary.com/documentation/python_integration)

---

**Date:** October 6, 2025  
**Status:** ✅ Fixed and Ready for Deployment  
**Commit:** `fix: add missing dependencies and fix jwt import`

