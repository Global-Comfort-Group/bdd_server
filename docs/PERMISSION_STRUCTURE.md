# Permission Structure Implementation (Server-Side)

## Overview

This document describes the server-side permission implementation for the BDD Property Tracker API. All permission checks are enforced at the API level to ensure security.

## Implementation Date

**Date**: October 6, 2025  
**Version**: v2.0 - Refined permission structure

## Changes Made

### 1. Property Edit Permissions

**Endpoint**: `PATCH /api/v1/properties/{property_id}`

**Before**:
```python
# Check permissions - only owner, reviewer, BDD user, or admin can update
if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
    property_obj.submitted_by_id != current_user.id and
    property_obj.reviewer_id != current_user.id):
    raise HTTPException(status_code=403, detail="Not authorized to update this property")
```

**After**:
```python
# Check permissions - only the property submitter can edit property details
# For status updates, use the dedicated /status endpoint instead
if property_obj.submitted_by_id != current_user.id:
    raise HTTPException(
        status_code=403, 
        detail="Only the property submitter can edit property details. Use /status endpoint to update property status."
    )
```

**Impact**: Now only the property submitter can edit property details. BDD_USER and ADMIN must use the dedicated status endpoint.

### 2. Property Status Update Permissions

**Endpoint**: `PATCH /api/v1/properties/{property_id}/status`

**Before**:
```python
# Status updates can be done by BDD users, admins, brokers, or property owner
if (current_user.role.value not in ["BDD_USER", "ADMIN", "BROKER"] and
    property_obj.submitted_by_id != current_user.id):
    raise HTTPException(status_code=403, detail="Not authorized to update property status")
```

**After**:
```python
# Status updates can only be done by BDD users and admins
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=403, 
        detail="Only BDD employees and admins can update property status"
    )
```

**Impact**: Removed BROKER and property owner from status update permissions. Only BDD staff can manage workflow.

### 3. Negotiation Chronicle Permissions

**Endpoints**: All negotiation chronicle endpoints now have permission checks

#### Create Chronicle
**Endpoint**: `POST /api/v1/nego-tables/`

```python
# Check permissions - only ADMIN or assigned reviewer (BDD_USER) can create nego tables
is_admin = current_user.role.value == "ADMIN"
is_assigned_reviewer = (
    current_user.role.value == "BDD_USER" and 
    property_obj.reviewer_id == current_user.id
)

if not (is_admin or is_assigned_reviewer):
    if current_user.role.value == "BDD_USER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create negotiation chronicles for properties you are assigned to as a reviewer. Please contact an admin to assign you to this property."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees assigned as reviewers or admins can create negotiation chronicles"
        )
```

#### Update Chronicle
**Endpoint**: `PUT /api/v1/nego-tables/{nego_table_id}`

```python
# Check permissions - only BDD users and admins can update negotiation chronicles
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only BDD employees and admins can update negotiation chronicles"
    )
```

#### Delete Chronicle
**Endpoint**: `DELETE /api/v1/nego-tables/{nego_table_id}`

```python
# Check permissions - only BDD users and admins can delete negotiation chronicles
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only BDD employees and admins can delete negotiation chronicles"
    )
```

#### Add Negotiation Entry
**Endpoint**: `POST /api/v1/nego-tables/{nego_table_id}/negotiations`

```python
# Check permissions - only BDD users and admins can add negotiation entries
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only BDD employees and admins can add negotiation entries"
    )
```

#### Update Negotiation Entry
**Endpoint**: `PUT /api/v1/nego-tables/{nego_table_id}/negotiations/{negotiation_id}`

```python
# Check permissions - only BDD users and admins can update negotiation entries
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only BDD employees and admins can update negotiation entries"
    )
```

#### Delete Negotiation Entry
**Endpoint**: `DELETE /api/v1/nego-tables/{nego_table_id}/negotiations/{negotiation_id}`

```python
# Check permissions - only BDD users and admins can delete negotiation entries
if current_user.role.value not in ["BDD_USER", "ADMIN"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only BDD employees and admins can delete negotiation entries"
    )
```

**Impact**: All negotiation chronicle operations now require BDD staff role.

## Permission Matrix

| Action | AGENT | BROKER | BDD_USER | BDD_USER (Assigned) | ADMIN |
|--------|-------|--------|----------|---------------------|-------|
| View Properties | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create Property | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit Own Property | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit Other's Property | ❌ | ❌ | ❌ | ❌ | ❌ |
| Update Property Status | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Own Property | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Nego Chronicles | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create Nego Chronicle | ❌ | ❌ | ❌ | ✅ | ✅ |
| Edit Nego Chronicle | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Nego Chronicle | ❌ | ❌ | ❌ | ✅ | ✅ |
| Add Nego Entry | ❌ | ❌ | ❌ | ✅ | ✅ |
| Edit Nego Entry | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Nego Entry | ❌ | ❌ | ❌ | ✅ | ✅ |

**Note**: "BDD_USER (Assigned)" means a BDD_USER who is assigned as the reviewer for that specific property.

## Files Modified

### 1. `/app/api/v1/properties.py`
- Updated property edit permission check (line 338-344)
- Updated status update permission check (line 400-405)

### 2. `/app/api/v1/nego_tables_simple.py`
- Added authentication requirement with `current_user` dependency
- Added permission check to create endpoint (line 80-99)
  - Only ADMIN can create nego tables for any property
  - Only BDD_USER assigned as reviewer can create nego tables for their assigned properties
- Updated created_by to use current_user information (line 175-179)

## Error Responses

All permission checks return HTTP 403 Forbidden with descriptive error messages:

### Property Edit
```json
{
  "detail": "Only the property submitter can edit property details. Use /status endpoint to update property status."
}
```

### Status Update
```json
{
  "detail": "Only BDD employees and admins can update property status"
}
```

### Negotiation Chronicles
```json
{
  "detail": "Only BDD employees and admins can [create/update/delete] negotiation chronicles"
}
```

```json
{
  "detail": "Only BDD employees and admins can [add/update/delete] negotiation entries"
}
```

## Testing

### Test Property Edit Permission
```bash
# As submitter - should succeed
curl -X PATCH http://localhost:8000/api/v1/properties/1 \
  -H "Authorization: Bearer <submitter_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Property Name"}'

# As BDD user (non-submitter) - should fail
curl -X PATCH http://localhost:8000/api/v1/properties/1 \
  -H "Authorization: Bearer <bdd_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Property Name"}'
# Expected: 403 Forbidden
```

### Test Status Update Permission
```bash
# As BDD user - should succeed
curl -X PATCH http://localhost:8000/api/v1/properties/1/status \
  -H "Authorization: Bearer <bdd_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"new_status": "PROPERTY_STUDY", "notes": "Moving to study phase"}'

# As agent - should fail
curl -X PATCH http://localhost:8000/api/v1/properties/1/status \
  -H "Authorization: Bearer <agent_token>" \
  -H "Content-Type: application/json" \
  -d '{"new_status": "PROPERTY_STUDY", "notes": "Moving to study phase"}'
# Expected: 403 Forbidden
```

### Test Nego Chronicle Permission
```bash
# As BDD user - should succeed
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <bdd_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"property_id": 1, "referred_date": "2025-10-06", ...}'

# As agent - should fail
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <agent_token>" \
  -H "Content-Type: application/json" \
  -d '{"property_id": 1, "referred_date": "2025-10-06", ...}'
# Expected: 403 Forbidden
```

## Migration Notes

### Breaking Changes
1. **Brokers can no longer update property status** - They must request status updates from BDD staff
2. **Property owners cannot update their own property status** - Only BDD staff can manage workflow
3. **Negotiation chronicles are now BDD-staff only** - Agents and brokers can only view

### Migration Steps
1. No database migrations required
2. Update client applications to reflect new permission structure
3. Notify users of permission changes
4. Update API documentation

### Backward Compatibility
⚠️ **Not backward compatible** - Existing workflows that relied on broker or owner status updates will break

## Security Considerations

1. **Strict Permission Checks**: All checks are done before any database operations
2. **Clear Separation**: Property editing and status updates use different endpoints
3. **Role Verification**: User role is extracted from authenticated session
4. **Consistent Error Messages**: All permission errors return 403 with clear messages
5. **Audit Trail**: All operations log user information for audit purposes

## Future Enhancements

1. **Role-Based Endpoint Access**: Implement FastAPI dependencies for role checking
2. **Permission Service**: Create centralized permission service
3. **Dynamic Permissions**: Allow admins to configure permissions
4. **Temporary Access**: Time-limited permission grants
5. **Activity Logging**: Enhanced audit trail for all permission checks

## Deployment Checklist

- [x] Update server-side permission checks
- [x] Update client-side permission utilities
- [x] Create documentation
- [ ] Update API documentation (Swagger/OpenAPI)
- [ ] Notify users of changes
- [ ] Deploy to staging
- [ ] Test all permission scenarios
- [ ] Deploy to production
- [ ] Monitor for permission-related errors

## Rollback Plan

If permission changes cause issues:

1. Revert changes in `app/api/v1/properties.py`:
   - Restore original property edit check
   - Restore original status update check

2. Revert changes in `app/api/v1/nego_tables.py`:
   - Remove all new permission checks

3. Redeploy previous version

4. Notify users of rollback

## Support

For issues or questions:
- Check server logs: `tail -f logs/app.log`
- Review permission documentation
- Contact backend team lead


