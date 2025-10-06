# Activity Logging System - Complete Guide

## 📋 Overview

The Activity Logging system tracks all user actions and system events in your BDD Property Tracker application. This includes logins, property creations, user management, and more.

---

## 🗄️ Database Schema

### `activity_logs` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `user_id` | Integer (FK) | User who performed the action |
| `action` | Enum | Type of action (LOGIN, CREATE, UPDATE, etc.) |
| `resource_type` | Enum | Type of resource (USER, PROPERTY, SYSTEM, etc.) |
| `resource_id` | Integer | ID of the affected resource (optional) |
| `details` | Text | Human-readable description |
| `ip_address` | String(45) | Client IP address (optional) |
| `user_agent` | String(500) | Browser user agent (optional) |
| `created_at` | DateTime | When the action occurred |

---

## 🎯 Activity Actions

- `LOGIN` - User logged in
- `LOGOUT` - User logged out
- `CREATE` - Resource created
- `READ` - Resource accessed
- `UPDATE` - Resource updated
- `DELETE` - Resource deleted
- `ACTIVATE` - User activated
- `DEACTIVATE` - User deactivated
- `ROLE_CHANGE` - User role changed
- `PASSWORD_CHANGE` - Password changed
- `EXPORT` - Data exported
- `APPROVE` - Resource approved
- `REJECT` - Resource rejected
- `STATUS_CHANGE` - Status changed

## 📦 Resource Types

- `USER` - User management actions
- `PROPERTY` - Property management actions
- `NEGO_TABLE` - Negotiation table actions
- `NEGOTIATION_CHRONICLE` - Negotiation chronicle actions
- `SYSTEM` - System-level actions
- `DUPLICATE` - Duplicate detection actions
- `NOTIFICATION` - Notification actions

---

## 🚀 How to Use

### 1. Import the Activity Logger

```python
from app.utils.activity_logger import log_activity, log_login, log_property_created
from app.models.activity_log import ActivityAction, ResourceType
```

### 2. Log Activities in Your API Endpoints

#### Example 1: Log User Login

```python
from app.utils.activity_logger import log_login

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    # ... authentication logic ...
    
    # Log the login
    await log_login(
        db=db,
        user_id=user.id,
        user_email=user.email,
        request=request
    )
    
    return {"access_token": token, "user": user_data}
```

#### Example 2: Log Property Creation

```python
from app.utils.activity_logger import log_property_created

@router.post("/properties-submit/")
async def create_property(
    name: str = Form(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ... create property logic ...
    
    # Log the creation
    await log_property_created(
        db=db,
        user_id=current_user.id,
        property_id=property.id,
        property_name=property.name,
        request=request
    )
    
    return property
```

#### Example 3: Log User Updates

```python
from app.utils.activity_logger import log_user_updated

@router.patch("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ... update user logic ...
    
    # Build changes description
    changes = []
    if user_update.first_name:
        changes.append(f"first_name: {user.first_name} → {user_update.first_name}")
    if user_update.role:
        changes.append(f"role: {user.role} → {user_update.role}")
    
    # Log the update
    await log_user_updated(
        db=db,
        admin_id=current_user.id,
        updated_user_id=user_id,
        updated_user_email=user.email,
        changes=", ".join(changes),
        request=request
    )
    
    return updated_user
```

#### Example 4: Custom Activity Log

```python
from app.utils.activity_logger import log_activity
from app.models.activity_log import ActivityAction, ResourceType

@router.post("/duplicates/merge")
async def merge_duplicates(
    primary_id: int,
    duplicate_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # ... merge logic ...
    
    # Log the merge operation
    await log_activity(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.UPDATE,
        resource_type=ResourceType.DUPLICATE,
        details=f"Merged property {duplicate_id} into {primary_id}",
        resource_id=primary_id,
        request=request
    )
    
    return {"message": "Properties merged successfully"}
```

---

## 🔍 Querying Activity Logs (Admin API)

### Get All Logs

```bash
GET /admin/activity-logs?limit=50&skip=0
```

### Filter by User

```bash
GET /admin/activity-logs?user_id=123&limit=50
```

### Filter by Action

```bash
GET /admin/activity-logs?action=LOGIN&limit=50
```

### Filter by Date Range

```bash
GET /admin/activity-logs?date_from=2025-01-01&date_to=2025-12-31
```

### Get Activity Statistics

```bash
GET /admin/activity-logs/stats
```

Returns:
```json
{
  "total_activities": 5420,
  "recent_logins": 23,
  "actions_by_type": {
    "LOGIN": 450,
    "CREATE": 320,
    "UPDATE": 890
  },
  "users_active_today": 15,
  "most_active_users": [
    {
      "user_id": 5,
      "user_name": "John Doe",
      "user_email": "john@example.com",
      "activity_count": 124
    }
  ]
}
```

### Export Logs as CSV

```bash
GET /admin/activity-logs/export?date_from=2025-01-01
```

---

## 🛠️ Helper Functions Available

| Function | Description |
|----------|-------------|
| `log_login()` | Log user login |
| `log_logout()` | Log user logout |
| `log_user_created()` | Log user creation |
| `log_user_updated()` | Log user update |
| `log_user_deleted()` | Log user deletion |
| `log_property_created()` | Log property creation |
| `log_property_updated()` | Log property update |
| `log_property_status_changed()` | Log property status change |
| `log_role_change()` | Log user role change |
| `log_data_export()` | Log data export |
| `log_activity()` | Generic activity logger |

---

## 🎨 Frontend Integration

### View Activity Logs (Admin Only)

The admin dashboard includes a comprehensive Activity Log viewer at:
```
/admin/activity-logs
```

Features:
- ✅ Real-time activity monitoring
- ✅ Advanced filtering (user, action, date range)
- ✅ Activity statistics dashboard
- ✅ CSV export functionality
- ✅ Detailed activity information

### Activity Log Component

```tsx
import { ActivityLogViewer } from '@/components/admin/ActivityLogViewer'

export default function ActivityPage() {
  return (
    <ActivityLogViewer 
      title="System Activity Logs" 
      showStats={true} 
    />
  )
}
```

---

## 📊 Performance Optimization

### Indexes

The activity_logs table has indexes on:
- `user_id` - Fast user-specific queries
- `action` - Filter by action type
- `resource_type` - Filter by resource
- `resource_id` - Find logs for specific resources
- `created_at` - Date-range queries

### Auto-Cleanup

Delete logs older than 90 days:
```bash
DELETE /admin/activity-logs/cleanup?days=90
```

---

## 🔒 Security Considerations

1. **Admin-Only Access**: All activity log endpoints require `ADMIN` role
2. **IP & User Agent Tracking**: Helps identify suspicious activities
3. **Immutable Logs**: Activity logs cannot be edited or deleted individually
4. **Cascade Deletion**: When a user is deleted, their logs remain with `user_id = NULL`

---

## 📝 Best Practices

1. **Always log authentication events**
   ```python
   await log_login(db, user_id, user_email, request)
   ```

2. **Log all CRUD operations on important resources**
   ```python
   await log_property_created(db, user_id, property_id, property_name, request)
   ```

3. **Include descriptive details**
   ```python
   details=f"Updated property '{property.name}': Changed status from {old_status} to {new_status}"
   ```

4. **Pass request object for IP/User-Agent tracking**
   ```python
   await log_activity(db, user_id, action, resource_type, details, request=request)
   ```

5. **Regular cleanup of old logs**
   - Set up a cron job to clean logs older than 90 days
   - Or manually trigger via admin panel

---

## 🧪 Testing

```python
# tests/test_activity_logs.py
import pytest
from app.utils.activity_logger import log_activity
from app.models.activity_log import ActivityAction, ResourceType

@pytest.mark.asyncio
async def test_activity_log_creation(db_session):
    await log_activity(
        db=db_session,
        user_id=1,
        action=ActivityAction.CREATE,
        resource_type=ResourceType.PROPERTY,
        details="Test property created",
        resource_id=123
    )
    
    # Query and verify
    result = await db_session.execute(
        select(ActivityLog).where(ActivityLog.user_id == 1)
    )
    log = result.scalar_one()
    
    assert log.action == ActivityAction.CREATE
    assert log.resource_type == ResourceType.PROPERTY
    assert log.details == "Test property created"
```

---

## 🚢 Deployment

1. **Run Migration**:
   ```bash
   alembic upgrade head
   ```

2. **Restart Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Verify**:
   - Check `/admin/activity-logs/stats` endpoint
   - Test logging in the admin panel
   - Verify logs appear in the Activity Logs page

---

## 📞 Support

For issues or questions:
1. Check the logs in `/admin/activity-logs`
2. Review the API documentation at `/docs`
3. Contact the development team

---

## ✅ Checklist for Implementation

- [x] Database model created
- [x] Migration file created
- [x] API endpoints implemented
- [x] Activity logger utilities created
- [x] Frontend component connected
- [x] Navigation menu updated
- [x] Documentation complete

**Status**: ✅ Fully implemented and ready to use!





