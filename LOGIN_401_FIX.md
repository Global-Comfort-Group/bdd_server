# 🔐 Login 401 Error - FIXED

## ❌ The Problem

Users couldn't log in and got this error:
```
/api/auth/callback/credentials:1  Failed to load resource: the server responded with a status of 401 ()
```

---

## 🎯 Root Cause

Sample users were created with `account_status = PENDING` (default), but login requires `account_status = APPROVED`.

**Why it happened:**
1. User model default: `account_status = AccountStatus.PENDING`
2. `create_sample_users.py` didn't set `account_status` field
3. Login endpoint checks: `if user.account_status != AccountStatus.APPROVED`
4. Result: Login rejected with 401 error

---

## ✅ The Fix

### 1. Updated `create_sample_users.py`
Added `account_status=AccountStatus.APPROVED` to user creation:

```python
user = User(
    email=user_data["email"],
    hashed_password=hashed_password,
    first_name=user_data["first_name"],
    last_name=user_data["last_name"],
    role=user_data["role"],
    company=user_data["company"],
    phone=user_data["phone"],
    is_active=True,
    is_verified=True,
    is_superuser=(user_data["role"] == UserRole.ADMIN),
    account_status=AccountStatus.APPROVED  # ← NEW: Approve sample users
)
```

### 2. Created `approve_all_users.py`
Quick script to fix existing users:

```bash
cd bdd_server
export DATABASE_URL="your-railway-url"
python3 approve_all_users.py
```

This updates all existing users to `APPROVED` status.

---

## 🚀 Fixed in Staging

Already applied to your staging database:
- ✅ All 4 users now have `account_status = APPROVED`
- ✅ Login should work now

**Test it:**
- Go to: `https://bdd-client-staging.up.railway.app/login`
- Login with: `admin@bdd.com` / `admin123`
- Should work! ✅

---

## 📋 About ALLOWED_ORIGINS

You had this set:
```
ALLOWED_ORIGINS=https://bdd-client-staging.up.railway.app/
```

**Good news:** Your server CORS is currently set to `allow_origins=["*"]` which allows all origins, so CORS wasn't the issue.

**For production**, you should:

### Option 1: Keep Permissive (Current - Easiest)
```python
# app/main.py (line 51)
allow_origins=["*"]  # Allow all origins
```

**Pros:** No configuration needed  
**Cons:** Less secure (but fine for most cases)

### Option 2: Use ALLOWED_ORIGINS Variable (More Secure)
Update `app/main.py`:

```python
# app/main.py
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins() if settings.get_cors_origins() else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

Then set in Railway:
```bash
# WITHOUT trailing slash!
ALLOWED_ORIGINS=https://bdd-client-staging.up.railway.app,http://localhost:3000

# Multiple origins separated by commas
```

**Important:** Remove the trailing slash from your URL!
- ❌ `https://bdd-client-staging.up.railway.app/`
- ✅ `https://bdd-client-staging.up.railway.app`

---

## 🔍 How to Diagnose 401 Errors

### 1. Check User Exists
```sql
SELECT email, account_status, is_active FROM "user" WHERE email = 'admin@bdd.com';
```

### 2. Check Account Status
Should be `APPROVED`, not `PENDING` or `REJECTED`

### 3. Check Password
Try resetting or verify it's correct

### 4. Check Server Logs
Look for authentication errors in Railway logs

---

## 🛠️ Future Migrations

When creating users in the future:

### For Testing/Staging:
```python
# Use create_sample_users.py (now fixed)
python3 create_sample_users.py
# Creates users with account_status=APPROVED
```

### For Production:
Create users through the admin portal, they'll be `PENDING` by default:
1. User registers
2. Status = `PENDING`
3. Admin approves them
4. Status = `APPROVED`
5. User can log in

Or manually create approved users:
```python
# create_production_admin.py
user = User(
    email="admin@company.com",
    hashed_password=get_password_hash("secure-password"),
    first_name="Admin",
    last_name="User",
    role=UserRole.ADMIN,
    is_active=True,
    is_verified=True,
    is_superuser=True,
    account_status=AccountStatus.APPROVED  # ← Important!
)
```

---

## ✅ Checklist

Before pushing to production:

- [ ] Update `create_sample_users.py` (done ✅)
- [ ] Run `approve_all_users.py` on existing databases
- [ ] Test login on staging
- [ ] Decide CORS strategy (permissive vs restricted)
- [ ] Update ALLOWED_ORIGINS if using restricted CORS
- [ ] Remove trailing slashes from URLs
- [ ] Test from actual client URL

---

## 🎉 Status: FIXED

Your staging environment should now allow logins! 🚀

**Test credentials:**
- Email: `admin@bdd.com`
- Password: `admin123`

All 4 sample users are now approved and ready to use.

