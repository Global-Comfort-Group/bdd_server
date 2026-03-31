# Business Requirements Specification (BRS)
## BDD Property Tracker System

---

### Document Information
- **Document Title**: Business Requirements Specification - BDD Property Tracker
- **Version**: 1.0
- **Date**: September 25, 2025
- **Prepared by**: Development Team
- **Related Documents**: BRD v1.0, Technical Architecture Document

---

## 1. Introduction

### 1.1 Purpose
This Business Requirements Specification (BRS) document provides detailed functional and technical specifications for the BDD Property Tracker system. It serves as the definitive guide for development, testing, and implementation teams.

### 1.2 Scope
This document covers all functional requirements, user interface specifications, data models, API specifications, and technical implementation details for the BDD Property Tracker system.

### 1.3 Document Structure
- **Section 2**: System Overview and Architecture
- **Section 3**: Detailed Functional Specifications
- **Section 4**: User Interface Specifications
- **Section 5**: Data Model Specifications
- **Section 6**: API Specifications
- **Section 7**: Security Specifications
- **Section 8**: Integration Specifications

---

## 2. System Overview

### 2.1 Architecture Overview
The BDD Property Tracker follows a modern three-tier architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  External APIs  │    │  File Storage   │    │   Migrations    │
│  - Google Maps  │    │  - Cloudinary   │    │   (Alembic)     │
│  - Philippines  │    │  - Local Files  │    │                 │
│    Address API  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 Technology Stack Details

#### 2.2.1 Frontend Stack
- **Framework**: Next.js 15.5.2
- **React Version**: 19.1.0
- **UI Library**: Radix UI components
- **Styling**: Tailwind CSS 4.0
- **State Management**: Zustand 5.0.8
- **Form Handling**: React Hook Form 7.62.0
- **Validation**: Zod 4.1.9
- **Authentication**: NextAuth.js 4.24.11
- **Maps**: Google Maps API (@googlemaps/js-api-loader 1.16.10)
- **Testing**: Playwright 1.55.0

#### 2.2.2 Backend Stack
- **Framework**: FastAPI 0.104.1
- **Python Version**: 3.11+
- **Database ORM**: SQLAlchemy 2.0.23
- **Database Driver**: psycopg2-binary 2.9.9
- **Migrations**: Alembic 1.12.1
- **Authentication**: FastAPI-Users 12.1.3
- **Password Hashing**: Passlib with bcrypt
- **JWT Tokens**: python-jose 3.3.0
- **File Processing**: Pillow 10.1.0
- **HTTP Client**: httpx 0.25.2
- **Fuzzy Matching**: fuzzywuzzy 0.18.0
- **Testing**: pytest 7.4.3 + pytest-asyncio 0.21.1

#### 2.2.3 Database Schema
- **Database**: PostgreSQL 13+
- **Connection Pooling**: SQLAlchemy async engine
- **Migration Management**: Alembic
- **Backup Strategy**: Automated daily backups

---

## 3. Detailed Functional Specifications

### 3.1 User Management System

#### 3.1.1 User Registration (FR-001-A)
**Specification**: Users can register for new accounts with approval workflow

**Input Requirements**:
- Email address (unique, validated)
- Password (8+ characters, complexity requirements)
- First name, middle name (optional), last name
- Company name (optional)
- Phone number (optional)
- Role selection (Agent, Broker)

**Business Rules**:
- Email must be unique across the system
- BDD_USER and ADMIN roles can only be created by administrators
- New accounts require approval before activation
- Password must meet security requirements

**Output**:
- Account created in pending status
- Email notification to administrators
- Confirmation message to user

#### 3.1.2 User Authentication (FR-001-B)
**Specification**: Secure login system with JWT tokens

**Input Requirements**:
- Email/username
- Password

**Business Rules**:
- Maximum 5 failed login attempts before lockout
- JWT token expires after 24 hours
- Refresh token mechanism for extended sessions
- Account must be active and verified

**Output**:
- JWT access token
- User profile information
- Role-based navigation permissions

#### 3.1.3 Role-Based Access Control (FR-001-C)
**Specification**: Four-tier role system with specific permissions

| Role | Permissions | Access Level |
|------|-------------|--------------|
| **ADMIN** | Full system access, user management, system configuration | System Administrator |
| **BDD_USER** | All properties, workflow management, duplicate resolution | Business User |
| **BROKER** | Own properties + agent properties, review capabilities | Supervisory User |
| **AGENT** | Own properties only, submit and edit | Basic User |

### 3.2 Property Management System

#### 3.2.1 Property Submission (FR-002-A)
**Specification**: Multi-step wizard for comprehensive property data entry

**Step 1: Basic Information**
- Property name (required, 1-200 characters)
- Property type (enum: RESIDENTIAL, COMMERCIAL, INDUSTRIAL, AGRICULTURAL, MIXED_USE)
- Description (optional, text area)

**Step 2: Location Details**
- Full address (required, 1-500 characters)
- Cascading Philippines address selection:
  - Region selection
  - Province selection (filtered by region)
  - City/Municipality selection (filtered by province)
  - Barangay selection (filtered by city)
- Street address (optional)
- ZIP code (optional)
- GPS coordinates (auto-generated or manual entry)

**Step 3: Property Details**
- Lot area (required, numeric, square meters)
- Zoning classification (required, text)
- Title number (required, unique, alphanumeric)
- Price (required, numeric with currency)
- Currency (default: PHP)

**Step 4: Transaction Details**
- Transaction status (enum: S=Sale, R=Rent, L=Lease)
- Additional terms (optional)

**Step 5: File Attachments**
- Multiple file upload support
- Accepted formats: PDF, DOC, DOCX, JPG, PNG, KMZ
- Maximum file size: 50MB per file
- File categorization (Title documents, Images, Maps, Other)

**Business Rules**:
- Title number must be unique across all properties
- Duplicate detection runs automatically on submission
- GPS coordinates auto-generated from address if possible
- All uploaded files scanned for security

#### 3.2.2 Property Search and Filtering (FR-002-B)
**Specification**: Advanced search capabilities with multiple filter options

**Search Fields**:
- Text search (property name, address, description)
- Property type filter
- Status filter (workflow status)
- Transaction status filter
- Price range filter
- Lot area range filter
- Date range filter (created, updated)
- Location filter (region, province, city)

**Search Results**:
- Paginated results (default 20 per page)
- Sortable columns
- Grid and table view options
- Export functionality

**Performance Requirements**:
- Search results returned within 2 seconds
- Support for complex filter combinations
- Real-time search suggestions

#### 3.2.3 Property Details View (FR-002-C)
**Specification**: Comprehensive property information display

**Information Sections**:
1. **Property Overview**: Name, type, status, key metrics
2. **Location Information**: Address, map view, coordinates
3. **Property Details**: Specifications, zoning, title information
4. **Financial Information**: Price, currency, transaction terms
5. **Attachments**: Image gallery, document viewer
6. **Workflow Timeline**: Status history with timestamps
7. **Negotiation Tables**: Deal tracking information

**Interactive Features**:
- Google Maps integration with property location
- Image gallery with lightbox view
- Document preview and download
- Status update controls (role-based)
- Edit property information (permission-based)

### 3.3 Workflow Management System

#### 3.3.1 8-Stage Workflow (FR-003-A)
**Specification**: Structured property acquisition workflow

**Workflow Stages**:
1. **PROPERTY_SOURCING**: Initial property submission
2. **PROPERTY_STUDY**: Analysis and feasibility assessment
3. **PBY_PREPARATION**: Property Business Yield preparation
4. **COUNCIL_APPROVAL**: Decision-making approval process
5. **NEGOTIATION**: Terms and price negotiation
6. **DUE_DILIGENCE**: Legal and financial verification
7. **CONTRACT_SIGNING**: Legal documentation execution
8. **TAKEOVER**: Property acquisition completion

**Stage Transitions**:
- Sequential progression with backward movement allowed
- Role-based transition permissions
- Required documentation for stage advancement
- Automated notifications on status changes

#### 3.3.2 Workflow History Tracking (FR-003-B)
**Specification**: Complete audit trail of all workflow changes

**Tracked Information**:
- Previous status and new status
- User who made the change
- Timestamp of change
- Notes/comments for the change
- Attached documents for the transition

**Business Rules**:
- All status changes must be logged
- History cannot be deleted or modified
- Only authorized users can make status changes
- Comments required for certain critical transitions

### 3.4 Duplicate Detection System

#### 3.4.1 Automatic Duplicate Detection (FR-004-A)
**Specification**: Multi-algorithm duplicate detection system

**Detection Methods**:
1. **Exact Title Number Match**: 100% match on title numbers
2. **Fuzzy Address Matching**: Levenshtein distance algorithm (threshold: 0.8)
3. **Geographic Proximity**: Coordinate-based distance calculation (threshold: 100m)
4. **Combined Score**: Weighted algorithm considering all factors

**Detection Triggers**:
- On property submission (real-time)
- Manual duplicate check requests
- Batch processing for existing properties
- API-based checks for external systems

**Detection Results**:
- Duplicate probability score (0-100%)
- Matching criteria explanation
- Side-by-side comparison interface
- Resolution recommendations

#### 3.4.2 Duplicate Resolution (FR-004-B)
**Specification**: Tools for managing detected duplicates

**Resolution Options**:
1. **Mark as Duplicate**: Flag property as duplicate
2. **Merge Properties**: Combine property information
3. **Mark as Different**: Override duplicate detection
4. **Request Review**: Escalate to BDD team

**Resolution Workflow**:
- BDD users can resolve duplicates
- Agents/Brokers can request review
- All resolutions logged in audit trail
- Notification system for affected users

### 3.5 Google Maps Integration

#### 3.5.1 Location Visualization (FR-005-A)
**Specification**: Interactive mapping capabilities

**Map Features**:
- Property location pinning with custom markers
- Satellite and street view options
- Zoom controls and navigation
- Property information popup windows
- Multiple property display on single map

**Address Integration**:
- Automatic geocoding of addresses
- Philippines address validation
- Coordinate-based navigation links
- Location search with autocomplete

#### 3.5.2 Facility Highlighting (FR-005-B)
**Specification**: Points of interest around properties

**Facility Types**:
- Schools (primary, secondary, universities)
- Hospitals and medical centers
- Transportation hubs (MRT, LRT, bus stations)
- Shopping centers and malls
- Government offices
- Banks and financial institutions

**Display Options**:
- Facility icons on map
- Distance calculations
- Filter by facility type
- Detailed facility information

#### 3.5.3 KMZ File Viewer (FR-005-C)
**Specification**: Support for KMZ file visualization

**Functionality**:
- KMZ file upload and parsing
- Overlay display on Google Maps
- Layer management controls
- Export capabilities

---

## 4. User Interface Specifications

### 4.1 Design System

#### 4.1.1 Design Principles
- **Consistency**: Uniform design language across all interfaces
- **Accessibility**: WCAG 2.1 AA compliance
- **Responsiveness**: Mobile-first design approach
- **Performance**: Optimized loading and interaction times

#### 4.1.2 Component Library
- **Base Components**: Radix UI primitives
- **Custom Components**: BDD-specific business components
- **Styling**: Tailwind CSS utility classes
- **Icons**: Lucide React icon library

#### 4.1.3 Color Scheme
```css
:root {
  --primary: #2563eb;      /* Blue 600 */
  --primary-foreground: #ffffff;
  --secondary: #f1f5f9;    /* Slate 100 */
  --secondary-foreground: #0f172a; /* Slate 900 */
  --accent: #10b981;       /* Emerald 500 */
  --destructive: #ef4444;  /* Red 500 */
  --warning: #f59e0b;      /* Amber 500 */
}
```

### 4.2 Layout Structure

#### 4.2.1 Dashboard Layout
```
┌─────────────────────────────────────────────────────────┐
│                    Header Navigation                     │
├─────────────┬───────────────────────────────────────────┤
│             │                                           │
│   Sidebar   │              Main Content                 │
│ Navigation  │                                           │
│             │                                           │
│             │                                           │
├─────────────┴───────────────────────────────────────────┤
│                      Footer                             │
└─────────────────────────────────────────────────────────┘
```

#### 4.2.2 Navigation Structure
**Primary Navigation (Sidebar)**:
- Dashboard
- Submit Property
- My Properties (Agents/Brokers)
- All Properties (BDD Users)
- Duplicate Checker (BDD Users)
- Location Search
- Profile Settings
- Admin Panel (Admins only)

**Secondary Navigation (Header)**:
- User profile dropdown
- Notifications
- Settings
- Logout

### 4.3 Page Specifications

#### 4.3.1 Dashboard Page
**Layout**: Grid-based dashboard with key metrics and quick actions

**Components**:
- Statistics cards (total properties, pending reviews, etc.)
- Recent activity timeline
- Quick action buttons
- Property status distribution chart
- Recent submissions table

**Role-based Content**:
- **Admin**: System-wide statistics and user management
- **BDD User**: All properties and workflow metrics
- **Broker/Agent**: Personal property metrics and submissions

#### 4.3.2 Property Submission Form
**Layout**: Multi-step wizard with progress indicator

**Form Sections**:
1. Basic Information (property name, type, description)
2. Location Details (address selection, coordinates)
3. Property Specifications (area, zoning, title)
4. Financial Information (price, terms)
5. File Attachments (documents, images)
6. Review and Submit

**Validation**:
- Real-time field validation
- Cross-field validation rules
- File type and size validation
- Duplicate detection on submission

#### 4.3.3 Property List Pages
**Layout**: Responsive table/grid view with filtering sidebar

**Table Columns**:
- Property name and type
- Location (address)
- Status (with color coding)
- Price and currency
- Submitted date
- Actions (view, edit, delete)

**Filtering Options**:
- Property type
- Status
- Price range
- Location
- Date range
- Submitted by (BDD users only)

---

## 5. Data Model Specifications

### 5.1 Entity Relationship Diagram

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    User     │    │    Property     │    │ PropertyAttach  │
├─────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)     │◄─┐ │ id (PK)         │◄───│ id (PK)         │
│ email       │  └─│ submitted_by_id │    │ property_id (FK)│
│ password    │  ┌─│ reviewer_id     │    │ filename        │
│ first_name  │◄─┘ │ name            │    │ cloudinary_url  │
│ last_name   │    │ address         │    │ file_size       │
│ role        │    │ latitude        │    │ mime_type       │
│ company     │    │ longitude       │    │ uploaded_at     │
│ is_active   │    │ lot_area        │    └─────────────────┘
│ created_at  │    │ property_type   │
└─────────────┘    │ price           │    ┌─────────────────┐
                   │ currency        │    │ WorkflowHistory │
                   │ status          │    ├─────────────────┤
                   │ title_number    │◄───│ id (PK)         │
                   │ created_at      │    │ property_id (FK)│
                   └─────────────────┘    │ from_status     │
                                          │ to_status       │
                                          │ changed_by_id   │
                                          │ notes           │
                                          │ created_at      │
                                          └─────────────────┘
```

### 5.2 Table Specifications

#### 5.2.1 User Table
```sql
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    email VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(1024) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    first_name VARCHAR(50) NOT NULL,
    middle_name VARCHAR(50),
    last_name VARCHAR(50) NOT NULL,
    role user_role NOT NULL DEFAULT 'AGENT',
    company VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE user_role AS ENUM ('ADMIN', 'BDD_USER', 'BROKER', 'AGENT');
```

#### 5.2.2 Property Table
```sql
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(500) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    street VARCHAR(200),
    barangay_name VARCHAR(100),
    city_name VARCHAR(100),
    zip_code VARCHAR(10),
    region_name VARCHAR(100),
    lot_area FLOAT NOT NULL,
    property_type property_type NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'PHP',
    zoning_classification VARCHAR(100) NOT NULL,
    title_number VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    status property_status DEFAULT 'PROPERTY_SOURCING',
    transaction_status transaction_status DEFAULT 'S',
    submitted_by_id INTEGER REFERENCES "user"(id),
    reviewer_id INTEGER REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE property_type AS ENUM ('RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL', 'AGRICULTURAL', 'MIXED_USE');
CREATE TYPE property_status AS ENUM ('PROPERTY_SOURCING', 'PROPERTY_STUDY', 'PBY_PREPARATION', 'COUNCIL_APPROVAL', 'NEGOTIATION', 'DUE_DILIGENCE', 'CONTRACT_SIGNING', 'TAKEOVER');
CREATE TYPE transaction_status AS ENUM ('S', 'R', 'L');
```

#### 5.2.3 Property Attachments Table
```sql
CREATE TABLE property_attachments (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    cloudinary_public_id VARCHAR(255) UNIQUE NOT NULL,
    cloudinary_url VARCHAR(500) NOT NULL,
    cloudinary_secure_url VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    width INTEGER,
    height INTEGER,
    uploaded_by_id INTEGER REFERENCES "user"(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.2.4 Workflow History Table
```sql
CREATE TABLE workflow_history (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE,
    from_status property_status,
    to_status property_status NOT NULL,
    changed_by_id INTEGER REFERENCES "user"(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 Data Validation Rules

#### 5.3.1 Business Rules
- Email addresses must be unique across all users
- Title numbers must be unique across all properties
- Property prices must be positive numbers
- Lot areas must be positive numbers
- Phone numbers must follow international format
- Workflow transitions must follow defined state machine

#### 5.3.2 Data Integrity
- Foreign key constraints enforced
- Cascade deletes for dependent records
- Audit trail preservation (no deletion of history)
- Automatic timestamp updates on record changes

---

## 6. API Specifications

### 6.1 API Architecture

#### 6.1.1 RESTful Design
- **Base URL**: `https://api.bddtracker.com/api/v1`
- **Authentication**: JWT Bearer tokens
- **Content Type**: `application/json`
- **Response Format**: JSON with consistent structure

#### 6.1.2 Standard Response Format
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2025-09-25T10:30:00Z",
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```

#### 6.1.3 Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "message": "Email address is required"
    }
  },
  "timestamp": "2025-09-25T10:30:00Z"
}
```

### 6.2 Authentication Endpoints

#### 6.2.1 User Registration
```
POST /auth/register
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "middle_name": "Michael",
  "last_name": "Doe",
  "company": "ABC Realty",
  "phone": "+639123456789",
  "role": "AGENT"
}

Response (201):
{
  "success": true,
  "data": {
    "id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "AGENT",
    "is_active": false,
    "is_verified": false
  },
  "message": "Account created successfully. Awaiting approval."
}
```

#### 6.2.2 User Login
```
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

Request:
username=user@example.com&password=SecurePassword123!

Response (200):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 6.3 Property Management Endpoints

#### 6.3.1 List Properties
```
GET /properties?skip=0&limit=20&status=PROPERTY_SOURCING&property_type=RESIDENTIAL
Authorization: Bearer {jwt_token}

Response (200):
{
  "success": true,
  "data": {
    "properties": [
      {
        "id": 1,
        "name": "Sample Property",
        "address": "123 Sample St, Manila",
        "property_type": "RESIDENTIAL",
        "status": "PROPERTY_SOURCING",
        "price": 5000000.00,
        "currency": "PHP",
        "lot_area": 200.0,
        "submitted_by": {
          "id": 5,
          "first_name": "John",
          "last_name": "Doe"
        },
        "created_at": "2025-09-25T10:30:00Z"
      }
    ]
  },
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 150
  }
}
```

#### 6.3.2 Create Property
```
POST /properties
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request:
{
  "name": "New Property",
  "address": "456 New St, Quezon City",
  "latitude": 14.6760,
  "longitude": 121.0437,
  "street": "456 New St",
  "barangay_name": "Barangay 123",
  "city_name": "Quezon City",
  "zip_code": "1100",
  "region_name": "National Capital Region",
  "lot_area": 300.0,
  "property_type": "RESIDENTIAL",
  "price": 8000000.00,
  "currency": "PHP",
  "zoning_classification": "R-1",
  "title_number": "TCT-123456",
  "description": "Beautiful residential property",
  "transaction_status": "S"
}

Response (201):
{
  "success": true,
  "data": {
    "id": 151,
    "name": "New Property",
    "status": "PROPERTY_SOURCING",
    "submitted_by_id": 5,
    "created_at": "2025-09-25T10:30:00Z"
  },
  "message": "Property created successfully"
}
```

#### 6.3.3 Update Property Status
```
PATCH /properties/{property_id}/status
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request:
{
  "status": "PROPERTY_STUDY",
  "notes": "Moving to property study phase after initial review"
}

Response (200):
{
  "success": true,
  "data": {
    "id": 151,
    "status": "PROPERTY_STUDY",
    "updated_at": "2025-09-25T10:35:00Z"
  },
  "message": "Property status updated successfully"
}
```

### 6.4 File Upload Endpoints

#### 6.4.1 Upload Property Attachment
```
POST /properties/{property_id}/attachments
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

Request:
file: [binary file data]

Response (201):
{
  "success": true,
  "data": {
    "id": 45,
    "filename": "property_image_1.jpg",
    "original_filename": "house_front.jpg",
    "cloudinary_url": "https://res.cloudinary.com/...",
    "file_size": 2048576,
    "mime_type": "image/jpeg",
    "uploaded_at": "2025-09-25T10:40:00Z"
  },
  "message": "File uploaded successfully"
}
```

### 6.5 Duplicate Detection Endpoints

#### 6.5.1 Check for Duplicates
```
POST /duplicates/check
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request:
{
  "title_number": "TCT-123456",
  "address": "123 Sample St, Manila",
  "latitude": 14.6760,
  "longitude": 121.0437,
  "threshold": 0.8
}

Response (200):
{
  "success": true,
  "data": {
    "duplicates": [
      {
        "property_id": 45,
        "property_name": "Similar Property",
        "match_score": 0.85,
        "match_reasons": [
          "Title number exact match",
          "Address similarity: 90%"
        ],
        "comparison_data": {
          "title_number": "TCT-123456",
          "address": "123 Sample Street, Manila City",
          "distance_meters": 25
        }
      }
    ],
    "total_matches": 1
  }
}
```

### 6.6 Admin Endpoints

#### 6.6.1 List Users (Admin Only)
```
GET /admin/users?skip=0&limit=20&role=AGENT&is_active=true
Authorization: Bearer {admin_jwt_token}

Response (200):
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 5,
        "email": "agent@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "AGENT",
        "company": "ABC Realty",
        "is_active": true,
        "is_verified": true,
        "created_at": "2025-09-20T08:00:00Z"
      }
    ]
  },
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 45
  }
}
```

---

## 7. Security Specifications

### 7.1 Authentication Security

#### 7.1.1 Password Requirements
- Minimum 8 characters
- Must contain uppercase and lowercase letters
- Must contain at least one number
- Must contain at least one special character
- Cannot be common passwords (dictionary check)
- Cannot be previously used passwords (last 5)

#### 7.1.2 JWT Token Security
- HS256 algorithm for token signing
- 24-hour token expiration
- Secure token storage (httpOnly cookies for web)
- Token refresh mechanism
- Automatic logout on token expiration

#### 7.1.3 Account Security
- Account lockout after 5 failed login attempts
- Lockout duration: 15 minutes
- Email verification required for new accounts
- Password reset via secure email tokens
- Two-factor authentication (future enhancement)

### 7.2 Authorization Security

#### 7.2.1 Role-Based Access Control
- Hierarchical role system
- Resource-level permissions
- API endpoint protection
- UI component-level access control
- Audit logging of all access attempts

#### 7.2.2 Data Access Controls
- Users can only access their own data (except BDD users)
- Property access based on ownership and role
- File access restricted to authorized users
- Administrative functions require ADMIN role
- Sensitive operations require additional verification

### 7.3 Data Security

#### 7.3.1 Data Encryption
- HTTPS/TLS 1.3 for all communications
- Database connection encryption
- File storage encryption at rest
- Sensitive data field encryption
- API payload encryption for sensitive data

#### 7.3.2 Input Validation
- Server-side validation for all inputs
- SQL injection prevention
- XSS protection
- File upload security scanning
- Rate limiting on API endpoints

### 7.4 Infrastructure Security

#### 7.4.1 Network Security
- VPC with private subnets
- Web Application Firewall (WAF)
- DDoS protection
- IP whitelisting for admin functions
- Regular security monitoring

#### 7.4.2 Database Security
- Database user with minimal privileges
- Regular database backups
- Backup encryption
- Access logging and monitoring
- Connection pooling security

---

## 8. Integration Specifications

### 8.1 Google Maps Integration

#### 8.1.1 Maps JavaScript API
```javascript
// Google Maps initialization
const initializeMap = (center, zoom = 13) => {
  const map = new google.maps.Map(document.getElementById("map"), {
    zoom: zoom,
    center: center,
    mapTypeId: "roadmap",
    gestureHandling: "cooperative",
    zoomControl: true,
    mapTypeControl: true,
    scaleControl: true,
    streetViewControl: true,
    rotateControl: true,
    fullscreenControl: true
  });
  
  return map;
};

// Property marker with info window
const addPropertyMarker = (map, property) => {
  const marker = new google.maps.Marker({
    position: { lat: property.latitude, lng: property.longitude },
    map: map,
    title: property.name,
    animation: google.maps.Animation.DROP
  });

  const infoWindow = new google.maps.InfoWindow({
    content: `
      <div class="property-info">
        <h3>${property.name}</h3>
        <p><strong>Address:</strong> ${property.address}</p>
        <p><strong>Type:</strong> ${property.property_type}</p>
        <p><strong>Price:</strong> ${property.price.toLocaleString()} ${property.currency}</p>
        <p><strong>Lot Area:</strong> ${property.lot_area} sqm</p>
      </div>
    `
  });

  marker.addListener("click", () => {
    infoWindow.open(map, marker);
  });

  return marker;
};
```

#### 8.1.2 Geocoding Integration
```javascript
// Address to coordinates conversion
const geocodeAddress = async (address) => {
  const geocoder = new google.maps.Geocoder();
  
  return new Promise((resolve, reject) => {
    geocoder.geocode({ address: address }, (results, status) => {
      if (status === "OK" && results[0]) {
        const location = results[0].geometry.location;
        resolve({
          latitude: location.lat(),
          longitude: location.lng(),
          formatted_address: results[0].formatted_address
        });
      } else {
        reject(new Error(`Geocoding failed: ${status}`));
      }
    });
  });
};

// Reverse geocoding (coordinates to address)
const reverseGeocode = async (latitude, longitude) => {
  const geocoder = new google.maps.Geocoder();
  const latlng = { lat: latitude, lng: longitude };
  
  return new Promise((resolve, reject) => {
    geocoder.geocode({ location: latlng }, (results, status) => {
      if (status === "OK" && results[0]) {
        resolve({
          formatted_address: results[0].formatted_address,
          address_components: results[0].address_components
        });
      } else {
        reject(new Error(`Reverse geocoding failed: ${status}`));
      }
    });
  });
};
```

#### 8.1.3 Places API Integration
```javascript
// Places autocomplete for address input
const initializeAutocomplete = (inputElement) => {
  const autocomplete = new google.maps.places.Autocomplete(inputElement, {
    types: ['address'],
    componentRestrictions: { country: 'ph' }, // Philippines only
    fields: ['place_id', 'geometry', 'formatted_address', 'address_components']
  });

  autocomplete.addListener('place_changed', () => {
    const place = autocomplete.getPlace();
    
    if (place.geometry) {
      const addressComponents = parseAddressComponents(place.address_components);
      
      // Update form fields with parsed address components
      updateAddressFields(addressComponents);
      
      // Update coordinates
      updateCoordinates(
        place.geometry.location.lat(),
        place.geometry.location.lng()
      );
    }
  });

  return autocomplete;
};

// Parse Google Places address components for Philippines
const parseAddressComponents = (components) => {
  const addressMap = {};
  
  components.forEach(component => {
    const types = component.types;
    
    if (types.includes('street_number')) {
      addressMap.street_number = component.long_name;
    } else if (types.includes('route')) {
      addressMap.route = component.long_name;
    } else if (types.includes('sublocality_level_1') || types.includes('barangay')) {
      addressMap.barangay = component.long_name;
    } else if (types.includes('locality') || types.includes('administrative_area_level_2')) {
      addressMap.city = component.long_name;
    } else if (types.includes('administrative_area_level_1')) {
      addressMap.province = component.long_name;
    } else if (types.includes('postal_code')) {
      addressMap.postal_code = component.long_name;
    }
  });

  return addressMap;
};
```

### 8.2 Philippines Address API Integration

#### 8.2.1 Address Data Structure
```json
{
  "regions": [
    {
      "region_code": "15",
      "region_name": "National Capital Region (NCR)"
    }
  ],
  "provinces": [
    {
      "province_code": "1339",
      "province_name": "Metro Manila",
      "region_code": "15"
    }
  ],
  "cities": [
    {
      "city_code": "133901",
      "city_name": "Manila",
      "province_code": "1339"
    }
  ],
  "barangays": [
    {
      "barangay_code": "13390101",
      "barangay_name": "Barangay 1",
      "city_code": "133901"
    }
  ]
}
```

#### 8.2.2 Cascading Address Selection
```javascript
// React component for cascading address selection
const PhilippinesAddressSelector = ({ onAddressChange }) => {
  const [regions, setRegions] = useState([]);
  const [provinces, setProvinces] = useState([]);
  const [cities, setCities] = useState([]);
  const [barangays, setBarangays] = useState([]);
  
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedProvince, setSelectedProvince] = useState('');
  const [selectedCity, setSelectedCity] = useState('');
  const [selectedBarangay, setSelectedBarangay] = useState('');

  // Load regions on component mount
  useEffect(() => {
    fetchRegions().then(setRegions);
  }, []);

  // Load provinces when region changes
  useEffect(() => {
    if (selectedRegion) {
      fetchProvinces(selectedRegion).then(setProvinces);
      setSelectedProvince('');
      setCities([]);
      setBarangays([]);
    }
  }, [selectedRegion]);

  // Load cities when province changes
  useEffect(() => {
    if (selectedProvince) {
      fetchCities(selectedProvince).then(setCities);
      setSelectedCity('');
      setBarangays([]);
    }
  }, [selectedProvince]);

  // Load barangays when city changes
  useEffect(() => {
    if (selectedCity) {
      fetchBarangays(selectedCity).then(setBarangays);
      setSelectedBarangay('');
    }
  }, [selectedCity]);

  // API calls
  const fetchRegions = async () => {
    const response = await fetch('/api/v1/address/regions');
    return response.json();
  };

  const fetchProvinces = async (regionCode) => {
    const response = await fetch(`/api/v1/address/provinces/${regionCode}`);
    return response.json();
  };

  const fetchCities = async (provinceCode) => {
    const response = await fetch(`/api/v1/address/cities/${provinceCode}`);
    return response.json();
  };

  const fetchBarangays = async (cityCode) => {
    const response = await fetch(`/api/v1/address/barangays/${cityCode}`);
    return response.json();
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Select value={selectedRegion} onValueChange={setSelectedRegion}>
        <SelectTrigger>
          <SelectValue placeholder="Select Region" />
        </SelectTrigger>
        <SelectContent>
          {regions.map(region => (
            <SelectItem key={region.region_code} value={region.region_code}>
              {region.region_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedProvince} onValueChange={setSelectedProvince} disabled={!selectedRegion}>
        <SelectTrigger>
          <SelectValue placeholder="Select Province" />
        </SelectTrigger>
        <SelectContent>
          {provinces.map(province => (
            <SelectItem key={province.province_code} value={province.province_code}>
              {province.province_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedCity} onValueChange={setSelectedCity} disabled={!selectedProvince}>
        <SelectTrigger>
          <SelectValue placeholder="Select City/Municipality" />
        </SelectTrigger>
        <SelectContent>
          {cities.map(city => (
            <SelectItem key={city.city_code} value={city.city_code}>
              {city.city_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedBarangay} onValueChange={setSelectedBarangay} disabled={!selectedCity}>
        <SelectTrigger>
          <SelectValue placeholder="Select Barangay" />
        </SelectTrigger>
        <SelectContent>
          {barangays.map(barangay => (
            <SelectItem key={barangay.barangay_code} value={barangay.barangay_code}>
              {barangay.barangay_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
```

### 8.3 Cloudinary Integration

#### 8.3.1 Image Upload Configuration
```python
# Python backend Cloudinary configuration
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

cloudinary.config(
    cloud_name="your_cloud_name",
    api_key="your_api_key",
    api_secret="your_api_secret",
    secure=True
)

# Upload image with optimization
async def upload_property_image(file_data: bytes, filename: str, property_id: int) -> dict:
    """Upload property image to Cloudinary with optimization"""
    
    upload_result = cloudinary.uploader.upload(
        file_data,
        folder=f"properties/{property_id}",
        public_id=f"{property_id}_{filename}",
        transformation=[
            {"quality": "auto:good"},
            {"fetch_format": "auto"},
            {"width": 1200, "height": 800, "crop": "limit"}
        ],
        eager=[
            {"width": 300, "height": 200, "crop": "thumb", "quality": "auto:good"},
            {"width": 600, "height": 400, "crop": "fit", "quality": "auto:good"}
        ]
    )
    
    return {
        "public_id": upload_result["public_id"],
        "secure_url": upload_result["secure_url"],
        "width": upload_result.get("width"),
        "height": upload_result.get("height"),
        "format": upload_result["format"],
        "bytes": upload_result["bytes"],
        "eager": upload_result.get("eager", [])
    }

# Generate responsive image URLs
def get_responsive_image_urls(public_id: str) -> dict:
    """Generate responsive image URLs for different screen sizes"""
    
    base_url, options = cloudinary_url(public_id)
    
    return {
        "thumbnail": cloudinary_url(public_id, width=300, height=200, crop="thumb")[0],
        "medium": cloudinary_url(public_id, width=600, height=400, crop="fit")[0],
        "large": cloudinary_url(public_id, width=1200, height=800, crop="limit")[0],
        "original": base_url
    }
```

#### 8.3.2 Frontend Image Display
```javascript
// React component for responsive image display
const PropertyImage = ({ publicId, alt, className }) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const generateCloudinaryUrl = (publicId, transformations) => {
    const baseUrl = `https://res.cloudinary.com/${process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME}/image/upload`;
    const transformString = transformations.join(',');
    return `${baseUrl}/${transformString}/${publicId}`;
  };

  const imageUrl = generateCloudinaryUrl(publicId, [
    'f_auto', 'q_auto:good', 'w_600', 'h_400', 'c_fit'
  ]);

  const thumbnailUrl = generateCloudinaryUrl(publicId, [
    'f_auto', 'q_auto:good', 'w_300', 'h_200', 'c_thumb'
  ]);

  return (
    <div className={`relative overflow-hidden ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center">
          <div className="text-gray-400">Loading...</div>
        </div>
      )}
      
      {!imageError ? (
        <img
          src={imageUrl}
          alt={alt}
          className="w-full h-full object-cover transition-opacity duration-300"
          style={{ opacity: isLoading ? 0 : 1 }}
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setImageError(true);
            setIsLoading(false);
          }}
        />
      ) : (
        <div className="w-full h-full bg-gray-200 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
            </svg>
            <p className="text-sm">Image not available</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Image gallery component
const PropertyImageGallery = ({ images }) => {
  const [selectedImage, setSelectedImage] = useState(null);

  return (
    <div className="space-y-4">
      {/* Main image display */}
      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
        {images.length > 0 ? (
          <PropertyImage
            publicId={images[0].cloudinary_public_id}
            alt={images[0].original_filename}
            className="w-full h-full"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            No images available
          </div>
        )}
      </div>

      {/* Thumbnail grid */}
      {images.length > 1 && (
        <div className="grid grid-cols-4 gap-2">
          {images.slice(1, 5).map((image, index) => (
            <button
              key={image.id}
              className="aspect-square bg-gray-100 rounded overflow-hidden hover:opacity-75 transition-opacity"
              onClick={() => setSelectedImage(image)}
            >
              <PropertyImage
                publicId={image.cloudinary_public_id}
                alt={image.original_filename}
                className="w-full h-full"
              />
            </button>
          ))}
        </div>
      )}

      {/* Lightbox modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-full p-4">
            <button
              className="absolute top-4 right-4 text-white hover:text-gray-300"
              onClick={() => setSelectedImage(null)}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
            <PropertyImage
              publicId={selectedImage.cloudinary_public_id}
              alt={selectedImage.original_filename}
              className="max-w-full max-h-full"
            />
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 9. Testing Specifications

### 9.1 Testing Strategy

#### 9.1.1 Testing Pyramid
```
                    ┌─────────────────┐
                    │   E2E Tests     │
                    │   (Playwright)  │
                    └─────────────────┘
                ┌─────────────────────────┐
                │   Integration Tests     │
                │   (API Testing)         │
                └─────────────────────────┘
            ┌─────────────────────────────────┐
            │        Unit Tests               │
            │   (Jest/Vitest + pytest)       │
            └─────────────────────────────────┘
```

#### 9.1.2 Test Coverage Requirements
- **Unit Tests**: 80% code coverage minimum
- **Integration Tests**: All API endpoints covered
- **E2E Tests**: Critical user journeys covered
- **Performance Tests**: Load testing for key scenarios

### 9.2 Frontend Testing

#### 9.2.1 Playwright E2E Tests
```typescript
// tests/property-submission.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Property Submission Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as agent user
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'agent@test.com');
    await page.fill('[data-testid="password"]', 'testpassword');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should complete property submission successfully', async ({ page }) => {
    // Navigate to property submission
    await page.click('[data-testid="submit-property-link"]');
    await expect(page).toHaveURL('/submit-property');

    // Step 1: Basic Information
    await page.fill('[data-testid="property-name"]', 'Test Property');
    await page.selectOption('[data-testid="property-type"]', 'RESIDENTIAL');
    await page.fill('[data-testid="description"]', 'Test property description');
    await page.click('[data-testid="next-step"]');

    // Step 2: Location Details
    await page.fill('[data-testid="address"]', '123 Test Street, Manila');
    await page.selectOption('[data-testid="region"]', '15'); // NCR
    await page.selectOption('[data-testid="province"]', '1339'); // Metro Manila
    await page.selectOption('[data-testid="city"]', '133901'); // Manila
    await page.selectOption('[data-testid="barangay"]', '13390101'); // Barangay 1
    await page.click('[data-testid="next-step"]');

    // Step 3: Property Details
    await page.fill('[data-testid="lot-area"]', '200');
    await page.fill('[data-testid="zoning"]', 'R-1');
    await page.fill('[data-testid="title-number"]', 'TCT-TEST-001');
    await page.fill('[data-testid="price"]', '5000000');
    await page.click('[data-testid="next-step"]');

    // Step 4: Transaction Details
    await page.selectOption('[data-testid="transaction-status"]', 'S');
    await page.click('[data-testid="next-step"]');

    // Step 5: File Attachments (optional)
    await page.click('[data-testid="next-step"]');

    // Step 6: Review and Submit
    await expect(page.locator('[data-testid="property-name-review"]')).toHaveText('Test Property');
    await expect(page.locator('[data-testid="property-type-review"]')).toHaveText('RESIDENTIAL');
    
    // Submit property
    await page.click('[data-testid="submit-property"]');
    
    // Verify success
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page).toHaveURL('/my-properties');
  });

  test('should show validation errors for required fields', async ({ page }) => {
    await page.goto('/submit-property');
    
    // Try to proceed without filling required fields
    await page.click('[data-testid="next-step"]');
    
    // Verify validation errors
    await expect(page.locator('[data-testid="property-name-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="property-type-error"]')).toBeVisible();
  });

  test('should detect duplicate properties', async ({ page }) => {
    await page.goto('/submit-property');
    
    // Fill form with existing property data
    await page.fill('[data-testid="property-name"]', 'Existing Property');
    await page.selectOption('[data-testid="property-type"]', 'RESIDENTIAL');
    await page.fill('[data-testid="title-number"]', 'TCT-EXISTING-001');
    
    // Submit and expect duplicate warning
    await page.click('[data-testid="submit-property"]');
    await expect(page.locator('[data-testid="duplicate-warning"]')).toBeVisible();
    await expect(page.locator('[data-testid="duplicate-property-list"]')).toBeVisible();
  });
});
```

#### 9.2.2 Component Unit Tests
```typescript
// components/__tests__/PropertyForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PropertyForm } from '../PropertyForm';

describe('PropertyForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('renders all form fields', () => {
    render(<PropertyForm onSubmit={mockOnSubmit} />);
    
    expect(screen.getByLabelText(/property name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/property type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/lot area/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/price/i)).toBeInTheDocument();
  });

  test('validates required fields', async () => {
    render(<PropertyForm onSubmit={mockOnSubmit} />);
    
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/property name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/property type is required/i)).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('submits form with valid data', async () => {
    render(<PropertyForm onSubmit={mockOnSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/property name/i), {
      target: { value: 'Test Property' }
    });
    fireEvent.change(screen.getByLabelText(/property type/i), {
      target: { value: 'RESIDENTIAL' }
    });
    fireEvent.change(screen.getByLabelText(/address/i), {
      target: { value: '123 Test St, Manila' }
    });
    fireEvent.change(screen.getByLabelText(/lot area/i), {
      target: { value: '200' }
    });
    fireEvent.change(screen.getByLabelText(/price/i), {
      target: { value: '5000000' }
    });
    
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Test Property',
        property_type: 'RESIDENTIAL',
        address: '123 Test St, Manila',
        lot_area: 200,
        price: 5000000,
        currency: 'PHP'
      });
    });
  });
});
```

### 9.3 Backend Testing

#### 9.3.1 API Integration Tests
```python
# tests/test_properties.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_property_success():
    """Test successful property creation"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login first
        login_response = await ac.post("/api/v1/auth/jwt/login", data={
            "username": "agent@test.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create property
        property_data = {
            "name": "Test Property",
            "address": "123 Test St, Manila",
            "lot_area": 200.0,
            "property_type": "RESIDENTIAL",
            "price": 5000000.00,
            "currency": "PHP",
            "zoning_classification": "R-1",
            "title_number": "TCT-TEST-001",
            "transaction_status": "S"
        }
        
        response = await ac.post("/api/v1/properties/", 
                                json=property_data, 
                                headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] == True
        assert data["data"]["name"] == "Test Property"
        assert data["data"]["status"] == "PROPERTY_SOURCING"

@pytest.mark.asyncio
async def test_create_property_duplicate_title():
    """Test property creation with duplicate title number"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login
        login_response = await ac.post("/api/v1/auth/jwt/login", data={
            "username": "agent@test.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create first property
        property_data = {
            "name": "Test Property 1",
            "title_number": "TCT-DUPLICATE-001",
            # ... other fields
        }
        
        await ac.post("/api/v1/properties/", json=property_data, headers=headers)
        
        # Try to create second property with same title number
        property_data["name"] = "Test Property 2"
        
        response = await ac.post("/api/v1/properties/", 
                                json=property_data, 
                                headers=headers)
        
        assert response.status_code == 400
        assert "title number already exists" in response.json()["error"]["message"].lower()

@pytest.mark.asyncio
async def test_list_properties_pagination():
    """Test property list with pagination"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login as BDD user
        login_response = await ac.post("/api/v1/auth/jwt/login", data={
            "username": "bdd@test.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get properties with pagination
        response = await ac.get("/api/v1/properties/?skip=0&limit=10", 
                               headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "pagination" in data
        assert len(data["data"]["properties"]) <= 10

@pytest.mark.asyncio
async def test_update_property_status():
    """Test property status update"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login as BDD user
        login_response = await ac.post("/api/v1/auth/jwt/login", data={
            "username": "bdd@test.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create property first
        property_data = {
            "name": "Test Property",
            "title_number": "TCT-STATUS-001",
            # ... other fields
        }
        
        create_response = await ac.post("/api/v1/properties/", 
                                       json=property_data, 
                                       headers=headers)
        property_id = create_response.json()["data"]["id"]
        
        # Update status
        status_update = {
            "status": "PROPERTY_STUDY",
            "notes": "Moving to study phase"
        }
        
        response = await ac.patch(f"/api/v1/properties/{property_id}/status", 
                                 json=status_update, 
                                 headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "PROPERTY_STUDY"
```

#### 9.3.2 Unit Tests for Services
```python
# tests/test_duplicate_service.py
import pytest
from app.services.duplicate import DuplicateDetectionService
from app.models.property import Property

@pytest.mark.asyncio
async def test_exact_title_match(db_session):
    """Test exact title number matching"""
    service = DuplicateDetectionService(db_session)
    
    # Create existing property
    existing_property = Property(
        name="Existing Property",
        title_number="TCT-123456",
        address="123 Test St, Manila",
        lot_area=200.0,
        property_type="RESIDENTIAL",
        price=5000000.00
    )
    db_session.add(existing_property)
    await db_session.commit()
    
    # Test duplicate detection
    test_property_data = {
        "title_number": "TCT-123456",
        "address": "456 Different St, Quezon City"
    }
    
    duplicates = await service.find_duplicates(test_property_data)
    
    assert len(duplicates) == 1
    assert duplicates[0]["property_id"] == existing_property.id
    assert duplicates[0]["match_score"] >= 0.9
    assert "title number exact match" in duplicates[0]["match_reasons"]

@pytest.mark.asyncio
async def test_fuzzy_address_matching(db_session):
    """Test fuzzy address matching"""
    service = DuplicateDetectionService(db_session)
    
    # Create existing property
    existing_property = Property(
        name="Existing Property",
        title_number="TCT-111111",
        address="123 Main Street, Manila City",
        lot_area=200.0,
        property_type="RESIDENTIAL",
        price=5000000.00
    )
    db_session.add(existing_property)
    await db_session.commit()
    
    # Test with similar address
    test_property_data = {
        "title_number": "TCT-222222",
        "address": "123 Main St, Manila"
    }
    
    duplicates = await service.find_duplicates(test_property_data, threshold=0.7)
    
    assert len(duplicates) >= 1
    match = next(d for d in duplicates if d["property_id"] == existing_property.id)
    assert match["match_score"] >= 0.7
    assert "address similarity" in match["match_reasons"][0]

@pytest.mark.asyncio
async def test_geographic_proximity(db_session):
    """Test geographic proximity detection"""
    service = DuplicateDetectionService(db_session)
    
    # Create existing property with coordinates
    existing_property = Property(
        name="Existing Property",
        title_number="TCT-333333",
        address="123 Test St, Manila",
        latitude=14.5995,
        longitude=120.9842,
        lot_area=200.0,
        property_type="RESIDENTIAL",
        price=5000000.00
    )
    db_session.add(existing_property)
    await db_session.commit()
    
    # Test with nearby coordinates (within 100m)
    test_property_data = {
        "title_number": "TCT-444444",
        "address": "456 Different St, Manila",
        "latitude": 14.5996,  # Very close
        "longitude": 120.9843
    }
    
    duplicates = await service.find_duplicates(test_property_data)
    
    assert len(duplicates) >= 1
    match = next(d for d in duplicates if d["property_id"] == existing_property.id)
    assert match["match_score"] >= 0.6
    assert "geographic proximity" in match["match_reasons"][0]
```

### 9.4 Performance Testing

#### 9.4.1 Load Testing with Playwright
```typescript
// tests/load/property-list-load.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Property List Load Testing', () => {
  test('should handle concurrent property list requests', async ({ browser }) => {
    const contexts = [];
    const pages = [];
    
    // Create 10 concurrent browser contexts
    for (let i = 0; i < 10; i++) {
      const context = await browser.newContext();
      const page = await context.newPage();
      contexts.push(context);
      pages.push(page);
    }
    
    // Login all users concurrently
    const loginPromises = pages.map(async (page, index) => {
      await page.goto('/login');
      await page.fill('[data-testid="email"]', `testuser${index}@test.com`);
      await page.fill('[data-testid="password"]', 'testpassword');
      await page.click('[data-testid="login-button"]');
      await expect(page).toHaveURL('/dashboard');
    });
    
    await Promise.all(loginPromises);
    
    // Navigate to property list concurrently
    const startTime = Date.now();
    const navigationPromises = pages.map(async (page) => {
      await page.goto('/all-properties');
      await expect(page.locator('[data-testid="property-table"]')).toBeVisible();
    });
    
    await Promise.all(navigationPromises);
    const endTime = Date.now();
    
    // Verify performance
    const totalTime = endTime - startTime;
    expect(totalTime).toBeLessThan(10000); // Should complete within 10 seconds
    
    // Cleanup
    await Promise.all(contexts.map(context => context.close()));
  });
});
```

---

## 10. Deployment & Operations

### 10.1 Deployment Architecture

#### 10.1.1 Railway Deployment Configuration
```yaml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
NODE_ENV = "production"
DATABASE_URL = "${{DATABASE_URL}}"
NEXTAUTH_SECRET = "${{NEXTAUTH_SECRET}}"
NEXTAUTH_URL = "${{NEXTAUTH_URL}}"
GOOGLE_MAPS_API_KEY = "${{GOOGLE_MAPS_API_KEY}}"
CLOUDINARY_CLOUD_NAME = "${{CLOUDINARY_CLOUD_NAME}}"
CLOUDINARY_API_KEY = "${{CLOUDINARY_API_KEY}}"
CLOUDINARY_API_SECRET = "${{CLOUDINARY_API_SECRET}}"
```

#### 10.1.2 Docker Configuration
```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM base AS build
RUN npm ci
COPY . .
RUN npm run build

FROM base AS runtime
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

```dockerfile
# Backend Dockerfile
FROM python:3.11-slim AS base
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations on startup
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
```

### 10.2 Environment Configuration

#### 10.2.1 Environment Variables
```bash
# Frontend (.env.local)
NEXTAUTH_SECRET=your-nextauth-secret-key
NEXTAUTH_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name

# Backend (.env)
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
ENVIRONMENT=production
```

### 10.3 Monitoring & Logging

#### 10.3.1 Application Monitoring
```python
# app/utils/monitoring.py
import logging
import time
from functools import wraps
from typing import Callable

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

def monitor_performance(operation_name: str):
    """Decorator to monitor API endpoint performance"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(f"Operation: {operation_name}, "
                           f"Duration: {execution_time:.2f}s, "
                           f"Status: Success")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(f"Operation: {operation_name}, "
                            f"Duration: {execution_time:.2f}s, "
                            f"Status: Error, "
                            f"Error: {str(e)}")
                
                raise
        return wrapper
    return decorator

# Usage example
@router.get("/properties/")
@monitor_performance("list_properties")
async def list_properties(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_session)
):
    # Implementation
    pass
```

#### 10.3.2 Error Tracking
```python
# app/utils/error_handler.py
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
import logging

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    
    # Log the full error details
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    
    # Return user-friendly error response
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            },
            "timestamp": "2025-09-25T10:30:00Z"
        }
    )

# Custom HTTP exception handler
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions"""
    
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    logger.warning(f"Request URL: {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            },
            "timestamp": "2025-09-25T10:30:00Z"
        }
    )
```

### 10.4 Backup & Recovery

#### 10.4.1 Database Backup Strategy
```bash
#!/bin/bash
# scripts/backup_database.sh

# Configuration
DB_NAME="bdd_property_tracker"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${DATE}.sql"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Create database backup
pg_dump ${DATABASE_URL} > ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Keep only last 30 days of backups
find ${BACKUP_DIR} -name "backup_${DB_NAME}_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

#### 10.4.2 File Backup Strategy
```python
# scripts/backup_files.py
import os
import boto3
from datetime import datetime
import logging

def backup_files_to_s3():
    """Backup local files to S3 for disaster recovery"""
    
    s3_client = boto3.client('s3')
    bucket_name = 'bdd-tracker-backups'
    
    # Backup directories
    backup_dirs = [
        '/app/uploads',
        '/app/logs'
    ]
    
    for backup_dir in backup_dirs:
        if os.path.exists(backup_dir):
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = f"backups/{datetime.now().strftime('%Y/%m/%d')}/{local_path[1:]}"
                    
                    try:
                        s3_client.upload_file(local_path, bucket_name, s3_key)
                        logging.info(f"Uploaded {local_path} to s3://{bucket_name}/{s3_key}")
                    except Exception as e:
                        logging.error(f"Failed to upload {local_path}: {str(e)}")

if __name__ == "__main__":
    backup_files_to_s3()
```

---

## 11. Maintenance & Support

### 11.1 Maintenance Procedures

#### 11.1.1 Regular Maintenance Tasks
```bash
#!/bin/bash
# scripts/maintenance.sh

echo "Starting maintenance procedures..."

# 1. Database maintenance
echo "Running database maintenance..."
psql ${DATABASE_URL} -c "VACUUM ANALYZE;"
psql ${DATABASE_URL} -c "REINDEX DATABASE bdd_property_tracker;"

# 2. Log rotation
echo "Rotating logs..."
logrotate /etc/logrotate.d/bdd-tracker

# 3. Clear temporary files
echo "Cleaning temporary files..."
find /tmp -name "bdd-*" -mtime +7 -delete

# 4. Update system packages (if needed)
echo "Checking for security updates..."
apt list --upgradable | grep -i security

# 5. Health check
echo "Running health checks..."
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:3000/api/health || echo "Frontend health check failed"

echo "Maintenance procedures completed."
```

#### 11.1.2 Performance Optimization
```sql
-- Database performance optimization queries
-- Run monthly

-- Analyze table statistics
ANALYZE properties;
ANALYZE "user";
ANALYZE property_attachments;
ANALYZE workflow_history;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
AND n_distinct > 100
AND correlation < 0.1;

-- Find slow queries
SELECT query, calls, total_time, mean_time, stddev_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;

-- Clean up old workflow history (keep 2 years)
DELETE FROM workflow_history 
WHERE created_at < NOW() - INTERVAL '2 years';

-- Update table statistics
VACUUM ANALYZE;
```

### 11.2 Troubleshooting Guide

#### 11.2.1 Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Slow Property List Loading** | Page takes >5 seconds to load | 1. Check database indexes<br>2. Optimize query filters<br>3. Implement pagination |
| **Google Maps Not Loading** | Blank map area | 1. Verify API key<br>2. Check browser console<br>3. Verify domain restrictions |
| **File Upload Failures** | Upload progress stops | 1. Check file size limits<br>2. Verify Cloudinary config<br>3. Check network connectivity |
| **Duplicate Detection Issues** | False positives/negatives | 1. Adjust similarity thresholds<br>2. Update fuzzy matching algorithm<br>3. Review address normalization |
| **Authentication Errors** | Users cannot login | 1. Check JWT secret key<br>2. Verify database connectivity<br>3. Check user account status |

#### 11.2.2 Emergency Procedures

```bash
#!/bin/bash
# scripts/emergency_procedures.sh

case "$1" in
    "database_down")
        echo "Database emergency procedure..."
        # 1. Check database status
        pg_isready -h $DB_HOST -p $DB_PORT
        
        # 2. Restart database service
        systemctl restart postgresql
        
        # 3. Verify connection
        psql $DATABASE_URL -c "SELECT 1;"
        ;;
        
    "high_cpu")
        echo "High CPU usage procedure..."
        # 1. Identify resource-heavy processes
        ps aux --sort=-%cpu | head -10
        
        # 2. Check for runaway queries
        psql $DATABASE_URL -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
        
        # 3. Kill long-running queries if necessary
        # psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE (now() - pg_stat_activity.query_start) > interval '10 minutes';"
        ;;
        
    "disk_full")
        echo "Disk space emergency procedure..."
        # 1. Check disk usage
        df -h
        
        # 2. Clean up old logs
        find /var/log -name "*.log" -mtime +30 -delete
        
        # 3. Clean up old backups
        find /backups -name "*.sql.gz" -mtime +7 -delete
        
        # 4. Clear application cache
        rm -rf /tmp/bdd-*
        ;;
esac
```

### 11.3 Support Documentation

#### 11.3.1 User Support Procedures

1. **Level 1 Support (User Issues)**
   - Password resets
   - Account activation
   - Basic navigation help
   - File upload assistance

2. **Level 2 Support (Technical Issues)**
   - Property submission problems
   - Data integrity issues
   - Performance problems
   - Integration failures

3. **Level 3 Support (System Issues)**
   - Database problems
   - Server maintenance
   - Security incidents
   - Code deployment issues

#### 11.3.2 Support Contact Information

- **Technical Support**: support@bddtracker.com
- **Emergency Contact**: +63 XXX XXX XXXX
- **Development Team**: dev@bddtracker.com
- **System Administrator**: admin@bddtracker.com

---

## 12. Conclusion

This Business Requirements Specification provides comprehensive technical and functional specifications for the BDD Property Tracker system. The document serves as the definitive guide for development, testing, deployment, and maintenance of the system.

### 12.1 Key Success Factors

1. **User-Centered Design**: Focus on intuitive user experience
2. **Robust Architecture**: Scalable and maintainable system design
3. **Security First**: Comprehensive security measures throughout
4. **Performance Optimization**: Fast and responsive user interface
5. **Comprehensive Testing**: Thorough testing at all levels
6. **Proper Documentation**: Complete technical and user documentation

### 12.2 Next Steps

1. **Development Phase**: Begin implementation according to specifications
2. **Testing Phase**: Execute comprehensive testing strategy
3. **Deployment Phase**: Deploy to production environment
4. **Training Phase**: User training and documentation
5. **Monitoring Phase**: Continuous monitoring and optimization

---

**Document Control:**
- **Version**: 1.0
- **Last Updated**: September 25, 2025
- **Next Review**: October 25, 2025
- **Owner**: Development Team
- **Approved by**: Business Development Team









