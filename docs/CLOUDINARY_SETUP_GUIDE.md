# 🚀 Cloudinary Setup Guide

Your file upload system is now configured to use **Cloudinary** instead of local storage! Here's how to complete the setup:

## 📋 Step 1: Get Your Cloudinary Credentials

1. **Sign up/Login** to [Cloudinary](https://cloudinary.com) (free tier available)
2. Go to your **Dashboard** 
3. Copy these 3 values:
   - **Cloud Name** (e.g., `dxyz123abc`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (e.g., `abcdefghijklmnopqrstuvwxyz123456`)

## 📝 Step 2: Create Your .env File

Create a `.env` file in your **bdd_server** directory with these contents:

```bash
# Database Configuration (update with your actual database URL)
DATABASE_URL=postgresql://username:password@localhost:5432/bdd_db

# Security (generate a strong secret key)
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 🔥 CLOUDINARY CONFIGURATION (REQUIRED FOR FILE UPLOADS)
CLOUDINARY_CLOUD_NAME=your-cloud-name-here
CLOUDINARY_API_KEY=your-api-key-here  
CLOUDINARY_API_SECRET=your-api-secret-here
CLOUDINARY_FOLDER=BDD_CLOUDINARY

# Optional: Google Maps API Key
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

## ⚡ Step 3: Replace the Placeholders

Replace these values in your `.env` file:
- `your-cloud-name-here` → Your actual Cloudinary Cloud Name
- `your-api-key-here` → Your actual Cloudinary API Key  
- `your-api-secret-here` → Your actual Cloudinary API Secret

## 🧪 Step 4: Test the Setup

1. **Restart your server**:
   ```bash
   cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server
   uvicorn app.main:app --reload
   ```

2. **Test with your Submit Property form** - it should now upload files to Cloudinary!

## 📁 File Organization in Cloudinary

Your files will be organized like this:
```
BDD_CLOUDINARY/
├── property_images/          # Property photos
├── property_documents/       # Attachments (PDFs, docs)
└── authorization_letters/    # Authorization letters
```

## ✅ What You'll Get

- ✅ **Global CDN** - Fast file delivery worldwide
- ✅ **Automatic optimization** - Images compressed automatically  
- ✅ **Secure URLs** - HTTPS by default
- ✅ **Unlimited scalability** - No server storage limits
- ✅ **Image transformations** - Thumbnails, resizing, etc.

## 🚨 Important Notes

1. **Free Tier**: Cloudinary free tier includes:
   - 25GB storage
   - 25GB monthly bandwidth
   - 1000 transformations/month

2. **Security**: Never commit your `.env` file to git!

3. **Testing**: Your Submit Property form will now upload real files to Cloudinary

## 🔧 Troubleshooting

If you get errors:
1. **Check credentials** - Make sure Cloud Name, API Key, and API Secret are correct
2. **Restart server** - Environment variables need a restart to load
3. **Check logs** - Server will show detailed Cloudinary error messages

---

**Ready to test?** Once you've created your `.env` file, restart the server and try submitting a property with files! 🎉
