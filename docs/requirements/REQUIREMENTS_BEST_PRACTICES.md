# 📦 Requirements.txt Best Practices

## ❓ Should You Use `pip freeze`?

### Short Answer: **NO, not directly**

---

## ⚖️ Comparison

### ❌ **`pip freeze > requirements.txt`** (Bad)

```bash
# This will output 150+ packages:
pip freeze > requirements.txt
```

**Problems:**
1. **Too many packages** (150+) - includes all transitive dependencies
2. **OS-specific** - Your Mac packages won't work on Railway's Linux
3. **Unreadable** - Can't tell what YOU actually need vs dependencies
4. **Hard to update** - Changing one package means regenerating everything
5. **Breaks easily** - One incompatible version breaks deployment

**Example output:**
```
alembic==1.12.1
annotated-types==0.6.0
anyio==3.7.1
asyncpg==0.29.0
bcrypt==4.1.1
certifi==2023.11.17
charset-normalizer==3.3.2
click==8.1.7
cloudinary==1.36.0
cryptography==41.0.7
...150 more lines...
```

---

### ✅ **Manual requirements.txt** (Good)

```txt
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

**Benefits:**
1. **Readable** - Clear what packages you actually use
2. **Maintainable** - Easy to update specific packages
3. **Cross-platform** - Works on Mac, Linux, Windows
4. **Comments** - Can document why each package is needed
5. **Flexible** - pip auto-resolves transitive dependencies

---

## ✅ **Best Practice Workflow**

### 1. Use `pip freeze` to IDENTIFY packages:

```bash
cd /path/to/bdd_server
source venv/bin/activate

# See what's installed
pip freeze | grep -i "package-name"
```

### 2. Add ONLY direct dependencies to requirements.txt:

```txt
# What YOU import in your code
fastapi==0.104.1      # from fastapi import FastAPI
sqlalchemy==2.0.23    # from sqlalchemy import ...
cloudinary==1.36.0    # import cloudinary
```

### 3. Use the dependency checker:

```bash
python3 check_requirements.py
```

This script will:
- ✅ Find all imports in your code
- ✅ Check if they're in requirements.txt
- ✅ Tell you what's missing
- ✅ Ignore standard library modules

---

## 🛠️ How to Fix Missing Dependencies

### Step 1: Find the package name

```bash
# Check if it's installed locally
pip show package-name

# Or search PyPI
pip search package-name  # (currently disabled)
# Use: https://pypi.org/search/?q=package-name
```

### Step 2: Find the version

```bash
# In your venv:
pip show package-name | grep Version

# Example output:
# Version: 0.29.0
```

### Step 3: Add to requirements.txt

```txt
# Add with version:
package-name==0.29.0

# Or allow minor updates:
package-name>=0.29.0,<0.30.0

# Or latest:
package-name  # (not recommended for production)
```

---

## 📋 Import Name vs Package Name

Some packages have different import and install names:

| Import | Package Name |
|--------|--------------|
| `import jwt` | `PyJWT` |
| `from jose import jwt` | `python-jose` |
| `import PIL` | `Pillow` |
| `import cv2` | `opencv-python` |
| `import sklearn` | `scikit-learn` |
| `import yaml` | `PyYAML` |
| `from dotenv import` | `python-dotenv` |

**The checker script handles these automatically!**

---

## 🚀 Your Current Workflow

### Before Deployment:

```bash
cd /path/to/bdd_server

# 1. Activate venv
source venv/bin/activate

# 2. Check for missing dependencies
python3 check_requirements.py

# 3. If missing packages found, add them:
pip show package-name  # Get version
# Add to requirements.txt

# 4. Test locally
pip install -r requirements.txt  # In fresh venv
uvicorn app.main:app --reload

# 5. If works, push!
git add requirements.txt
git commit -m "fix: add missing dependencies"
git push
```

---

## 🎯 Requirements.txt Structure

### Good Structure:

```txt
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.7

# File handling
python-magic==0.4.27
pillow==10.1.0
openpyxl==3.1.2
cloudinary==1.36.0

# Utilities
python-decouple==3.8
httpx==0.25.2
geopy==2.4.0
fuzzywuzzy==0.18.0
python-levenshtein==0.23.0

# Development and testing (optional for production)
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
```

**Benefits:**
- ✅ Grouped by purpose
- ✅ Commented sections
- ✅ Easy to find packages
- ✅ Clear what's optional

---

## 🔍 Finding Missing Dependencies

### Method 1: Check imports manually

```bash
# Find all imports in your code
grep -rh "^import \|^from " app/ --include="*.py" | sort -u

# Check each one in requirements.txt
```

### Method 2: Use the checker script

```bash
python3 check_requirements.py
```

### Method 3: Try to import in clean venv

```bash
# Create clean venv
python3 -m venv test_env
source test_env/bin/activate

# Install from requirements
pip install -r requirements.txt

# Try to run
python3 -c "from app.main import app"

# If it fails, add the missing package
deactivate && rm -rf test_env
```

---

## 💡 Pro Tips

### 1. **Pin Major Versions**

```txt
# Good - allows minor updates
fastapi>=0.104.0,<0.105.0

# Better for production - exact version
fastapi==0.104.1
```

### 2. **Separate Dev Dependencies**

```txt
# requirements.txt - production
fastapi==0.104.1
sqlalchemy==2.0.23

# requirements-dev.txt - development only
-r requirements.txt  # Include production deps
pytest==7.4.3
black==23.11.0
ipython==8.12.0
```

### 3. **Document Why**

```txt
# Auth - JWT tokens and password hashing
python-jose[cryptography]==3.3.0  # JWT encoding/decoding
passlib[bcrypt]==1.7.4            # Password hashing

# Database - Async PostgreSQL
sqlalchemy==2.0.23     # ORM
asyncpg==0.29.0        # Async driver
psycopg2-binary==2.9.9 # Sync driver (for Alembic)
```

### 4. **Use Requirements Checker**

Add to your git pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

python3 check_requirements.py || {
    echo "❌ Missing dependencies detected!"
    echo "Run: python3 check_requirements.py"
    exit 1
}
```

---

## 🆘 Common Issues

### Issue: "ModuleNotFoundError: No module named 'xyz'"

**Solution:**
1. Find import: `grep -r "import xyz" app/`
2. Find package: `pip search xyz` or google "xyz python package"
3. Get version: `pip show xyz | grep Version`
4. Add to requirements.txt: `xyz==version`
5. Push to Railway

### Issue: "Package has conflicting dependencies"

**Solution:**
1. Check what needs it: `pip show package-name | grep Required-by`
2. Update parent package version
3. Or pin specific version that works

### Issue: "Requirements too large, build timeout"

**Solution:**
1. Remove dev dependencies (pytest, black, etc.)
2. Use binary packages (psycopg2-binary not psycopg2)
3. Use slimmer alternatives

---

## ✅ Your Checklist

Before every deployment:

- [ ] Run `python3 check_requirements.py`
- [ ] Fix any missing dependencies
- [ ] Test in clean venv locally
- [ ] Pin versions with `==`
- [ ] Group by purpose with comments
- [ ] Remove dev-only packages
- [ ] Push to Railway
- [ ] Monitor deployment logs

---

## 📚 Resources

- [pip documentation](https://pip.pypa.io/en/stable/)
- [requirements.txt format](https://pip.pypa.io/en/stable/reference/requirements-file-format/)
- [PyPI - Python Package Index](https://pypi.org/)

---

**Remember:** Less is more! Only add packages you actually import in your code.

