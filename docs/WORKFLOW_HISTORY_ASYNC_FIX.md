# Workflow History Async Fix

## Issue
When fetching property details via `GET /api/v1/properties/{id}`, the server threw a 500 Internal Server Error:

```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for PropertyRead
workflow_history.0.changed_by
  Error extracting attribute: MissingGreenlet: greenlet_spawn has not been called; 
  can't call await_only() here. Was IO attempted in an unexpected place?
```

## Root Cause
SQLAlchemy's async ORM requires all relationships to be **eagerly loaded** before the async session closes. The `workflow_history` relationship was being loaded, but its nested `changed_by` (User) relationship was not, causing a lazy-load attempt outside of an async context.

## Solution
Updated `/Users/kyleisaacmendoza/Documents/workspace/bdd_server/app/services/property.py`:

### Changes Made

1. **Import WorkflowHistory model** (Line 8):
   ```python
   from app.models.workflow import PropertyStatus, WorkflowHistory
   ```

2. **Add nested selectinload for changed_by** (Line 24):
   ```python
   selectinload(Property.workflow_history).selectinload(WorkflowHistory.changed_by)
   ```

### Before
```python
stmt = (
    select(Property)
    .options(
        selectinload(Property.submitted_by),
        selectinload(Property.reviewer),
        selectinload(Property.attachments),
        selectinload(Property.workflow_history)  # ❌ Missing nested relationship
    )
    .where(Property.id == property_id)
)
```

### After
```python
stmt = (
    select(Property)
    .options(
        selectinload(Property.submitted_by),
        selectinload(Property.reviewer),
        selectinload(Property.attachments),
        selectinload(Property.workflow_history).selectinload(WorkflowHistory.changed_by)  # ✅ Nested load
    )
    .where(Property.id == property_id)
)
```

## Client-Side Fix
Also fixed the client-side fetch request in `bdd_client/src/app/(dashboard)/property/[id]/page.tsx`:

1. **Added authentication headers** (Lines 131-136):
   ```typescript
   const response = await fetch(PROPERTY_ENDPOINTS.GET(params.id as string), {
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${session?.accessToken || ''}`
     }
   })
   ```

2. **Added session dependency** (Line 269):
   ```typescript
   }, [params.id, refreshKey, session?.accessToken, fetchNegoTables])
   ```

## Testing
After the fix:
- ✅ Property details page loads successfully
- ✅ Workflow history is properly serialized with user information
- ✅ No more SQLAlchemy MissingGreenlet errors
- ✅ All relationships are eagerly loaded in async context

## Key Takeaways

### For Async SQLAlchemy
- **Always eagerly load relationships** that will be accessed after the session closes
- Use **nested `selectinload()`** for relationships of relationships
- The pattern: `.selectinload(Parent.child).selectinload(Child.grandchild)`

### For FastAPI + SQLAlchemy Async
- Load all relationships in the service layer query
- Don't rely on lazy loading in async endpoints
- Pydantic serialization happens outside the DB session context

## Related Files
- `app/services/property.py` - Service layer with eager loading
- `app/api/v1/properties.py` - API endpoint
- `app/models/workflow.py` - WorkflowHistory model
- `src/app/(dashboard)/property/[id]/page.tsx` - Client-side property detail page

## Date
October 7, 2025

