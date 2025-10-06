# 📦 Requirements Management Guide

## ❓ Should You Use `pip freeze`?

### **Short Answer: NO, not directly**

---

## ⚖️ Why Not `pip freeze > requirements.txt`?

### Problems:

1. **Too many packages** (150+) - includes all transitive dependencies
2. **OS-specific** - Your Mac packages won't work on Railway's Linux
3. **Unreadable** - Can't tell what YOU need vs dependencies
4. **Hard to maintain** - Difficult to update individual packages

---

## ✅ Best Practice: Manual + Checker

### Your New Workflow:

```bash
cd /path/to/bdd_server
source venv/bin/activate

# 1. Check for missing dependencies
python3 check_requirements.py

# 2. If missing, find version
pip show package-name | grep Version

# 3. Add to requirements.txt
# Edit requirements.txt and add: package-name==version

# 4. Verify again
python3 check_requirements.py

# 5. Push to Railway
git add requirements.txt
git commit -m "fix: add missing dependency"
git push
```

---

## 🔍 The Dependency Checker

### What It Does:

✅ Scans all `.py` files in `app/` folder  
✅ Finds all `import` and `from X import` statements  
✅ Filters out standard library (os, sys, datetime, etc.)  
✅ Checks if each import is in `requirements.txt`  
✅ Handles name differences (import jose → python-jose)  
✅ Shows what's missing

### Example Output:

```bash
$ python3 check_requirements.py

🔍 Checking for missing dependencies...
📁 Scanning: /path/to/app
📄 Requirements: /path/to/requirements.txt

✅ Found 11 external package imports

✅ All dependencies are in requirements.txt!

📦 External packages used:
  ✓ fastapi              (fastapi)
  ✓ sqlalchemy           (sqlalchemy)
  ✓ jose                 (python-jose)
  ✓ pydantic_settings    (pydantic-settings)
  ...
```

---

## 📋 Import vs Package Names

Some imports differ from package names:

| Your Import | Package Name |
|-------------|--------------|
| `from jose import jwt` | `python-jose` |
| `from pydantic_settings import` | `pydantic-settings` |
| `import PIL` | `Pillow` |
| `import cv2` | `opencv-python` |
| `import yaml` | `PyYAML` |

**The checker handles these automatically!**

---

## 🛠️ How to Fix Missing Dependencies

### When checker shows missing package:

```bash
❌ MISSING DEPENDENCIES:
  import cloudinary → ADD: cloudinary
```

### Steps:

```bash
# 1. Find installed version
pip show cloudinary | grep Version
# Output: Version: 1.44.1

# 2. Add to requirements.txt
echo "cloudinary==1.44.1" >> requirements.txt

# 3. Add in correct section with comment
# Edit requirements.txt manually:

# File handling
python-magic==0.4.27
pillow==10.1.0
cloudinary==1.44.1  # <- Add here

# 4. Verify
python3 check_requirements.py

# 5. Push
git add requirements.txt
git commit -m "fix: add cloudinary dependency"
git push
```

---

## 📁 Requirements.txt Structure

### Good Example:

```txt
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# File handling
cloudinary==1.36.0
pillow==10.1.0

# Utilities
httpx==0.25.2
geopy==2.4.0
```

**Benefits:**
- ✅ Grouped by purpose
- ✅ Clear and organized
- ✅ Easy to find packages
- ✅ Pinned versions (==)

---

## 🚨 Common Errors

### Error: `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```bash
# 1. Run checker
python3 check_requirements.py

# 2. It will tell you what's missing
# 3. Add to requirements.txt
# 4. Push to Railway
```

### Error: "Package already in requirements but still fails"

**Check for:**
- Wrong package name (jose vs python-jose)
- Typo in requirements.txt
- Wrong version (too old/new)

**Solution:**
```bash
# Verify package name
pip search package-name  # Or check PyPI.org
```

---

## ✅ Pre-Deployment Checklist

Before every Railway deployment:

```bash
# 1. Check dependencies
python3 check_requirements.py

# 2. Verify it passes
# ✅ All dependencies are in requirements.txt!

# 3. Test locally (optional)
python3 -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
python3 -c "from app.main import app; print('✅ OK')"
deactivate && rm -rf test_env

# 4. Push
git add requirements.txt
git commit -m "fix: add missing dependencies"
git push

# 5. Monitor Railway logs
# Check for any ModuleNotFoundError
```

---

## 💡 Pro Tips

### 1. Use Checker Before Every Push

```bash
# Add to git pre-push hook
python3 check_requirements.py || exit 1
```

### 2. Document Why Packages Are Needed

```txt
# JWT tokens and password hashing
python-jose[cryptography]==3.3.0  # For JWT tokens
passlib[bcrypt]==1.7.4            # For password hashing
```

### 3. Pin Exact Versions

```txt
# Good for production
fastapi==0.104.1

# Risky - may break on update
fastapi>=0.104.1
fastapi  # Very risky
```

### 4. Group Related Packages

```txt
# Authentication (all auth-related)
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.7

# Database (all DB-related)
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
```

---

## 🎯 Quick Reference

```bash
# Check dependencies
python3 check_requirements.py

# Find package version
pip show package-name | grep Version

# Add to requirements.txt
echo "package-name==version" >> requirements.txt

# Verify
python3 check_requirements.py

# Push
git add requirements.txt && git commit -m "fix: add dependency" && git push
```

---

## 📚 Summary

### DO:
✅ Use `check_requirements.py` before deployment  
✅ Add only packages you directly import  
✅ Pin exact versions with `==`  
✅ Group and comment your requirements  
✅ Run checker as part of CI/CD

### DON'T:
❌ Run `pip freeze > requirements.txt`  
❌ Add every package you see  
❌ Leave packages unversioned  
❌ Skip the dependency check  
❌ Push without verifying

---

**Remember:** The checker does the hard work for you. Just run it before every deployment!

