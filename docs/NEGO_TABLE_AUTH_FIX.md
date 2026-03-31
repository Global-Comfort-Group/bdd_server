# Negotiation Table Authentication Fix

## Issue
Negotiation table creation was failing in staging because the endpoint had no authentication or permission checks.

## Date
October 7, 2025

## Problem Description
The `POST /api/v1/nego-tables/` endpoint in `nego_tables_simple.py` was missing:
1. User authentication requirement (`current_user` dependency)
2. Permission checks to verify user can create nego tables
3. Proper assignment validation for BDD_USER role

x`
This caused:
- Anyone to potentially create nego tables without authentication
- No validation of reviewer assignment for BDD_USER
- Security vulnerability in production

## Solution Implemented

### Server-Side Changes

#### File: `/app/api/v1/nego_tables_simple.py`

**Before:**
```python
@router.post("/")
async def create_nego_table(
    nego_table_data: dict,
    db: AsyncSession = Depends(get_async_session)
):
```

**After:**
```python
@router.post("/")
async def create_nego_table(
    nego_table_data: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new negotiation table for a property with auto-populated data.
    
    Only ADMIN or BDD_USER assigned as reviewer can create nego tables.
    """
```

**Permission Check Added:**
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

### Client-Side Changs

#### File: `/src/lib/permissions.ts`

**Before:**
```typescript
export function canManageNegotiationChronicles(userRole: UserRole | undefined): boolean {
  if (!userRole) return false
  return userRole === UserRole.BDD_USER || userRole === UserRole.ADMIN
}
```

**After:**
```typescript
export function canManageNegotiationChronicles(
  userRole: UserRole | undefined,
  userId: string | undefined,
  property: Property | undefined
): boolean {
  if (!userRole || !userId || !property) return false
  
  // Admin can manage any negotiation chronicles
  if (userRole === UserRole.ADMIN) {
    return true
  }
  
  // BDD_USER can only manage chronicles for properties they are assigned to as reviewer
  if (userRole === UserRole.BDD_USER && property.reviewerId) {
    return property.reviewerId.toString() === userId
  }
  
  return false
}
```

#### File: `/src/components/property/property-nego-section.tsx`

**Updated Usage:**
```typescript
// Before
const canManage = canManageNegotiationChronicles(userRole)

// After
const canManage = canManageNegotiationChronicles(userRole, session?.user?.id, property)
```

## Permission Matrix

| User Role | Can Create Nego Table |
|-----------|----------------------|
| AGENT | ❌ No | 
| BROKER | ❌ No |
| BDD_USER (Not assigned) | ❌ No |
| BDD_USER (Assigned as reviewer) | ✅ Yes |
| ADMIN | ✅ Yes (any property) |

## Testing

### Test Case 1: ADMIN User
```bash
# ADMIN should be able to create nego table for any property
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"propertyId": 1, "sourceOrigin": "Direct Inquiry"}'
# Expected: 200 OK
```

### Test Case 2: BDD_USER (Assigned Reviewer)
```bash
# BDD_USER assigned to property should succeed
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <bdd_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"propertyId": 1, "sourceOrigin": "Direct Inquiry"}'
# Expected: 200 OK (if user is assigned as reviewer to property 1)
```

### Test Case 3: BDD_USER (Not Assigned)
```bash
# BDD_USER not assigned to property should fail
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <bdd_user_token>" \
  -H "Content-Type: application/json" \
  -d '{"propertyId": 2, "sourceOrigin": "Direct Inquiry"}'
# Expected: 403 Forbidden
# Message: "You can only create negotiation chronicles for properties you are assigned to as a reviewer. Please contact an admin to assign you to this property."
```

### Test Case 4: AGENT/BROKER User
```bash
# AGENT/BROKER should not be able to create nego tables
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Authorization: Bearer <agent_token>" \
  -H "Content-Type: application/json" \
  -d '{"propertyId": 1, "sourceOrigin": "Direct Inquiry"}'
# Expected: 403 Forbidden
# Message: "Only BDD employees assigned as reviewers or admins can create negotiation chronicles"
```

### Test Case 5: Unauthenticated User
```bash
# No auth token should fail
curl -X POST http://localhost:8000/api/v1/nego-tables/ \
  -H "Content-Type: application/json" \
  -d '{"propertyId": 1, "sourceOrigin": "Direct Inquiry"}'
# Expected: 401 Unauthorized
```

## Deployment Steps

1. **Deploy Server Changes:**
   ```bash
   cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
   git add app/api/v1/nego_tables_simple.py
   git add docs/PERMISSION_STRUCTURE.md
   git commit -m "feat: add authentication and permission checks to nego table creation"
   git push origin staging
   ```

2. **Deploy Client Changes:**
   ```bash
   cd /Users/kyleisaacmendoza/Documents/workspace/bdd_client
   git add src/lib/permissions.ts
   git add src/components/property/property-nego-section.tsx
   git add docs/PERMISSION_STRUCTURE.md
   git commit -m "feat: update nego table permission checks to require reviewer assignment"
   git push origin staging
   ```

3. **Test in Staging:**
   - Login as ADMIN and verify nego table creation works
   - Login as BDD_USER assigned to a property and verify creation works
   - Login as BDD_USER not assigned and verify creation is blocked
   - Login as AGENT and verify creation is blocked

4. **Monitor Production:**
   - Check server logs for any 403 errors
   - Verify users can assign reviewers to properties
   - Verify assigned reviewers can create nego tables

## Rollback Plan

If issues occur:

1. **Revert Server Changes:**
   ```bash
   cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
   git revert HEAD
   git push origin staging
   ```

2. **Revert Client Changes:**
   ```bash
   cd /Users/kyleisaacmendoza/Documents/workspace/bdd_client
   git revert HEAD
   git push origin staging
   ```

## Impact

### Security
✅ **Improved**: Authentication now required for nego table creation
✅ **Improved**: Permission checks prevent unauthorized access
✅ **Improved**: Reviewer assignment validation

### User Experience
- ✅ ADMIN: No change, still has full access
- ⚠️ BDD_USER: Now requires reviewer assignment (more restrictive)
- ℹ️ AGENT/BROKER: No change, still cannot create nego tables

### Breaking Changes
⚠️ **BDD_USERs must now be assigned as reviewers** to create nego tables for a property. Admins can assign reviewers via:
- Admin Portal
- Property detail page
- API endpoint: `PATCH /api/v1/properties/{id}/assign-reviewer`

## Related Files

### Server
- `/app/api/v1/nego_tables_simple.py` - Main endpoint with auth fix
- `/app/api/v1/auth.py` - Authentication dependency
- `/app/models/user.py` - User model
- `/app/models/property.py` - Property model with reviewer_id
- `/docs/PERMISSION_STRUCTURE.md` - Updated documentation

### Client
- `/src/lib/permissions.ts` - Permission utility functions
- `/src/components/property/property-nego-section.tsx` - UI component
- `/docs/PERMISSION_STRUCTURE.md` - Updated documentation

## Future Improvements

1. **Bulk Reviewer Assignment**: Allow assigning reviewers to multiple properties at once
2. **Temporary Access**: Time-limited reviewer assignments
3. **Co-Reviewers**: Allow multiple reviewers per property
4. **Permission Delegation**: Allow reviewers to delegate access
5. **Audit Trail**: Log all permission checks and denials

## Support

For issues:
1. Check server logs: `tail -f logs/app.log`
2. Verify user role: Query database `SELECT id, email, role FROM user WHERE email = 'user@example.com'`
3. Check reviewer assignment: Query database `SELECT id, name, reviewer_id FROM properties WHERE id = {property_id}`
4. Contact backend team lead

## References

- Property Status Update Permission (uses same reviewer assignment logic)
- User Roles Documentation
- BDD_USER Permissions Guide

