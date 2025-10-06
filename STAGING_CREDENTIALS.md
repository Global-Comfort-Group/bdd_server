# 🔐 Staging Environment - Login Credentials

**Environment:** Staging  
**Database:** `postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway`  
**Migrated:** October 6, 2025

---

## 👥 Test Users

### 🔧 ADMIN PORTAL
```
Email:    admin@bdd.com
Password: admin123
Role:     ADMIN
Purpose:  System administration, user management
```

---

### 🏢 PROPERTY MANAGEMENT PORTAL

#### BDD User (Internal Operations)
```
Email:    bdd.user@bdd.com
Password: bdduser123
Role:     BDD_USER
Purpose:  Full property access, internal BDD operations
```

#### Agent (Submit Properties)
```
Email:    agent@realty.com
Password: agent123
Role:     AGENT
Purpose:  Submit properties, track submissions
```

#### Broker (Review Properties)
```
Email:    broker@brokers.com
Password: broker123
Role:     BROKER
Purpose:  Review properties, approve/reject submissions
```

---

## 📊 Database Tables Created

1. `user` - User accounts and authentication
2. `properties` - Property listings
3. `property_attachments` - Property files/images
4. `addresses` - Property addresses (detailed)
5. `workflow_history` - Property status changes
6. `nego_tables` - Negotiation tables
7. `negotiation_entries` - Negotiation records
8. `negotiation_chronicle_attachments` - Negotiation files
9. `notifications` - User notifications
10. `activity_logs` - System activity logs

---

## 🚀 Next Steps

1. **Deploy Server to Railway:**
   ```bash
   cd bdd_server
   git push origin main
   # Railway auto-deploys
   ```

2. **Set Railway Environment Variables:**
   - `DATABASE_URL`: Already set (auto from Railway Postgres)
   - `SECRET_KEY`: Generate new one for staging
   - `CLOUDINARY_*`: Your Cloudinary credentials

3. **Test Login:**
   - Go to your Railway client URL
   - Login with `admin@bdd.com` / `admin123`
   - Verify dashboard loads

4. **Change Passwords (Optional for Staging):**
   - Login as admin
   - Go to Users management
   - Update passwords for all test users

---

## ⚠️ Security Reminder

- ✅ These are **TEST CREDENTIALS** for staging
- ✅ Safe to use for development/testing
- ❌ **DO NOT** use these passwords in production
- ❌ **DO NOT** commit this file to Git (it's in .gitignore)

---

## 🔄 To Re-migrate (Reset Database)

If you need to reset the staging database:

```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
source venv/bin/activate

export DATABASE_URL="postgresql://postgres:SUABxhWFDiaDfMVLnMDssTXscWnxyqqH@trolley.proxy.rlwy.net:15142/railway"

python3 create_tables.py
python3 create_sample_users.py
```

See `DATABASE_MIGRATION_GUIDE.md` for detailed instructions.

