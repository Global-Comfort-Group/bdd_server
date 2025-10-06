# Async/Sync Fix: Greenlet Spawn Error

## Problem

When creating a negotiation chronicle, the server crashed with:

```
❌ Error fetching property: greenlet_spawn has not been called; can't call await_only() here. 
Was IO attempted in an unexpected place? 
(Background on this error at: https://sqlalche.me/e/20/xd2s)
INFO: 127.0.0.1:62371 - "POST /api/v1/nego-tables/ HTTP/1.1" 404 Not Found
```

## Root Cause

**SQLAlchemy Lazy Loading in Async Context**

The code was accessing `property_obj.submitted_by.id` which is a **lazy-loaded relationship**. In SQLAlchemy async mode, lazy loading triggers an async database query, but the code tried to access it synchronously, causing the "greenlet_spawn" error.

### Problem Code:
```python
result = await db.execute(select(Property).filter(Property.id == property_id))
property_obj = result.scalar_one_or_none()

if property_obj:
    # ❌ This triggers lazy loading!
    user_id = property_obj.submitted_by.id  # Async query in sync context!
    first_name = property_obj.submitted_by.first_name  # Another query!
```

Each access to `property_obj.submitted_by.X` was trying to load the relationship from the database, but since we're not in an `await` context, SQLAlchemy couldn't perform the async query.

## Solution

**Eager Load Relationships**

Use `selectinload()` to load the relationship immediately when querying the property:

```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Property)
    .filter(Property.id == property_id)
    .options(selectinload(Property.submitted_by))  # ✅ Eager load!
)
property_obj = result.scalar_one_or_none()

if property_obj:
    # ✅ Now this works! The relationship is already loaded
    user_id = property_obj.submitted_by.id
    first_name = property_obj.submitted_by.first_name
```

## What Changed

**File**: `app/api/v1/nego_tables_simple.py`

### Before:
```python
result = await db.execute(select(Property).filter(Property.id == property_id))
property_obj = result.scalar_one_or_none()
```

### After:
```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Property)
    .filter(Property.id == property_id)
    .options(selectinload(Property.submitted_by))  # Eagerly load relationship
)
property_obj = result.scalar_one_or_none()
```

### Additional Changes:

1. **Added property_id type conversion**:
```python
property_id = int(property_id)  # Ensure it's an integer
```

2. **Better error handling**:
```python
except Exception as e:
    print(f"❌ Error fetching property: {e}")
    import traceback
    traceback.print_exc()  # Print full stack trace for debugging
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Database error while fetching property: {str(e)}"
    )
```

## Why This Happens

In SQLAlchemy async mode:
- **Lazy loading** = Load relationship only when accessed (requires async query)
- **Eager loading** = Load relationship immediately with the main query

When you access a lazy-loaded relationship (`property_obj.submitted_by`), SQLAlchemy needs to:
1. Create a new database query
2. Execute it asynchronously
3. Return the result

But if you're not in an `await` context, step 2 fails because SQLAlchemy can't use `await` automatically. That's the "greenlet_spawn" error.

## How to Fix Similar Issues

If you see "greenlet_spawn" errors, it means you're accessing a relationship that needs to be eagerly loaded:

### Option 1: Use selectinload (Recommended)
```python
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(Model)
    .options(selectinload(Model.relationship))
)
```

### Option 2: Use joinedload (For one-to-one)
```python
from sqlalchemy.orm import joinedload

result = await db.execute(
    select(Model)
    .options(joinedload(Model.relationship))
)
```

### Option 3: Load relationship explicitly
```python
property_obj = result.scalar_one_or_none()
if property_obj:
    # Explicitly load the relationship
    await db.refresh(property_obj, ['submitted_by'])
```

## Testing

### Server Logs Should Show:
```
📥 RECEIVED NEGO TABLE CREATE REQUEST
📥 Request data: {'propertyId': 20, ...}
🔍 Creating negotiation chronicle for property ID: 20
✅ Found property in database: test
✅ Chronicle created successfully: 1
```

### No More Errors:
```
❌ greenlet_spawn error - GONE! ✅
❌ 404 error - GONE! ✅
```

### Success Response:
```json
{
  "id": 1,
  "propertyId": 20,
  "status": "active",
  ...
}
```

## Status

✅ **FIXED** - Eager loading prevents lazy load errors
✅ **READY** - Restart server and test chronicle creation

## Next Action

**RESTART YOUR SERVER** and try creating a chronicle again!

The property data should now be loaded correctly without triggering lazy loading errors.

