# BDD Client-Server Connection Setup

This document provides step-by-step instructions for connecting your BDD Client (Next.js) to the BDD Server (FastAPI).

## 🔗 Connection Overview

- **Client**: Next.js application running on `http://localhost:3000`
- **Server**: FastAPI application running on `http://localhost:8000`
- **Communication**: REST API with JWT authentication
- **CORS**: Properly configured for local development

## 📋 Prerequisites

1. **PostgreSQL Database** running and accessible
2. **Node.js 18+** and **Python 3.11+** installed
3. Both projects cloned in your workspace

## 🚀 Setup Instructions

### 1. Server Setup (bdd_server)

```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment configuration is already set up in .env
# Database setup
createdb bdd_property_tracker
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Client Setup (bdd_client)

```bash
cd /Users/kyleisaacmendoza/Documents/workspace/bdd_client

# Install dependencies
npm install

# Environment configuration is already set up in .env
# Start client
npm run dev
```

## 🔧 Environment Configuration

### Server (.env)
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/bdd_property_tracker

# Security
SECRET_KEY=bdd-super-secret-key-change-in-production-2024

# CORS - Includes Next.js client
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://your-production-domain.com
```

### Client (.env)
```env
# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=bdd-client-super-secret-key-change-in-production-2024

# Backend API Connection
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Specific Endpoints
NEXT_PUBLIC_AUTH_LOGIN_URL=http://localhost:8000/api/v1/auth/jwt/login
NEXT_PUBLIC_PROPERTIES_URL=http://localhost:8000/api/v1/properties
```

## 🛠️ API Client Configuration

The client includes pre-configured API utilities:

### API Client (`src/lib/api-client.ts`)
```typescript
import apiClient from '@/lib/api-client';

// Set authentication token
apiClient.setToken(userToken);

// Make API calls
const properties = await apiClient.get('/properties');
const newProperty = await apiClient.post('/properties', propertyData);
```

### API Configuration (`src/lib/api-config.ts`)
```typescript
import { AUTH_ENDPOINTS, PROPERTY_ENDPOINTS } from '@/lib/api-config';

// All endpoints are pre-configured
console.log(AUTH_ENDPOINTS.LOGIN); // http://localhost:8000/api/v1/auth/jwt/login
console.log(PROPERTY_ENDPOINTS.LIST); // http://localhost:8000/api/v1/properties
```

## 🧪 Testing the Connection

### 1. Connection Test Component
A `ConnectionTest` component has been created at `src/components/connection-test.tsx` to verify the connection.

### 2. Manual Testing

#### Test Server Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "BDD Property Tracker",
  "version": "1.0.0"
}
```

#### Test CORS
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/v1/properties
```

### 3. API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Authentication Flow

### 1. User Registration
```typescript
const registerData = {
  email: "user@example.com",
  password: "password123",
  first_name: "John",
  last_name: "Doe",
  role: "AGENT"
};

const response = await apiClient.post('/auth/register', registerData);
```

### 2. User Login
```typescript
const formData = new FormData();
formData.append('username', 'user@example.com');
formData.append('password', 'password123');

const response = await apiClient.postForm('/auth/jwt/login', formData);
// Token will be in cookies or response headers
```

### 3. Authenticated Requests
```typescript
// Set token (usually from login response or cookies)
apiClient.setToken(jwtToken);

// All subsequent requests will include Authorization header
const userProfile = await apiClient.get('/users/me');
```

## 📊 Available API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/jwt/login` - Login
- `GET /api/v1/users/me` - Get current user

### Properties
- `GET /api/v1/properties` - List properties
- `POST /api/v1/properties` - Create property
- `GET /api/v1/properties/{id}` - Get property
- `PATCH /api/v1/properties/{id}` - Update property
- `PATCH /api/v1/properties/{id}/status` - Update status

### Duplicates
- `POST /api/v1/duplicates/check` - Check for duplicates
- `POST /api/v1/duplicates/{id}/mark-duplicate` - Mark as duplicate

### Admin (Admin/Manager only)
- `GET /api/v1/admin/users` - List users
- `GET /api/v1/admin/properties/stats` - Property statistics

## 🚨 Troubleshooting

### Common Issues

#### 1. CORS Errors
**Problem**: `Access-Control-Allow-Origin` error in browser
**Solution**: Ensure `ALLOWED_ORIGINS` in server `.env` includes `http://localhost:3000`

#### 2. Connection Refused
**Problem**: `ECONNREFUSED` error
**Solution**: Ensure server is running on port 8000

#### 3. Authentication Errors
**Problem**: 401 Unauthorized responses
**Solution**: Verify JWT token is being sent in Authorization header

#### 4. Database Connection
**Problem**: Database connection errors
**Solution**: Ensure PostgreSQL is running and credentials are correct

### Debug Steps

1. **Check server status**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify CORS headers**:
   ```bash
   curl -I -H "Origin: http://localhost:3000" http://localhost:8000/api/v1/properties
   ```

3. **Test API endpoints**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","password":"test123","first_name":"Test","last_name":"User","role":"AGENT"}'
   ```

## 🌐 Production Deployment

### Environment Variables for Production

#### Server
```env
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/bdd_property_tracker
SECRET_KEY=super-secure-production-secret
ALLOWED_ORIGINS=https://your-client-domain.com
```

#### Client
```env
NEXT_PUBLIC_API_URL=https://your-server-domain.com
NEXT_PUBLIC_API_BASE_URL=https://your-server-domain.com/api/v1
NEXTAUTH_URL=https://your-client-domain.com
```

## ✅ Success Checklist

- [ ] Server runs on http://localhost:8000
- [ ] Client runs on http://localhost:3000  
- [ ] Health check returns 200 status
- [ ] CORS headers are present
- [ ] Can register new user
- [ ] Can login user
- [ ] Can fetch user profile
- [ ] Can create/read properties
- [ ] Connection test component shows green status

## 📞 Support

If you encounter issues:

1. Check the console logs in both client and server
2. Verify environment variables are loaded correctly
3. Ensure database is accessible
4. Test API endpoints individually using curl or Postman
5. Use the ConnectionTest component for quick debugging

Your BDD Client and Server are now properly connected and ready for development! 🎉