# Profile Edit and Avatar Fix - Complete Implementation

## Overview
Fixed profile editing functionality for Admin, BDD User, and Agent/Broker roles. Users can now:
- ✅ Update their profile information (name, email, phone, company)
- ✅ Change their password
- ✅ Upload and update their avatar image
- ✅ See their avatar displayed throughout the application

## Problem
The original implementation had several issues:
1. Profile update endpoint did not exist (only admin-level user updates)
2. No avatar support in the database or API
3. Frontend used mock API calls that didn't save anything
4. Avatar changes weren't reflected throughout the app

## Solution Implemented

### Backend Changes

#### 1. Database Schema Updates
**File**: `app/models/user.py`
- Added `avatar_url` field (String, 500 chars, nullable)
- Stores Cloudinary URL for user avatar images

**Migration**: `alembic/versions/4b11a6d6f1ca_add_avatar_url_to_user.py`
```python
def upgrade():
    op.add_column('user', sa.Column('avatar_url', sa.String(length=500), nullable=True))

def downgrade():
    op.drop_column('user', 'avatar_url')
```

#### 2. Schema Updates
**File**: `app/schemas/user.py`
- Added `avatar_url` to `UserRead`, `UserUpdate`, and `UserPublic` schemas
- Ensures avatar URL is returned in all user API responses

#### 3. New API Endpoints
**File**: `app/api/v1/auth.py`

**GET /api/v1/auth/me**
- Returns current user profile including avatar_url

**PATCH /api/v1/auth/me**
- Allows users to update their own profile
- Fields: first_name, middle_name, last_name, email, phone, company
- Validates Philippines phone numbers
- Checks email uniqueness
- Updates session data

**PATCH /api/v1/auth/password**
- Allows users to change their password
- Validates current password
- Enforces minimum 8 character length for new password

**POST /api/v1/auth/avatar**
- Upload avatar image (5MB limit)
- Validates image file type
- Stores in Cloudinary at `avatars/user_{id}/`
- Returns secure URL

### Frontend Changes

#### 1. Profile API Client
**New File**: `src/lib/profile-api.ts`
- `getProfile()` - Fetch current user profile
- `updateProfile()` - Update profile information
- `changePassword()` - Change password
- `uploadAvatar()` - Upload avatar image

#### 2. Profile Page Updates
**File**: `src/app/(dashboard)/profile/page.tsx`

**Profile Update**:
- Replaced mock implementation with real API call
- Updates session after successful save
- Shows proper error messages

**Password Change**:
- Validates password match and length
- Calls real backend API
- Clears form on success

**Avatar Upload**:
- Immediate preview of selected image
- Uploads to Cloudinary via backend
- Updates session with new avatar URL
- Shows success/error notifications

#### 3. NextAuth Session Updates
**File**: `src/lib/auth.ts`

**Added avatar_url to**:
- Session.user interface
- User interface  
- JWT interface

**Updated callbacks**:
- `jwt()` - Stores avatar_url in token
- `jwt()` with trigger="update" - Updates avatar_url when profile changes
- `session()` - Includes avatar_url in session

#### 4. Avatar Display Updates

**Header Component** (`src/components/layout/header.tsx`):
- Added `avatar_url` to user prop interface
- Displays avatar image if available
- Falls back to initials if no avatar

**Dashboard Layout** (`src/components/layout/dashboard-layout.tsx`):
- Passes `avatar_url` from session to Header component

**Profile Page** (`src/app/(dashboard)/profile/page.tsx`):
- Displays avatar with preview on change
- Shows fallback initials if no avatar

## API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| PATCH | `/api/v1/auth/me` | Update own profile | Yes |
| PATCH | `/api/v1/auth/password` | Change password | Yes |
| POST | `/api/v1/auth/avatar` | Upload avatar | Yes |

## File Upload Details

**Avatar Upload**:
- Max size: 5MB
- Allowed: Image files only (image/*)
- Storage: Cloudinary
- Path: `BDD_CLOUDINARY/avatars/user_{user_id}/`
- Returns: Secure HTTPS URL

## Testing

### Profile Update
1. Navigate to `/profile`
2. Update name, email, phone, or company
3. Click "Save Changes"
4. Verify success message
5. Reload page - changes should persist

### Password Change
1. Go to "Security" tab in profile
2. Enter current password
3. Enter new password (min 8 chars)
4. Confirm new password
5. Click "Change Password"
6. Log out and log back in with new password

### Avatar Upload
1. Go to profile page
2. Click camera icon on avatar
3. Select an image (< 5MB)
4. Image uploads automatically
5. Avatar appears immediately
6. Check header - avatar should update there too
7. Reload page - avatar should persist

## Migration Steps

### On Staging/Production

1. **Apply database migration**:
```bash
cd /path/to/bdd_server
alembic upgrade head
```

2. **Restart backend server** (Railway auto-deploys)

3. **Clear browser cache** for frontend

4. **Test with a user account**:
   - Log in
   - Go to profile
   - Update information
   - Upload avatar
   - Verify changes persist

## Configuration Required

### Cloudinary (Already configured)
Ensure these environment variables are set:
```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=BDD_CLOUDINARY
```

## Security Considerations

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Users can only update their own profile
3. **File Validation**: 
   - File type checked (images only)
   - File size limited (5MB)
4. **Email Uniqueness**: Prevents duplicate emails
5. **Password Security**:
   - Current password required
   - Minimum length enforced
   - Passwords hashed with bcrypt

## Benefits

✅ **Complete Profile Management**: Users control their own data
✅ **Visual Identity**: Avatar uploads enhance user experience  
✅ **Real-time Updates**: Changes reflect immediately across the app
✅ **Admin Independence**: Admins no longer need to update basic user info
✅ **Session Synchronization**: Profile changes update the session automatically

## Future Enhancements

- Image cropping/resizing UI
- Multiple profile pictures
- Avatar deletion option
- Profile picture gallery
- Social profile links
- Email verification on email change

## Troubleshooting

**Avatar not uploading?**
- Check Cloudinary credentials in environment variables
- Verify image is < 5MB
- Check browser console for errors

**Profile changes not saving?**
- Check network tab for API errors
- Verify JWT token is valid
- Check server logs for errors

**Avatar not displaying?**
- Clear browser cache
- Check if avatar_url is in session (dev tools)
- Verify Cloudinary URL is accessible

## Related Files

### Backend
- `app/models/user.py`
- `app/schemas/user.py`
- `app/api/v1/auth.py`
- `alembic/versions/4b11a6d6f1ca_add_avatar_url_to_user.py`

### Frontend
- `src/lib/profile-api.ts` (new)
- `src/lib/auth.ts`
- `src/app/(dashboard)/profile/page.tsx`
- `src/components/layout/header.tsx`
- `src/components/layout/dashboard-layout.tsx`

## Migration Applied
✅ Migration `4b11a6d6f1ca` successfully applied on database
✅ `avatar_url` column added to `user` table

