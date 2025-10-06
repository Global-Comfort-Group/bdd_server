# 🗄️ Database Migration Guide - Do It Yourself

## 📋 Overview

This guide teaches you how to migrate your database schemas and data to a new Railway database (staging, production, or any environment).

---

## 🎯 What We're Going to Do

1. **Create database tables** (schema migration)
2. **Populate with sample users** (data migration)
3. **Verify the migration** (optional but recommended)

---

## 🛠️ Prerequisites

Before starting, you need:

1. ✅ **Railway database URL** 
   - Format: `postgresql://user:password@host:port/database`
   - Get this from Railway dashboard → Database → Connection → Public URL

2. ✅ **Server codebase** with migration scripts:
   - `create_tables.py` - Creates all tables
   - `create_sample_users.py` - Creates test users

3. ✅ **Python virtual environment** activated:
   ```bash
   cd /path/to/bdd_server
   source venv/bin/activate  # Mac/Linux
   # OR
   venv\Scripts\activate     # Windows
   ```

---

## 📝 Step-by-Step Migration Process

### Step 1: Get Your Database URL

From Railway dashboard:
```
Railway → Your Database → Connect → Public URL (copy)
```

Example URL:
```
postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway
```

**⚠️ IMPORTANT:** This URL is secret! Never commit it to Git.

---

### Step 2: Navigate to Server Directory

```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server

# Verify you're in the right place
ls -la *.py | grep create
# Should show: create_tables.py and create_sample_users.py
```

---

### Step 3: Activate Virtual Environment

```bash
source venv/bin/activate

# Verify it's activated (you should see (venv) in your prompt)
which python3
# Should show: .../bdd_server/venv/bin/python3
```

---

### Step 4: Create Database Tables

**Option A: Temporary Environment Variable (Recommended)**

```bash
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
python3 create_tables.py
```

**Option B: One-liner (My Preferred Method)**

```bash
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway" python3 create_tables.py
```

**Expected Output:**
```
Creating database tables...
Dropping existing tables...
Dropped existing tables
Creating new tables...
Created all tables
✅ Database tables created successfully!

Created tables:
  - user
  - properties
  - property_attachments
  - addresses
  - workflow_history
  - nego_tables
  - negotiation_entries
  - negotiation_chronicle_attachments
  - notifications
  - activity_logs
```

**⚠️ Warning:** This script **drops all existing tables** first! Make sure you're migrating to the correct database.

---

### Step 5: Create Sample Users

```bash
# Same DATABASE_URL from Step 4
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
python3 create_sample_users.py
```

**Expected Output:**
```
✅ Created user: admin@bdd.com (ADMIN)
✅ Created user: bdd.user@bdd.com (BDD_USER)
✅ Created user: agent@realty.com (AGENT)
✅ Created user: broker@brokers.com (BROKER)

🎉 Successfully created 4 sample users!

📝 Login Credentials:
==================================================

🔧 ADMIN PORTAL:
  Email: admin@bdd.com
  Password: admin123
  Role: ADMIN

🏢 PROPERTY MANAGEMENT PORTAL:
  Email: bdd.user@bdd.com
  Password: bdduser123
  Role: BDD_USER

  Email: agent@realty.com
  Password: agent123
  Role: AGENT

  Email: broker@brokers.com
  Password: broker123
  Role: BROKER
```

**💾 SAVE THESE CREDENTIALS!** You'll need them to log in.

---

### Step 6: Verify Migration (Optional)

Connect to your database and verify:

```bash
# Using psql (PostgreSQL command-line tool)
psql "postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"

# Once connected, run:
\dt                          # List all tables
SELECT email, role FROM "user";   # List users
\q                           # Quit
```

Or use a GUI tool like **TablePlus**, **pgAdmin**, or **DBeaver**.

---

## 🔄 Complete Migration Script (Copy-Paste Ready)

For **quick migrations**, use this all-in-one script:

```bash
#!/bin/bash
# Save this as: migrate_database.sh

# 1. Set variables
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR_HOST:PORT/railway"
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server

# 2. Activate venv
source venv/bin/activate

# 3. Create tables
echo "📦 Creating database tables..."
DATABASE_URL="$DATABASE_URL" python3 create_tables.py

# 4. Create users
echo ""
echo "👥 Creating sample users..."
DATABASE_URL="$DATABASE_URL" python3 create_sample_users.py

# 5. Done
echo ""
echo "✅ Migration complete!"
echo "🔐 Check the output above for login credentials"
```

**Usage:**
```bash
# Make it executable
chmod +x migrate_database.sh

# Edit the DATABASE_URL
nano migrate_database.sh

# Run it
./migrate_database.sh
```

---

## 🎯 Quick Reference Commands

### Migrate to **Staging**:
```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
source venv/bin/activate

export DATABASE_URL="postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway"

python3 create_tables.py
python3 create_sample_users.py
```

### Migrate to **Production**:
```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
source venv/bin/activate

export DATABASE_URL="your-production-database-url"

python3 create_tables.py
python3 create_sample_users.py
```

### Migrate to **Local Dev**:
```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
source venv/bin/activate

export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bdd_property_tracker"

python3 create_tables.py
python3 create_sample_users.py
```

---

## ⚠️ Important Notes

### 1. **Database URL Security**
- ❌ **Never** commit DATABASE_URL to Git
- ❌ **Never** share it publicly
- ✅ Use environment variables
- ✅ Use Railway's Variables section for deployment

### 2. **Data Loss Warning**
`create_tables.py` **DROPS ALL TABLES** before creating new ones:
```python
# This deletes everything!
await conn.run_sync(Base.metadata.drop_all)
```

**Before running on production:**
1. ✅ Backup your data
2. ✅ Verify you have the correct DATABASE_URL
3. ✅ Test on staging first

### 3. **User Passwords**
The sample users have **simple passwords** (`admin123`, `bdduser123`, etc.):
- ✅ **Fine for staging/development**
- ❌ **NOT secure for production**
- 🔒 **Change them immediately in production!**

---

## 🐛 Troubleshooting

### Error: "relation does not exist"
**Problem:** Tables weren't created properly

**Solution:**
```bash
# Re-run create_tables.py
python3 create_tables.py
```

---

### Error: "could not connect to server"
**Problem:** Wrong database URL or network issue

**Solution:**
1. Check DATABASE_URL is correct
2. Verify Railway database is running
3. Check your internet connection

---

### Error: "UNIQUE constraint violation"
**Problem:** User already exists

**Solution:** Script will skip existing users automatically:
```
⚠️  User already exists: admin@bdd.com
```
This is normal if you run the script multiple times.

---

### Error: "asyncpg is not installed"
**Problem:** Missing dependency

**Solution:**
```bash
pip install asyncpg
# Or reinstall all requirements
pip install -r requirements.txt
```

---

## 📚 Understanding the Migration Scripts

### `create_tables.py` - What it does:

1. **Imports all models** (User, Property, etc.)
2. **Drops existing tables** (⚠️ deletes data)
3. **Creates new tables** from model definitions
4. **Lists created tables**

```python
# Core logic:
async with async_engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)    # Delete old
    await conn.run_sync(Base.metadata.create_all)  # Create new
```

---

### `create_sample_users.py` - What it does:

1. **Checks for existing users** (by email)
2. **Hashes passwords** securely (bcrypt)
3. **Creates 4 test users**:
   - 1 Admin (system administration)
   - 1 BDD User (internal operations)
   - 1 Agent (submit properties)
   - 1 Broker (review properties)
4. **Displays login credentials**

```python
# Core logic:
hashed_password = get_password_hash(user_data["password"])
user = User(email=..., hashed_password=..., ...)
db.add(user)
await db.commit()
```

---

## 🎓 Pro Tips

### 1. **Create a Custom User Script**

For production, create your own user script:

```python
# create_production_users.py
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import get_password_hash

async def create_production_users():
    async with AsyncSessionLocal() as db:
        # Create your real admin
        admin = User(
            email="your-real-email@company.com",
            hashed_password=get_password_hash("secure-password-here"),
            first_name="Your",
            last_name="Name",
            role=UserRole.ADMIN,
            company="Your Company",
            phone="+63917000001",
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        db.add(admin)
        await db.commit()
        print("✅ Production admin created!")

if __name__ == "__main__":
    asyncio.run(create_production_users())
```

---

### 2. **Backup Before Migration**

```bash
# Backup existing database (if it has data)
pg_dump "postgresql://USER:PASS@HOST:PORT/DB" > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
psql "postgresql://USER:PASS@HOST:PORT/DB" < backup_20250106_123456.sql
```

---

### 3. **Use Railway Variables**

In Railway, set `DATABASE_URL` as an environment variable:
```
Railway → Your Service → Variables → Add Variable
Name: DATABASE_URL
Value: ${{Postgres.DATABASE_URL}}  (automatic reference)
```

Your code will automatically use it without hardcoding.

---

## ✅ Migration Checklist

Use this checklist every time you migrate:

- [ ] Get Railway database URL
- [ ] Navigate to `bdd_server` directory
- [ ] Activate virtual environment (`source venv/bin/activate`)
- [ ] Set `DATABASE_URL` environment variable
- [ ] Run `python3 create_tables.py`
- [ ] Verify tables created successfully
- [ ] Run `python3 create_sample_users.py`
- [ ] Save the displayed login credentials
- [ ] Test login with one of the users
- [ ] Update Railway service environment variables if needed
- [ ] Deploy your server to Railway

---

## 🎉 You're Done!

Your staging database now has:
- ✅ All database tables
- ✅ 4 test users (admin, bdd_user, agent, broker)
- ✅ Ready for development/testing

**Next Steps:**
1. Deploy your server to Railway
2. Set `DATABASE_URL` in Railway environment variables
3. Test login with the sample users
4. Start building features!

---

## 📞 Need Help?

If you run into issues:
1. Check the troubleshooting section above
2. Verify your DATABASE_URL is correct
3. Check Railway logs for errors
4. Run `python3 check_requirements.py` to verify dependencies

---

**Remember:** Practice on staging before touching production! 🎯

