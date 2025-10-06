# Merge Properties Feature Guide

## ✅ Status: **FULLY WORKING**

The merge properties feature is now fully functional with proper database tracking and user notifications.

## What Does Merge Do?

When you merge duplicate properties, the system:

1. ✅ **Marks duplicates in database** using `is_duplicate`, `duplicate_of_id`, `duplicate_notes` fields
2. ✅ **Creates notifications** for property owners
3. ✅ **Sends email alerts** to affected users
4. ✅ **Updates property descriptions** with merge information
5. ✅ **Maintains data integrity** by keeping relationships

## API Endpoint

### POST `/api/v1/duplicates/merge`

**Authorization:** Admin or BDD_USER

**Request Body:**
```json
{
  "primary_property_id": 123,
  "duplicate_property_ids": [456, 789],
  "merge_notes": "Optional notes about the merge"
}
```

**Response:**
```json
{
  "message": "Properties merged successfully",
  "primary_property": {
    "id": 123,
    "name": "Primary Property Name",
    "description": "...\n\nMERGED WITH PROPERTIES: 456, 789\nMerge notes: ..."
  },
  "merged_properties": [
    {
      "id": 456,
      "name": "Duplicate Property Name",
      "status": "marked_as_merged",
      "is_duplicate": true,
      "duplicate_of_id": 123
    }
  ]
}
```

## How It Works

### Step-by-Step Process

1. **Admin initiates merge** from Duplicate Checker UI or API
2. **System validates:**
   - User has ADMIN role
   - Primary property exists
   - All duplicate properties exist
3. **For each duplicate property:**
   - Sets `is_duplicate = true`
   - Sets `duplicate_of_id = primary_property_id`
   - Adds merge notes to `duplicate_notes` field
   - Creates notification for property owner
   - Sends email alert
4. **Updates primary property:**
   - Adds merge information to description
   - Lists all merged property IDs
5. **Returns success response** with all updated properties

### Database Changes

**Duplicate Property (ID: 456):**
```sql
UPDATE properties SET
  is_duplicate = true,
  duplicate_of_id = 123,
  duplicate_notes = 'MERGED INTO PROPERTY #123. Notes: ...'
WHERE id = 456;
```

**Primary Property (ID: 123):**
```sql
UPDATE properties SET
  description = description || '\n\nMERGED WITH PROPERTIES: 456, 789\nMerge notes: ...'
WHERE id = 123;
```

**Notification Created:**
```sql
INSERT INTO notifications (
  user_id,
  notification_type,
  title,
  message,
  property_id,
  duplicate_property_id,
  is_read,
  created_at
) VALUES (
  <owner_user_id>,
  'PROPERTY_MERGED',
  'Property Merged',
  'Your property "..." has been merged into property "..."',
  456,
  123,
  false,
  NOW()
);
```

## Using the Merge Feature

### From Duplicate Checker UI

1. Navigate to **Duplicate Checker** page
2. Find duplicate properties in the list
3. Click **"Merge Properties"** button
4. Confirm the merge action
5. System automatically:
   - Merges properties in database
   - Notifies property owners
   - Refreshes the property list

### From API (Using curl)

```bash
# Get your auth token first
TOKEN="your_admin_token_here"

# Merge properties
curl -X POST http://localhost:8000/api/v1/duplicates/merge \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_property_id": 123,
    "duplicate_property_ids": [456],
    "merge_notes": "Properties have identical title numbers and addresses"
  }'
```

### From Client Application

```typescript
import { apiClient } from '@/lib/api'

// Set auth token
apiClient.setAuthToken(session.accessToken)

// Merge properties
const result = await apiClient.post('/api/v1/duplicates/merge', {
  primary_property_id: 123,
  duplicate_property_ids: [456, 789],
  merge_notes: 'Merged via duplicate checker'
})

console.log(result.message) // "Properties merged successfully"
```

## User Notifications

### What Property Owners Receive

**In-App Notification:**
- Title: "Property Merged"
- Message: "Your property 'XYZ' (ID: 456) has been merged into property 'ABC' (ID: 123). Merge notes: ..."
- Type: PROPERTY_MERGED
- Links to both properties

**Email Alert:**
- Subject: "Property Merged"
- Body: Same message as in-app notification
- Sent to property owner's email address

### Checking Notifications

```typescript
// Get user's notifications
const notifications = await apiClient.getNotifications()

// Get unread count
const { unread_count } = await apiClient.getUnreadCount()

// Mark as read
await apiClient.markNotificationAsRead(notificationId)
```

## Querying Merged Properties

### Find All Duplicates

```sql
SELECT * FROM properties 
WHERE is_duplicate = true;
```

### Find Properties Merged Into a Specific Property

```sql
SELECT * FROM properties 
WHERE duplicate_of_id = 123;
```

### Get Full Merge Relationship

```sql
SELECT 
  p1.id as duplicate_id,
  p1.name as duplicate_name,
  p1.duplicate_notes,
  p2.id as primary_id,
  p2.name as primary_name
FROM properties p1
JOIN properties p2 ON p1.duplicate_of_id = p2.id
WHERE p1.is_duplicate = true;
```

## Permissions

### Who Can Merge Properties?

- ✅ **ADMIN** - Full merge access
- ✅ **BDD_USER** - Can merge properties (BDD employees)
- ❌ **AGENT** - Cannot merge (can only submit properties)
- ❌ **BROKER** - Cannot merge (can only review properties)

### Permission Check in Code

```python
if current_user.role.value not in ["ADMIN", "BDD_USER"]:
    raise HTTPException(status_code=403, detail="Not authorized to merge properties")
```

## Best Practices

### 1. Review Before Merging
- Always verify properties are actual duplicates
- Check all property details match
- Review similarity scores
- Check with property owners if uncertain

### 2. Choose the Right Primary Property
- Usually the oldest property (created first)
- The one with most complete information
- The one with more attachments/documents
- The one with active negotiation tables

### 3. Add Detailed Merge Notes
```json
{
  "merge_notes": "Exact title number match (TCT-12345). Same address, owner, and lot area. Property #456 was submitted 2 days later as duplicate."
}
```

### 4. Notify Users Promptly
The system automatically sends notifications, but you may want to:
- Follow up with a phone call for high-value properties
- Provide additional context if needed
- Explain what happens to their property after merge

## Testing the Merge Feature

### Test Scenario 1: Simple Merge
```bash
# 1. Create two test properties
# 2. Mark them as duplicates
# 3. Merge them
curl -X POST http://localhost:8000/api/v1/duplicates/merge \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"primary_property_id": 1, "duplicate_property_ids": [2]}'

# 4. Verify in database
psql -d bdd -c "SELECT id, name, is_duplicate, duplicate_of_id FROM properties WHERE id IN (1,2);"
```

### Test Scenario 2: Multiple Duplicates
```bash
# Merge multiple duplicates into one primary
curl -X POST http://localhost:8000/api/v1/duplicates/merge \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"primary_property_id": 1, "duplicate_property_ids": [2, 3, 4]}'
```

### Test Scenario 3: Verify Notifications
```bash
# Check that notifications were created
psql -d bdd -c "SELECT * FROM notifications WHERE notification_type = 'PROPERTY_MERGED' ORDER BY created_at DESC LIMIT 5;"
```

## Troubleshooting

### Error: "Not authorized to merge properties"
**Solution:** Ensure user has ADMIN role:
```sql
UPDATE "user" SET role = 'ADMIN' WHERE email = 'your@email.com';
```

### Error: "Primary property not found"
**Solution:** Verify property exists:
```sql
SELECT id, name FROM properties WHERE id = 123;
```

### Error: "Duplicate property X not found"
**Solution:** Check all property IDs exist before merging

### Merge Not Updating Database
**Solution:** 
1. Check migration was run: `alembic current`
2. Verify columns exist: `\d properties` in psql
3. Restart server after migration

## Future Enhancements

### Planned Features:
1. **Attachment Transfer** - Move files from duplicate to primary
2. **Workflow History Merge** - Combine status change history
3. **Negotiation Table Merge** - Consolidate negotiation data
4. **Undo Merge** - Reverse a merge operation
5. **Merge Preview** - Show what will happen before merging
6. **Batch Merge** - Merge multiple property groups at once
7. **Merge Approval Workflow** - Require multiple admin approvals

### API Enhancement Ideas:
```python
# Undo merge
POST /api/v1/duplicates/{property_id}/unmerge

# Preview merge (dry run)
POST /api/v1/duplicates/merge-preview

# Transfer specific data
POST /api/v1/duplicates/merge-custom
{
  "primary_property_id": 123,
  "duplicate_property_id": 456,
  "transfer_attachments": true,
  "transfer_history": true,
  "transfer_negotiations": false
}
```

## Summary

✅ **Merge Properties is FULLY WORKING**

The feature now:
- Properly marks duplicates in database
- Sets foreign key relationships
- Notifies all affected users
- Sends email alerts
- Maintains data integrity
- Requires admin authorization
- Provides detailed response data

You can safely use this feature in production! 🚀

---

**Last Updated:** October 3, 2025  
**Status:** Production Ready  
**Version:** 1.0.0

