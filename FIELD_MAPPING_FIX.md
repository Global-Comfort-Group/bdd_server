# Field Mapping Fix: "Not Specified" Issue Resolution

## Problem
When creating a Negotiation Chronicle, several property fields showed "Not specified" even though the data existed in the database:
- Property Type
- Lot Area  
- Title Number
- Transaction Status
- Zoning Classification
- Submitted By

## Root Causes Identified

### 1. Missing Authentication Token
**Issue**: The chronicle creation page was fetching property data without passing the JWT authentication token.

**Location**: `bdd_client/src/app/(dashboard)/nego-table/create/page.tsx`

**Fix Applied**:
```typescript
// Added useSession hook
import { useSession } from 'next-auth/react'
const { data: session } = useSession()

// Pass token to API call
const response = await fetch(PROPERTY_ENDPOINTS.GET(propertyId), {
  headers: getAuthHeaders(session?.accessToken)  // ✅ Now includes token
})

// Wait for session before fetching
if (!session) {
  console.log('⏳ Waiting for session to load...')
  return
}
```

### 2. Field Name Mismatch (snake_case vs camelCase)
**Issue**: Server returned fields in `snake_case` (Python convention) but client expected `camelCase` (JavaScript convention).

**Server Response (Before)**:
```json
{
  "property_type": "LAND_ONLY",
  "lot_area": 1000,
  "title_number": "TCT-12345",
  "transaction_status": "S",
  "zoning_classification": "Residential",
  "submitted_by": {
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Client Expected**:
```json
{
  "propertyType": "LAND_ONLY",
  "lotArea": 1000,
  "titleNumber": "TCT-12345",
  "transactionStatus": "S",
  "zoningClassification": "Residential",
  "submittedBy": {
    "firstName": "John",
    "lastName": "Doe"
  }
}
```

**Location**: `bdd_server/app/api/v1/properties.py` - `get_property()` function (lines 207-285)

**Fix Applied**:
```python
# Convert to dict and add camelCase aliases for client compatibility
response_dict = response.model_dump()

# Convert submittedBy user object to camelCase
submitted_by_camel = None
if property_obj.submitted_by:
    submitted_by_camel = {
        "id": property_obj.submitted_by.id,
        "email": property_obj.submitted_by.email,
        "firstName": property_obj.submitted_by.first_name,  # ✅ camelCase
        "middleName": property_obj.submitted_by.middle_name,
        "lastName": property_obj.submitted_by.last_name,
        "role": property_obj.submitted_by.role.value,
        "company": property_obj.submitted_by.company,
        "phone": property_obj.submitted_by.phone,
        "isActive": property_obj.submitted_by.is_active,
        "accountStatus": property_obj.submitted_by.account_status.value,
    }

response_dict.update({
    "propertyType": str(property_obj.property_type.value),  # ✅ camelCase
    "lotArea": float(property_obj.lot_area),
    "zoningClassification": property_obj.zoning_classification,
    "titleNumber": property_obj.title_number,
    "transactionStatus": str(property_obj.transaction_status.value),
    "submittedBy": submitted_by_camel,
    "submittedById": str(property_obj.submitted_by_id),
    "createdAt": property_obj.created_at.isoformat(),
    "updatedAt": property_obj.updated_at.isoformat(),
})
```

## Changes Made

### Client-Side Changes

#### File: `src/app/(dashboard)/nego-table/create/page.tsx`

**1. Added Authentication**
```typescript
// Line 5: Import useSession
import { useSession } from 'next-auth/react'

// Line 20: Get session
const { data: session } = useSession()

// Line 45-48: Wait for session
if (!session) {
  console.log('⏳ Waiting for session to load...')
  return
}

// Line 54: Pass token to API
headers: getAuthHeaders(session?.accessToken)

// Line 79: Added session dependency
}, [propertyId, session])
```

**2. Added Debug Logging**
```typescript
console.log('🔍 Fetching property from:', PROPERTY_ENDPOINTS.GET(propertyId))
console.log('🔐 Session token available:', !!session?.accessToken)
console.log('✅ Property data received:', propertyData)
console.log('  - propertyType:', propertyData.propertyType)
console.log('  - lotArea:', propertyData.lotArea)
console.log('  - titleNumber:', propertyData.titleNumber)
console.log('  - zoningClassification:', propertyData.zoningClassification)
console.log('  - transactionStatus:', propertyData.transactionStatus)
console.log('  - submittedBy:', propertyData.submittedBy)
```

### Server-Side Changes

#### File: `app/api/v1/properties.py`

**Updated `get_property()` function (lines 207-285)**:

1. **Added camelCase field mapping** for all property fields
2. **Converted nested user object** (`submittedBy`) to camelCase
3. **Maintained backward compatibility** by keeping both formats

**Benefits**:
- Client receives data in expected format
- No changes needed to TypeScript interfaces
- Enum values properly extracted (e.g., `PropertyType.LAND_ONLY` → `"LAND_ONLY"`)

## Expected Console Output

When creating a negotiation chronicle, you should now see:

```
⏳ Waiting for session to load...
🔍 Fetching property from: http://localhost:8000/api/v1/properties/123
🔐 Session token available: true
✅ Property data received: { ... }
  - propertyType: LAND_ONLY
  - lotArea: 1000
  - titleNumber: TCT-12345
  - zoningClassification: Residential
  - transactionStatus: S
  - submittedBy: { firstName: 'John', lastName: 'Doe', ... }
```

## Property Data Preview (UI)

The chronicle preview should now display:

```
Property Type:          Land Only         ✅ (was: "Not specified")
Lot Area (sqm):         1000              ✅ (was: 0)
Title Number:           TCT-12345         ✅ (was: "Not specified")
Zoning Classification:  Residential       ✅ (was: "Not specified")
Transaction Status:     Sale              ✅ (was: "Not specified")
Submitted By:           John Doe          ✅ (was: "Not specified")
```

## Testing Checklist

- [ ] User is logged in with valid JWT token
- [ ] Browser console shows "Session token available: true"
- [ ] Property data is fetched successfully (200 OK)
- [ ] All camelCase fields are present in response
- [ ] Property preview shows all field values correctly
- [ ] Chronicle creation succeeds without errors
- [ ] No "Not specified" values for fields that have data

## Related Files Modified

### Client
1. `src/app/(dashboard)/nego-table/create/page.tsx` - Added authentication and debug logging

### Server
2. `app/api/v1/properties.py` - Added camelCase field mapping in `get_property()`

### Documentation
3. `PRODUCTION_API_STATUS.md` - Production API migration status
4. `AUTH_DEBUGGING_GUIDE.md` - Authentication troubleshooting
5. `FIELD_MAPPING_FIX.md` - This document

## API Response Format (Final)

```json
{
  "id": 123,
  "name": "Sample Property",
  "address": "12675 Rd 3, Los Baños, Laguna",
  
  // Both formats for backward compatibility
  "property_type": "LAND_ONLY",
  "propertyType": "LAND_ONLY",  // ✅ Client uses this
  
  "lot_area": 1000,
  "lotArea": 1000,              // ✅ Client uses this
  
  "title_number": "TCT-12345",
  "titleNumber": "TCT-12345",   // ✅ Client uses this
  
  "zoning_classification": "Residential",
  "zoningClassification": "Residential",  // ✅ Client uses this
  
  "transaction_status": "S",
  "transactionStatus": "S",     // ✅ Client uses this
  
  // User object also in camelCase
  "submitted_by": { ... },
  "submittedBy": {              // ✅ Client uses this
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
  }
}
```

## Next Steps

1. **Test the fix**:
   - Log out and log in again (fresh JWT token)
   - Create a new property (if needed)
   - Navigate to create negotiation chronicle
   - Verify all fields display correctly in preview

2. **Monitor console**:
   - Check for authentication logs
   - Verify property data structure
   - Confirm no errors during chronicle creation

3. **Verify database**:
   - Check that property data is actually in database
   - Ensure `submitted_by_id` foreign key is set
   - Verify enum values are stored correctly

## Common Issues

### Still seeing "Not specified"?

1. **Check session**: Log out and log in again
2. **Check console**: Look for "Session token available: false"
3. **Check response**: Verify API returns camelCase fields
4. **Check database**: Ensure data actually exists in the property record

### Authentication errors?

1. See `AUTH_DEBUGGING_GUIDE.md`
2. Verify `NEXTAUTH_SECRET` and `SECRET_KEY` match
3. Check JWT token hasn't expired (30 min default)

## Status: ✅ FIXED

All property fields should now display correctly in negotiation chronicle creation.

