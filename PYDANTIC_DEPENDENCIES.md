# 📧 Pydantic Email Validation Dependency

## Issue: `ModuleNotFoundError: No module named 'email_validator'`

### Why This Happened

When you use `EmailStr` in Pydantic schemas, Pydantic **lazily imports** `email_validator` at runtime:

```python
from pydantic import BaseModel, EmailStr

class UserPublic(BaseModel):
    email: EmailStr  # ← This triggers email_validator import
```

**The problem:** This is an indirect dependency that the checker can't detect because there's no explicit `import email_validator` in your code.

---

## ✅ Solution

Added to `requirements.txt`:
```txt
email-validator==2.1.2
```

---

## 🔍 Pydantic Optional Dependencies

Pydantic has several optional features that require extra packages:

### Email Validation
```python
from pydantic import EmailStr
# Requires: email-validator
```

### URL Validation
```python
from pydantic import HttpUrl, AnyUrl
# Built-in, no extra package needed
```

### UUID Validation
```python
from uuid import UUID
# Built-in (standard library)
```

### Date/Time
```python
from datetime import datetime
# Built-in (standard library)
```

### Dotenv Settings
```python
from pydantic_settings import BaseSettings
# Requires: pydantic-settings
```

---

## 📋 Common Pydantic Dependencies

If you use these Pydantic features, you need:

| Pydantic Feature | Required Package |
|------------------|------------------|
| `EmailStr` | `email-validator` |
| `pydantic_settings.BaseSettings` | `pydantic-settings` |
| `pydantic.networks.IPvAnyAddress` | Built-in |
| `pydantic.types.FilePath` | Built-in |
| `pydantic.Json` | Built-in |

---

## 🛠️ How to Find These

### Method 1: Read the Error
```
ModuleNotFoundError: No module named 'email_validator'
```
→ Add `email-validator` to requirements.txt

### Method 2: Check Pydantic Docs
See what each type requires:
https://docs.pydantic.dev/latest/api/types/

### Method 3: Test in Clean Environment
```bash
python3 -m venv test_env
source test_env/bin/activate
pip install pydantic
python3 -c "from pydantic import EmailStr"
# Will fail if email-validator not installed
```

---

## ✅ Current Status

All Pydantic dependencies are now in `requirements.txt`:
- ✅ `pydantic==2.5.0` - Core library
- ✅ `pydantic-settings==2.1.0` - For BaseSettings
- ✅ `email-validator==2.1.2` - For EmailStr

---

## 💡 Pro Tip

When adding new Pydantic field types, check if they need extra packages:

```python
# Safe - built-in
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MyModel(BaseModel):
    name: str
    age: int
    created: datetime
    # All built-in types

# Requires package
from pydantic import EmailStr  # Need email-validator

class User(BaseModel):
    email: EmailStr  # ← Add email-validator to requirements.txt
```

---

## 🚀 Deployment Status

Fixed and pushed to Railway. The server should now start successfully! ✅

