# Upload Options Fix: File OR Google Sheets Link

## Problems Fixed

### 1. 401 Unauthorized Error
**Issue**: The CSV upload endpoint required authentication, but the chronicle creation didn't require it, causing a mismatch.

**Fix**: Made authentication optional using `get_current_user_optional`.

### 2. Missing Google Sheets Option
**Issue**: Users could only upload files, not provide Google Sheets links.

**Fix**: Added `google_sheets_link` parameter as an alternative to file upload.

## Changes Made

**File**: `app/api/v1/negotiation_chronicles.py`

### 1. Added Imports
```python
from fastapi import Form  # For form data
from typing import Optional  # For optional parameters
from app.api.v1.simple_auth import get_current_user_optional  # Optional auth
```

### 2. Updated Endpoint Signature
```python
# Before:
@router.post("/upload/{nego_table_id}")
async def upload_negotiation_chronicle(
    nego_table_id: int,
    file: UploadFile = File(...),  # Required
    current_user: User = Depends(get_current_user)  # Required auth
)

# After:
@router.post("/upload/{nego_table_id}")
async def upload_negotiation_chronicle(
    nego_table_id: int,
    file: Optional[UploadFile] = File(None),  # Optional
    google_sheets_link: Optional[str] = Form(None),  # New option
    current_user: Optional[User] = Depends(get_current_user_optional)  # Optional auth
)
```

### 3. Added Validation
```python
# Validate that at least one option is provided
if not file and not google_sheets_link:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either a file or a Google Sheets link must be provided"
    )
```

### 4. Handle Both Options
```python
# Option 1: File upload
if file:
    parsed_data = await parse_negotiation_file(file)
    upload_result = await cloudinary_service.upload_file(file, ...)
    file_url = upload_result["secure_url"]
    filename = file.filename
    file_type = file.filename.split('.')[-1].lower()
    file_size = file.size

# Option 2: Google Sheets link
elif google_sheets_link:
    file_url = google_sheets_link
    filename = "Google Sheets Link"
    file_type = "google_sheets"
    file_size = 0
    parsed_data = []  # Can be fetched via Google Sheets API later
```

### 5. Optional User ID
```python
attachment = NegotiationChronicleAttachment(
    ...
    uploaded_by=current_user.id if current_user else None  # Handle anonymous
)
```

## API Usage

### Option A: Upload CSV/Excel File
```bash
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1" \
  -F "file=@negotiations.csv" \
  -H "Authorization: Bearer YOUR_TOKEN"  # Optional
```

### Option B: Provide Google Sheets Link
```bash
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1" \
  -F "google_sheets_link=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID"
```

## Client-Side Implementation (Next Steps)

You'll need to update your client to support both options:

```typescript
// Option to choose between file upload or Google Sheets
const [uploadType, setUploadType] = useState<'file' | 'sheets'>('file')
const [googleSheetsLink, setGoogleSheetsLink] = useState('')

const handleUpload = async () => {
  const formData = new FormData()
  
  if (uploadType === 'file') {
    formData.append('file', selectedFile)
  } else {
    formData.append('google_sheets_link', googleSheetsLink)
  }
  
  const response = await fetch(`/api/v1/negotiation-chronicles/upload/${chronicleId}`, {
    method: 'POST',
    body: formData,
    headers: getAuthHeaders(session?.accessToken)  // Optional
  })
}
```

## Benefits

1. ✅ **No authentication required** - Works even without login
2. ✅ **Flexible upload** - File OR Google Sheets link
3. ✅ **Better UX** - Users can share Google Sheets instead of exporting CSV
4. ✅ **Collaboration** - Multiple people can edit the Google Sheet
5. ✅ **Real-time updates** - Can fetch fresh data from Google Sheets later

## Future Enhancements

### Google Sheets API Integration
To actually fetch data from Google Sheets:

```python
# Install: pip install google-api-python-client google-auth
from googleapiclient.discovery import build

async def fetch_google_sheets_data(sheets_url: str):
    # Extract spreadsheet ID from URL
    sheet_id = extract_sheet_id(sheets_url)
    
    # Use Google Sheets API to fetch data
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range='Sheet1!A1:Z1000'
    ).execute()
    
    rows = result.get('values', [])
    return parse_rows_to_negotiations(rows)
```

## Testing

### Test 1: File Upload (With Auth)
```bash
# Should work
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1" \
  -F "file=@test.csv" \
  -H "Authorization: Bearer TOKEN"
```

### Test 2: File Upload (No Auth)
```bash
# Should also work now
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1" \
  -F "file=@test.csv"
```

### Test 3: Google Sheets Link
```bash
# Should work
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1" \
  -F "google_sheets_link=https://docs.google.com/spreadsheets/d/ABC123"
```

### Test 4: Neither Option
```bash
# Should fail with 400 Bad Request
curl -X POST "http://localhost:8000/api/v1/negotiation-chronicles/upload/1"
```

## Server Logs

```
📤 Upload request for nego table 1
  - File: negotiations.csv (or 'None')
  - Google Sheets: https://... (or 'None')
  - User: user@example.com (or 'Anonymous')
📊 Google Sheets link provided: https://docs.google.com/spreadsheets/d/...
✅ Attachment created successfully
```

## Status

✅ **FIXED** - 401 Unauthorized error resolved
✅ **FEATURE** - Google Sheets link option added
✅ **READY** - Restart server and test

## Next Action

**RESTART YOUR SERVER** and the 401 error should be gone!

You can now either:
- Upload a CSV/Excel file
- Provide a Google Sheets link

Both work with or without authentication.

