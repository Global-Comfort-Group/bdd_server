# Duplicate Tracking & Notification Feature

## Overview

This feature adds comprehensive duplicate property detection, tracking, and user notification capabilities to the BDD Property Tracker system.

## Features Implemented

### 1. Database Schema Enhancements

#### **New Tables:**
- `notifications` - Stores user notifications with types, messages, and read status
  - Columns: id, user_id, notification_type, title, message, property_id, duplicate_property_id, is_read, created_at, read_at

#### **Property Table Updates:**
- `is_duplicate` (Boolean) - Flags if property is marked as duplicate
- `duplicate_of_id` (Integer, FK) - References the original property
- `duplicate_notes` (Text) - Additional notes about the duplication

#### **Migration:**
- File: `alembic/versions/f3950a9ad6f4_add_duplicate_tracking_and_notifications.py`
- Run with: `alembic upgrade head`

### 2. Notification System

#### **Notification Types:**
```python
- DUPLICATE_DETECTED      # When duplicate is found
- PROPERTY_APPROVED       # When property is approved
- PROPERTY_REJECTED       # When property is rejected
- PROPERTY_ASSIGNED       # When reviewer is assigned
- PROPERTY_MERGED         # When properties are merged
- SYSTEM_ALERT            # General system alerts
```

#### **Backend Services:**

**NotificationService** (`app/services/notification.py`):
- `create_notification()` - Create new notifications
- `get_user_notifications()` - Get notifications for a user
- `mark_as_read()` - Mark notification as read
- `mark_all_as_read()` - Mark all user notifications as read
- `delete_notification()` - Delete a notification
- `get_unread_count()` - Get unread notification count
- `create_duplicate_notification()` - Helper for duplicate notifications
- Email integration via `EmailService`

**API Endpoints** (`app/api/v1/notifications.py`):
```
GET    /api/v1/notifications              # Get current user's notifications
GET    /api/v1/notifications/unread-count # Get unread count
PATCH  /api/v1/notifications/{id}/read    # Mark as read
POST   /api/v1/notifications/mark-all-read # Mark all as read
DELETE /api/v1/notifications/{id}         # Delete notification
```

### 3. Enhanced Duplicate Detection

#### **DuplicateDetectionService Updates** (`app/services/duplicate.py`):

**New Methods:**
- `mark_property_as_duplicate()` - Mark property as duplicate with proper DB fields
- `check_and_notify_duplicates()` - Check for duplicates and auto-notify users

**Existing Methods:**
- `check_duplicates()` - Multi-criteria duplicate checking
  - Exact title number match (100% confidence)
  - Fuzzy address matching (configurable threshold)
  - Geographic proximity (within 500m radius)
- `check_duplicates_by_criteria()` - Flexible criteria-based search
- `calculate_similarity_score()` - Comprehensive similarity scoring

#### **Duplicate Detection Criteria:**
1. **Title Number** (Exact Match - 100% score)
2. **Address Similarity** (Fuzzy matching - 40% weight)
3. **Name Similarity** (Fuzzy matching - 30% weight)
4. **Location Proximity** (Haversine distance - 30% weight)

### 4. Updated Duplicate Marking Endpoint

**Enhanced `/api/v1/duplicates/{property_id}/mark-duplicate`:**
- Uses new database fields (is_duplicate, duplicate_of_id, duplicate_notes)
- Automatically notifies property owner
- Sends email notification
- Returns updated property with duplicate relationship

### 5. Client-Side Implementation

#### **New Types** (`src/types/notification.ts`):
```typescript
interface Notification {
  id: number
  user_id: number
  notification_type: NotificationType
  title: string
  message: string
  property_id?: number
  duplicate_property_id?: number
  is_read: boolean
  created_at: string
  read_at?: string
}
```

#### **API Client Updates** (`src/lib/api.ts`):
```typescript
- getNotifications(unreadOnly)
- getUnreadCount()
- markNotificationAsRead(id)
- markAllNotificationsAsRead()
- deleteNotification(id)
```

#### **New UI Component:**
**NotificationBell** (`src/components/ui/notification-bell.tsx`):
- Bell icon with unread badge
- Dropdown menu with scrollable notifications
- Real-time unread count updates (polls every 30s)
- Mark as read / Mark all as read actions
- Delete notification action
- Timestamp formatting ("2 hours ago")

### 6. Email Notifications

**Automatic Email Alerts:**
- When property marked as duplicate
- Configurable via `EmailService`
- Uses SMTP settings from `.env`:
  - `SMTP_HOST`
  - `SMTP_PORT`
  - `SMTP_USER`
  - `SMTP_PASSWORD`

## Usage

### Backend

#### Mark Property as Duplicate (Admin/BDD User):
```python
POST /api/v1/duplicates/{property_id}/mark-duplicate
Query Params:
  - original_property_id: int
  - notes: str (optional)
```

#### Check for Duplicates:
```python
POST /api/v1/duplicates/check
Body: PropertyCreate schema
Response: List[DuplicateResult]
```

#### Get Notifications:
```python
GET /api/v1/notifications?unread_only=false&limit=50
Response: List[Notification]
```

### Frontend

#### Add Notification Bell to Layout:
```tsx
import { NotificationBell } from '@/components/ui/notification-bell'

// In your layout/header:
<NotificationBell />
```

#### Check for Duplicates Before Submission:
```typescript
import { apiClient } from '@/lib/api'

const duplicates = await apiClient.post('/api/v1/duplicates/check', propertyData)
if (duplicates.length > 0) {
  // Show warning to user
  // Ask for confirmation before proceeding
}
```

## Configuration

### Environment Variables (Backend):

```env
# Email Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your_password

# Database
DATABASE_URL=postgresql://user:pass@host:5432/bdd

# Security
SECRET_KEY=your_secret_key
```

### Frontend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### Duplicate Detection Tests:
```bash
# Run duplicate tests
cd bdd_server
pytest tests/test_duplicates.py -v
```

### Test Scenarios:
1. ✅ Exact title number match
2. ✅ Fuzzy address matching
3. ✅ Geographic proximity detection
4. ✅ Mark property as duplicate
5. ✅ Merge duplicate properties
6. ✅ Calculate similarity scores
7. ✅ Unauthorized access prevention

## Integration Points

### Property Creation Flow:
```python
1. User submits property
2. DuplicateDetectionService.check_duplicates()
3. If duplicates found (score >= 0.75):
   - Create notification for user
   - Send email alert
   - Log duplicate detection
4. Proceed with creation (or warn user)
```

### Notification Flow:
```python
1. Event occurs (duplicate detected, property approved, etc.)
2. NotificationService.create_notification()
3. Save to database
4. EmailService.send_email() (optional)
5. User sees notification in UI
6. User marks as read or deletes
```

## Best Practices

### Duplicate Detection:
- Use threshold >= 0.75 for high-confidence matches
- Combine multiple criteria for better accuracy
- Always check exact title number first
- Consider geographic proximity for physical properties

### Notifications:
- Send email only for important events
- Batch notifications to avoid spam
- Auto-mark as read after 30 days (consider implementing)
- Provide clear action items in notification text

### Performance:
- Index on `title_number` for fast exact matches
- Use database-level fuzzy matching for large datasets
- Cache duplicate check results temporarily
- Poll for notifications every 30 seconds (not more frequent)

## Future Enhancements

1. **Batch Duplicate Detection:**
   - Scan all properties periodically
   - Generate duplicate reports
   - Admin dashboard for reviewing duplicates

2. **Smart Merge:**
   - Auto-merge property data
   - Transfer attachments
   - Consolidate workflow history

3. **Machine Learning:**
   - Train ML model on confirmed duplicates
   - Improve matching accuracy over time
   - Detect pattern-based duplicates

4. **Real-time Notifications:**
   - WebSocket support for instant updates
   - Push notifications
   - In-app toast notifications

5. **Duplicate Confidence Levels:**
   - High (>90%): Auto-flag
   - Medium (70-90%): Notify for review
   - Low (50-70%): Show warning only

## API Documentation

Full API documentation available at:
- Development: `http://localhost:8000/docs`
- Production: `https://your-api-url.com/docs`

## Support

For issues or questions:
1. Check logs in `bdd_server/logs/`
2. Review migration status: `alembic current`
3. Verify database schema: `alembic show f3950a9ad6f4`
4. Test API endpoints in `/docs` interface

## Changelog

**Version 1.0.0 - October 3, 2025**
- ✅ Added notifications table
- ✅ Added duplicate tracking fields to properties
- ✅ Implemented NotificationService
- ✅ Enhanced DuplicateDetectionService
- ✅ Created notification API endpoints
- ✅ Built NotificationBell UI component
- ✅ Added email notification support
- ✅ Updated API client with notification methods
- ✅ Created database migration

