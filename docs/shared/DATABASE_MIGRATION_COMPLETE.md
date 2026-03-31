# ✅ Database Migration Complete!

## 🎉 Success Summary

Your Railway PostgreSQL database has been fully set up with:
- ✅ Complete schema (all tables created)
- ✅ Sample users for testing
- ✅ Ready for production use

---

## 👥 Sample Users Created

### 🔧 Admin Portal Access

**System Administrator**
- **Email:** `admin@bdd.com`
- **Password:** `admin123`
- **Role:** ADMIN
- **Access:** Full system administration, user management, system settings
- **Portal:** Admin Portal (Separate)

---

### 🏢 Property Management Portal Access

**BDD Internal User**
- **Email:** `bdd.user@bdd.com`
- **Password:** `bdduser123`
- **Role:** BDD_USER
- **Access:** Full property access, can manage all properties, assign reviewers
- **Portal:** Main Property Management

**Property Agent**
- **Email:** `agent@realty.com`
- **Password:** `agent123`
- **Role:** AGENT
- **Access:** Submit properties, track own submissions
- **Portal:** Main Property Management

**Property Broker**
- **Email:** `broker@brokers.com`
- **Password:** `broker123`
- **Role:** BROKER
- **Access:** Review and approve/reject properties, manage agent submissions
- **Portal:** Main Property Management

---

## 📊 Database Status

```
Railway PostgreSQL Database
├── Schema: ✅ Migrated (all 11 tables)
├── Users: ✅ 4 sample users created
├── Properties: Empty (ready for data)
├── Notifications: Empty (ready for data)
└── Activity Logs: Empty (will auto-populate)
```

---

## 🚀 How to Add More Users

### Option 1: Via API (Production Way)

Use your API registration endpoint:

```bash
curl -X POST "https://your-app.up.railway.app/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepassword",
    "firstName": "John",
    "lastName": "Doe",
    "role": "AGENT",
    "company": "Realty Company",
    "phone": "+63917000005"
  }'
```

### Option 2: Via Script (Development)

```bash
cd /path/to/bdd_server
export DATABASE_URL="your-railway-database-url"
python3 create_sample_users.py
```

Edit the script to add more users as needed.

### Option 3: Via Railway Console

1. Go to Railway Dashboard
2. Click your PostgreSQL database
3. Click "Data" tab
4. Click "Query"
5. Run SQL:

```sql
INSERT INTO "user" (
  email, hashed_password, first_name, last_name, 
  role, company, phone, is_active, is_verified
) VALUES (
  'newuser@example.com',
  '$2b$12$...',  -- Use bcrypt hashed password
  'First',
  'Last',
  'AGENT',
  'Company Name',
  '+63917000000',
  true,
  true
);
```

---

## 📝 How to Migrate Existing Data

If you have data from another database and want to import it:

### Step 1: Export from Source Database

```bash
# Export specific tables
pg_dump -h source-host -U source-user -d source-db \
  -t user -t properties -t nego_tables \
  --data-only --column-inserts > data_export.sql

# Or export all data
pg_dump -h source-host -U source-user -d source-db \
  --data-only --column-inserts > full_data_export.sql
```

### Step 2: Clean Export File

Open `data_export.sql` and:
1. Remove any existing user inserts if you want to keep sample users
2. Adjust IDs if needed
3. Check foreign key references

### Step 3: Import to Railway

```bash
# Set Railway database URL
export DATABASE_URL="postgresql://postgres:RDoeukTnCyVUWNCezEtduSBUllXPDQbw@yamanote.proxy.rlwy.net:12820/railway"

# Import data
psql $DATABASE_URL < data_export.sql
```

### Step 4: Fix Sequences (Important!)

After importing, reset auto-increment sequences:

```bash
psql $DATABASE_URL << 'EOF'
-- Reset sequences for all tables
SELECT setval('"user_id_seq"', (SELECT MAX(id) FROM "user"));
SELECT setval('properties_id_seq', (SELECT MAX(id) FROM properties));
SELECT setval('nego_tables_id_seq', (SELECT MAX(id) FROM nego_tables));
-- Add more as needed
EOF
```

---

## 🔐 Security Recommendations

### 1. Change Default Passwords

After initial setup, change all sample user passwords:

**Via API:**
```bash
curl -X POST "https://your-app.up.railway.app/api/v1/auth/change-password" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "NewSecurePassword123!"
  }'
```

**Via Database:**
```sql
-- Generate new bcrypt hash using Python:
-- python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('NewPassword123!'))"

UPDATE "user" 
SET hashed_password = '$2b$12$...' 
WHERE email = 'admin@bdd.com';
```

### 2. Rotate Database Credentials

Your database URL was shared publicly. Rotate it:

1. Go to Railway Dashboard
2. Click PostgreSQL service
3. Settings → Danger Zone
4. "Reset Database Password"
5. Update environment variables in your server deployment

### 3. Enable Account Approval Workflow

By default, new registrations should require approval:

```python
# This is already configured in your app
# New users get account_status = PENDING
# Admin must approve via admin portal
```

---

## 🧪 Test Your Setup

### 1. Test Login

```bash
# Admin login
curl -X POST "https://your-app.up.railway.app/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@bdd.com",
    "password": "admin123"
  }'

# Should return JWT token
```

### 2. Test Protected Endpoint

```bash
# Get current user info
curl "https://your-app.up.railway.app/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Test Frontend Login

1. Open your Next.js app
2. Navigate to login page
3. Use any of the sample credentials
4. Should successfully log in and redirect to dashboard

---

## 📚 Next Steps

### For Development:

1. **Test All Features:**
   - User authentication
   - Property submission
   - File uploads (Cloudinary)
   - Admin portal
   - Activity logs

2. **Add Real Data:**
   - Create actual properties
   - Upload documents
   - Test workflows

3. **Configure Frontend:**
   - Update API endpoint URLs
   - Set up environment variables
   - Deploy to Vercel/Netlify

### For Production:

1. **Security Hardening:**
   - ✅ Change all default passwords
   - ✅ Rotate database credentials
   - ✅ Set up proper CORS origins
   - ✅ Enable rate limiting
   - ✅ Set up monitoring

2. **Backup Strategy:**
   ```bash
   # Schedule daily backups
   # Railway provides automatic backups
   # Or use pg_dump cron job:
   
   0 2 * * * pg_dump $DATABASE_URL > backup_$(date +\%Y\%m\%d).sql
   ```

3. **Monitoring:**
   - Set up Railway alerts
   - Monitor database size
   - Track API usage
   - Monitor error rates

---

## 🔧 Troubleshooting

### Issue: "User already exists"

**Cause:** Running create_sample_users.py multiple times

**Solution:** Script automatically skips existing users. To recreate:

```sql
-- Delete existing users (careful!)
DELETE FROM "user" WHERE email LIKE '%@bdd.com%';

-- Then re-run the script
python3 create_sample_users.py
```

### Issue: "Cannot login with sample credentials"

**Cause:** Password hashing issue or wrong credentials

**Solution:**

1. Verify user exists:
   ```sql
   SELECT email, role, account_status FROM "user";
   ```

2. Check account status is not PENDING
3. Reset password via admin

### Issue: "Foreign key constraint violation"

**Cause:** Importing data with wrong IDs or missing references

**Solution:**

1. Import users first
2. Then properties
3. Then related tables
4. Fix sequences after import

---

## 📞 Reference

### Database Connection

```
Host: yamanote.proxy.rlwy.net
Port: 12820
Database: railway
User: postgres
Password: [Rotate this after public exposure!]
```

### Important Files

- `create_sample_users.py` - Create/recreate users
- `create_tables.py` - Recreate full schema
- `alembic/` - Database migrations

### Environment Variables

```bash
DATABASE_URL=postgresql://postgres:PASSWORD@HOST:PORT/railway
SECRET_KEY=your-jwt-secret-key
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

---

## ✅ Checklist

Before going live:

- [x] Database schema migrated
- [x] Sample users created  
- [ ] Default passwords changed
- [ ] Database credentials rotated
- [ ] Frontend connected to API
- [ ] Cloudinary configured
- [ ] CORS origins set
- [ ] SSL/HTTPS enabled
- [ ] Monitoring set up
- [ ] Backup strategy in place

---

**Migration Date:** October 6, 2025  
**Database:** Railway PostgreSQL  
**Status:** ✅ Ready for Development/Testing  
**Next:** Change passwords and deploy frontend!

---

## 🎉 You're All Set!

Your BDD Property Tracker database is now live on Railway with sample users ready for testing. You can now:

1. Deploy your FastAPI backend to Railway
2. Connect your Next.js frontend
3. Start testing the full application
4. Add real users and properties

**Remember:** Change those default passwords before going to production! 🔐

