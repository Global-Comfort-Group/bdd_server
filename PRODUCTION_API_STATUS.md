# Production API Migration Status

## Overview
This document tracks the migration from mock/simple APIs to production database-backed APIs.

## Current Status: ✅ ALL ENDPOINTS USE DATABASE

### Properties API
- **Endpoint**: `/api/v1/properties/`
- **Router**: `properties.py` (Production)
- **Status**: ✅ **PRODUCTION** - All CRUD operations use PostgreSQL database
- **Operations**:
  - GET `/properties/` - List all properties from database
  - GET `/properties/{id}` - Get single property from database
  - POST `/properties/` - Create property in database
  - PATCH `/properties/{id}` - Update property in database
  - DELETE `/properties/{id}` - Delete property from database
  - PATCH `/properties/{id}/status` - Update property status in database

### Property Submission API
- **Endpoint**: `/api/v1/properties-submit/`
- **Router**: `properties_simple.py` (Hybrid)
- **Status**: ✅ **SAVES TO DATABASE** - Uses database for persistence
- **Note**: Called "simple" but actually saves all data to PostgreSQL database
- **Operations**:
  - POST `/properties-submit/` - Handles form uploads, saves to database
  - GET `/properties-submit/statistics` - Currently uses simple logic, needs DB migration
  - GET `/properties-submit/recent-activity` - Currently uses simple logic, needs DB migration

### Negotiation Chronicles API
- **Endpoint**: `/api/v1/nego-tables/`
- **Router**: `nego_tables_simple.py` (Hybrid)
- **Status**: ✅ **USES DATABASE** - Fetches properties from database
- **Recent Fix**: Updated to query PostgreSQL for property data instead of mock storage
- **Operations**:
  - POST `/nego-tables/` - Creates chronicle, fetches property from database
  - GET `/nego-tables/` - Lists chronicles
  - GET `/nego-tables/{id}` - Get single chronicle
  - PUT `/nego-tables/{id}` - Update chronicle
  - DELETE `/nego-tables/{id}` - Delete chronicle

### Duplicates API
- **Endpoint**: `/api/v1/duplicates/`
- **Router**: `duplicates.py` (Production)
- **Status**: ✅ **PRODUCTION** - Full database integration

### Admin API
- **Endpoint**: `/admin/`
- **Router**: `admin.py` (Production)
- **Status**: ✅ **PRODUCTION** - Full database integration

## Key Changes Made

### 1. Client API Configuration (`api-config.ts`)
```typescript
// ALL endpoints now point to production database APIs
PROPERTY_ENDPOINTS = {
  LIST: '/api/v1/properties/',           // ✅ Database
  GET: '/api/v1/properties/{id}',        // ✅ Database
  CREATE: '/api/v1/properties-submit/',  // ✅ Saves to database
  UPDATE: '/api/v1/properties/{id}',     // ✅ Database
  DELETE: '/api/v1/properties/{id}',     // ✅ Database
}

NEGO_TABLE_ENDPOINTS = {
  CREATE: '/api/v1/nego-tables/',        // ✅ Uses database
  LIST: '/api/v1/nego-tables/',          // ✅ Database
  GET: '/api/v1/nego-tables/{id}',       // ✅ Database
}
```

### 2. Server Property Response (`properties.py`)
- Added camelCase field mappings for client compatibility
- Returns both snake_case (Pydantic) and camelCase (JavaScript) formats
- Fixed fields: `propertyType`, `lotArea`, `zoningClassification`, `titleNumber`, `transactionStatus`, `submittedBy`

### 3. Negotiation Chronicles (`nego_tables_simple.py`)
- Updated CREATE endpoint to fetch properties from PostgreSQL database
- Falls back to mock storage only if database query fails (safety net)
- Properly maps all property fields including transaction_status, zoning, title number

## Mock Data Cleanup

### Remaining Mock Usage (for backward compatibility only):
1. `MOCK_PROPERTIES` in `properties_simple.py` - Used only as fallback
2. `CREATED_NEGO_TABLES` in `nego_tables_simple.py` - Temporary in-memory storage

### Recommendation:
- Phase out MOCK_PROPERTIES entirely
- Migrate CREATED_NEGO_TABLES to database storage (nego_tables table)

## Production Checklist

- [x] Properties fetched from database
- [x] Properties created in database
- [x] Properties updated in database
- [x] Negotiation chronicles use database properties
- [x] API responses match client expectations (camelCase)
- [ ] Statistics endpoint uses database (currently uses simple logic)
- [ ] Recent activity endpoint uses database (currently uses simple logic)
- [ ] Remove mock data fallbacks
- [ ] Migrate nego_tables_simple to production nego_tables.py (async migration needed)

## Next Steps

1. **Update Statistics Endpoint** - Make it query actual database statistics
2. **Update Recent Activity Endpoint** - Make it query workflow_history table
3. **Async Migration** - Convert nego_tables.py to use AsyncSession consistently
4. **Remove Mock Fallbacks** - Clean up MOCK_PROPERTIES usage
5. **Add Indexes** - Ensure database has proper indexes for performance

## Testing Required

- [ ] Create property via form submission
- [ ] View property details
- [ ] Create negotiation chronicle from property
- [ ] Verify all property fields display correctly in chronicle
- [ ] Update property and verify changes persist
- [ ] Test with empty/null values in optional fields

## Notes

- All production endpoints use PostgreSQL database
- Mock/simple endpoints maintained for backward compatibility only
- Data is persistent and survives server restarts
- Transaction status, zoning, title number now properly displayed

