# Cloudinary Integration Setup Guide

Your BDD Property Tracker now uses **Cloudinary** for file storage instead of local file storage. This provides better performance, scalability, and automatic image optimization.

## ✅ What's Been Updated

### 1. **Database Schema**
- `property_attachments` table now stores Cloudinary metadata instead of file paths
- New fields: `cloudinary_public_id`, `cloudinary_url`, `cloudinary_secure_url`
- Added `width` and `height` fields for images

### 2. **Models & Schemas**
- Updated `PropertyAttachment` model with Cloudinary fields
- Updated Pydantic schemas to match new structure

### 3. **Services**
- **`CloudinaryService`** - Core Cloudinary integration
- **`FileStorageService`** - Updated to use Cloudinary instead of local storage
- Automatic image optimization and transformations

### 4. **API Endpoints**
- **`POST /api/v1/uploads/property/{property_id}/attachment`** - Upload file to property
- **`DELETE /api/v1/uploads/attachment/{attachment_id}`** - Delete attachment
- **`GET /api/v1/uploads/attachment/{attachment_id}/thumbnail`** - Get thumbnail URL
- **`POST /api/v1/uploads/test-upload`** - Test endpoint for development

## 🚀 Setup Instructions

### 1. **Get Cloudinary Account**
1. Sign up at [cloudinary.com](https://cloudinary.com) (free tier available)
2. Go to your Dashboard to get credentials
3. Note down: `Cloud Name`, `API Key`, `API Secret`

### 2. **Configure Environment Variables**
Add to your `.env` file:
```bash
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key  
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=BDD_CLOUDINARY  # Optional: defaults to BDD_CLOUDINARY
```

### 3. **Test the Integration**
```bash
# Start your server
uvicorn app.main:app --reload

# Test upload endpoint (requires authentication)
curl -X POST "http://localhost:8000/api/v1/uploads/test-upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/test-image.jpg"
```

## 🎯 Key Features

### **Automatic Optimization**
- Images automatically compressed and optimized
- Multiple formats supported (JPEG, PNG, PDF, Word, Excel, etc.)
- Auto-format conversion for better performance

### **Transformations**
```python
# Generate thumbnail
thumbnail_url = file_storage_service.get_thumbnail_url(
    public_id="your_file_id",
    width=300,
    height=200
)

# Custom transformations
custom_url = cloudinary_service.generate_url(
    public_id="your_file_id",
    transformation={
        "width": 500,
        "height": 300,
        "crop": "fill",
        "quality": "auto"
    }
)
```

### **Security**
- Secure HTTPS URLs by default
- File type validation
- Size limits enforced
- Unique public IDs prevent conflicts

## 📁 File Organization

Files are organized in Cloudinary with your custom collection:
```
BDD_CLOUDINARY/          # Your main collection
├── properties/          # General property files
├── property_1/          # Files for property ID 1
├── property_2/          # Files for property ID 2
└── test/                # Test uploads
```

This keeps all your BDD Property Tracker files organized in one main collection, making it easy to:
- **Find files** - All BDD files in one place
- **Manage permissions** - Apply settings to entire collection
- **Track usage** - Monitor storage and bandwidth per project
- **Backup/export** - Bulk operations on your collection

## 🔧 Development Features

### **Test Upload Endpoint**
Use `/api/v1/uploads/test-upload` for testing without creating database records.

### **Thumbnail Generation**
Automatic thumbnail URLs for images with customizable dimensions.

### **Error Handling**
- Graceful fallbacks if Cloudinary is unavailable
- Automatic cleanup on database failures
- Detailed error messages for debugging

## 📊 Benefits Over Local Storage

| Feature | Local Storage | Cloudinary |
|---------|--------------|------------|
| **Performance** | Limited by server | Global CDN |
| **Scalability** | Server dependent | Unlimited |
| **Image Processing** | Manual | Automatic |
| **Backup** | Manual | Automatic |
| **Bandwidth** | Your server | Cloudinary's CDN |
| **Mobile Optimization** | Manual | Automatic |

## 🚨 Important Notes

1. **Free Tier Limits**: Cloudinary free tier has monthly limits
2. **Environment Variables**: Required for production use
3. **Database Migration**: Existing local files need manual migration
4. **Testing**: Use test endpoint before production deployment

## 🔄 Migration from Local Files

If you have existing local files, you'll need to:
1. Upload them to Cloudinary
2. Update database records with Cloudinary URLs
3. Remove local files after verification

## 📝 API Documentation

Once your server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Look for the "uploads" section to see all available endpoints.

---

Your file upload system is now enterprise-ready with Cloudinary! 🎉