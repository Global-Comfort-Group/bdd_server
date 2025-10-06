# Negotiation Chronicle Attachment Fix

## Issue Summary

When creating a Negotiation Chronicle and uploading an attachment (CSV/Excel), then clicking "Complete & View", the application threw a validation error:

```
ResponseValidationError: 1 validation errors:
  {'type': 'int_type', 'loc': ('response', 0, 'uploaded_by'), 'msg': 'Input should be a valid integer', 'input': None}
```

This occurred when fetching attachments at: `GET /api/v1/negotiation-chronicles/{nego_table_id}/attachments`

## Root Causes

1. **Strict Pydantic Validation**: The `uploaded_by` field was marked as `Optional[int]` but Pydantic v2 with `from_attributes=True` was rejecting `None` values
2. **Date Type Mismatch**: In-memory attachments stored dates as ISO strings, but the schema expected `datetime` objects

## Changes Made

### File: `/app/schemas/negotiation_chronicle.py`

#### Change 1: Fixed `uploaded_by` field validation
```python
# Before:
uploaded_by: Optional[int] = None

# After:
uploaded_by: Union[int, None] = Field(default=None)
```

#### Change 2: Fixed date field validation
```python
# Before:
upload_date: datetime
created_at: datetime
updated_at: Optional[datetime]

# After:
upload_date: Union[datetime, str]  # Accept both datetime objects and ISO strings
created_at: Union[datetime, str]   # Accept both datetime objects and ISO strings
updated_at: Union[datetime, str, None] = None
```

#### Change 3: Added proper JSON encoding
```python
class Config:
    from_attributes = True
    json_encoders = {
        datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
    }
```

## How the Flow Works

### 1. Create Negotiation Chronicle
- User navigates to `/nego-table/create?propertyId={id}`
- Clicks "Auto-Create Chronicle"
- System calls `POST /api/v1/nego-tables` with property data
- Nego table is created and stored in `CREATED_NEGO_TABLES` (in-memory)

### 2. Upload Attachment
- User uploads CSV/Excel file or provides Google Sheets link
- System calls `POST /api/v1/negotiation-chronicles/upload/{nego_table_id}`
- File is parsed and uploaded to Cloudinary
- Attachment data is stored in `NEGO_TABLE_ATTACHMENTS[nego_table_id]` (in-memory)

### 3. View Property with Chronicle
- User clicks "Complete & View Chronicle"
- Redirects to `/property/{propertyId}`
- System fetches nego tables: `GET /api/v1/nego-tables?propertyId={id}`
- System fetches attachments: `GET /api/v1/negotiation-chronicles/{nego_table_id}/attachments`
- Attachments are displayed in the Negotiation Chronicle Table

## Testing the Fix

### Prerequisites
1. Server restarted with updated schema
2. Client running on port 3000

### Test Steps

1. **Navigate to a Property**
   ```
   http://localhost:3000/property/{property_id}
   ```

2. **Create New Chronicle**
   - Click "Create Negotiation Chronicle"
   - Review property data preview
   - Click "Auto-Create Chronicle"

3. **Upload Negotiation Data**
   - Upload a CSV or Excel file with columns:
     - Header (field names)
     - Value (current values)
     - Agreed Amount (numbers)
     - For Negotiation (numbers)
   - OR provide a Google Sheets link
   - Verify file is parsed successfully

4. **Complete and View**
   - Click "Complete & View Chronicle"
   - Should redirect to property page
   - Negotiation Chronicle section should display
   - Uploaded attachment data should be visible in the table
   - NO validation errors should appear

### Expected Results

✅ Chronicle created successfully
✅ File uploaded and parsed
✅ Property page loads without errors
✅ Negotiation data displays in the table
✅ Can upload additional files
✅ Can download original files
✅ Can delete attachments

### Sample CSV Format

```csv
Header,Value,Agreed Amount,For Negotiation
Property Name,Sample Property,,
Location,123 Main St,,
Lot Area,1000,500000,450000
Sale Price,1000000,950000,900000
Monthly Lease,,50000,45000
```

## Files Modified

1. `/app/schemas/negotiation_chronicle.py` - Fixed schema validation
2. Server restarted to apply changes

## API Endpoints Used

- `POST /api/v1/nego-tables` - Create chronicle
- `POST /api/v1/negotiation-chronicles/upload/{nego_table_id}` - Upload attachment
- `GET /api/v1/nego-tables?propertyId={id}` - Get chronicles by property
- `GET /api/v1/negotiation-chronicles/{nego_table_id}/attachments` - Get attachments

## Notes

- In-memory storage is used for development (`CREATED_NEGO_TABLES` and `NEGO_TABLE_ATTACHMENTS`)
- In production, these would be stored in the database
- The fix ensures compatibility with both in-memory dicts and database ORM objects
- Dates can be returned as either `datetime` objects or ISO strings


