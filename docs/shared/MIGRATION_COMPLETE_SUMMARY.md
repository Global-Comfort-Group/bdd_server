# ✅ Staging Database Migration - COMPLETE

## 🎉 What I Just Did for You

### ✅ Migrated Your Staging Database

**Database:** `postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway`

**Created:**
- ✅ 10 database tables (users, properties, negotiations, etc.)
- ✅ 4 test user accounts

---

## 🔐 Your Staging Login Credentials

### Admin Portal:
```
Email:    admin@bdd.com
Password: admin123
Role:     ADMIN
```

### Property Management Portal:
```
Email:    bdd.user@bdd.com
Password: bdduser123
Role:     BDD_USER

Email:    agent@realty.com
Password: agent123
Role:     AGENT

Email:    broker@brokers.com
Password: broker123
Role:     BROKER
```

**💾 Save these!** You'll need them to test your staging environment.

---

## 📚 How to Do This Yourself Next Time

I created 3 files to help you:

### 1. **`DATABASE_MIGRATION_GUIDE.md`** (Complete Tutorial)
   - Step-by-step instructions
   - Detailed explanations
   - Troubleshooting guide
   - Best practices

**Location:** `/bdd_server/DATABASE_MIGRATION_GUIDE.md`

---

### 2. **`QUICK_MIGRATE.sh`** (Automated Script)
   - One-click migration
   - Safety checks included
   - Color-coded output

**How to use:**
```bash
cd /path/to/bdd_server

# 1. Edit the script and set your DATABASE_URL
nano QUICK_MIGRATE.sh
# Change line 23: DATABASE_URL="your-database-url-here"

# 2. Run it
./QUICK_MIGRATE.sh
```

---

### 3. **`STAGING_CREDENTIALS.md`** (Your Saved Credentials)
   - Contains all staging login info
   - Saved locally (not in Git for security)

**Location:** `/bdd_server/STAGING_CREDENTIALS.md`

---

## 🚀 Quick Migration Reference

### For Next Time (Copy-Paste Ready):

```bash
# 1. Navigate to server
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set database URL (get from Railway)
export DATABASE_URL="postgresql://postgres:PASSWORD@HOST:PORT/railway"

# 4. Create tables
python3 create_tables.py

# 5. Create users
python3 create_sample_users.py

# Done! ✅
```

**That's it!** Just 5 commands.

---

## 📋 What Gets Created

### Tables:
1. `user` - User accounts
2. `properties` - Property listings
3. `property_attachments` - Files/images
4. `addresses` - Detailed addresses
5. `workflow_history` - Status changes
6. `nego_tables` - Negotiation tables
7. `negotiation_entries` - Negotiations
8. `negotiation_chronicle_attachments` - Negotiation files
9. `notifications` - User notifications
10. `activity_logs` - Activity tracking

### Users:
- 1 Admin (full system access)
- 1 BDD User (internal operations)
- 1 Agent (submit properties)
- 1 Broker (review properties)

---

## 🎯 When to Run Migrations

### Run migrations when you:
- ✅ Create a new Railway database
- ✅ Want to reset/clean your database
- ✅ Deploy to a new environment (staging, production)
- ✅ Need fresh test data

### ⚠️ Be careful because:
- ❌ **Drops all existing tables** (deletes data!)
- ❌ Make backups before production migrations
- ❌ Test on staging first

---

## 🔄 Different Environments

### Staging (What we just did):
```bash
export DATABASE_URL="postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway"
python3 create_tables.py
python3 create_sample_users.py
```

### Production (Future):
```bash
export DATABASE_URL="your-production-database-url"
python3 create_tables.py
# Don't use create_sample_users.py in production!
# Create real users manually or with a custom script
```

### Local Development:
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/bdd_property_tracker"
python3 create_tables.py
python3 create_sample_users.py
```

---

## 🛠️ Tools I Created for You

### 1. Automated Script (`QUICK_MIGRATE.sh`)
```bash
./QUICK_MIGRATE.sh
```
- ✅ Safety checks
- ✅ Color-coded output
- ✅ Error handling
- ✅ Step-by-step progress

### 2. Manual Commands (If you prefer control)
```bash
cd /path/to/bdd_server
source venv/bin/activate
export DATABASE_URL="your-url"
python3 create_tables.py
python3 create_sample_users.py
```

**Both ways work!** Use whichever you prefer.

---

## 💡 Pro Tips

### 1. **Save Your Database URLs**
Create a file (NOT in Git) with your database URLs:

```bash
# ~/.railway_databases (example)
STAGING_DB="postgresql://postgres:PASSWORD@HOST:PORT/railway"
PRODUCTION_DB="postgresql://postgres:PASSWORD@HOST:PORT/railway"
LOCAL_DB="postgresql://postgres:postgres@localhost:5432/bdd"
```

Then:
```bash
export DATABASE_URL=$(grep STAGING_DB ~/.railway_databases | cut -d'=' -f2 | tr -d '"')
```

---

### 2. **Backup Before Migration**
```bash
# Backup existing database
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
psql "$DATABASE_URL" < backup_20250106_123456.sql
```

---

### 3. **Create Custom Users**
For production, don't use the sample users script. Create your own:

```python
# create_production_admin.py
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email="your-email@company.com",
            hashed_password=get_password_hash("secure-password"),
            first_name="Your",
            last_name="Name",
            role=UserRole.ADMIN,
            company="Your Company",
            is_active=True,
            is_verified=True,
            is_superuser=True
        )
        db.add(admin)
        await db.commit()
        print("✅ Production admin created!")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

---

## 🐛 Troubleshooting

### Problem: "Could not connect to database"
**Solution:** Check your DATABASE_URL is correct

### Problem: "asyncpg not installed"
**Solution:** `pip install -r requirements.txt`

### Problem: "User already exists"
**Solution:** This is normal! Script skips existing users

### Problem: "Permission denied: ./QUICK_MIGRATE.sh"
**Solution:** `chmod +x QUICK_MIGRATE.sh`

---

## 📖 Read the Full Guide

For complete details, troubleshooting, and advanced topics:

**Open:** `bdd_server/DATABASE_MIGRATION_GUIDE.md`

It includes:
- Detailed explanations
- What each script does
- Security best practices
- Backup/restore procedures
- Custom user creation
- Production considerations

---

## ✅ Your Next Steps

1. **Test Staging Environment:**
   ```bash
   # Your staging server URL (from Railway)
   https://your-staging-server.railway.app
   
   # Login with:
   admin@bdd.com / admin123
   ```

2. **Deploy Server to Railway:**
   ```bash
   git push origin staging  # (already done!)
   # Railway auto-deploys
   ```

3. **Update Railway Environment Variables:**
   - Go to Railway → Your Service → Variables
   - `DATABASE_URL` should auto-reference Postgres
   - Add other variables (SECRET_KEY, CLOUDINARY_*, etc.)

4. **Test All Features:**
   - Login with each test user
   - Create a property
   - Upload files
   - Test negotiations
   - Verify everything works

---

## 🎓 Summary

### What You Learned:
1. ✅ How to get Railway database URL
2. ✅ How to run migration scripts
3. ✅ How to create database tables
4. ✅ How to create sample users
5. ✅ How to use the automated script

### What You Can Do Now:
- ✅ Migrate any Railway database yourself
- ✅ Reset databases when needed
- ✅ Set up new environments (staging, prod)
- ✅ Troubleshoot migration issues

### Next Time:
```bash
cd bdd_server
source venv/bin/activate
export DATABASE_URL="your-url"
python3 create_tables.py
python3 create_sample_users.py
```

**That's it!** You're now a database migration pro! 🎉

---

## 📞 Need Help?

If you get stuck:
1. Check `DATABASE_MIGRATION_GUIDE.md` (comprehensive guide)
2. Check troubleshooting section above
3. Verify DATABASE_URL is correct
4. Check Railway logs for errors
5. Make sure venv is activated

---

**You're all set!** Your staging database is ready to go. 🚀

