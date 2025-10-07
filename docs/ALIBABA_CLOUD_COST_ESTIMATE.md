# Alibaba Cloud & Google Maps API - Cost Estimate

## Project Overview

**BDD Property Tracker** is a comprehensive real estate property management system with:
- **Frontend**: Next.js 15 with TypeScript
- **Backend**: FastAPI (Python) with PostgreSQL
- **Features**: 
  - Property management with 8-stage workflow
  - User management (Admin, Manager, Agent, Reviewer roles)
  - File uploads (images, documents, CSV)
  - Google Maps integration (interactive maps, geocoding, places API)
  - Negotiation chronicles
  - Activity logging and notifications
  - Duplicate property detection

---

## Cost Assumptions

### Traffic & Usage Estimates (Small-Medium Business)
- **Monthly Active Users**: 50-100 users
- **Daily Active Users**: 20-30 users
- **Properties in Database**: 1,000-5,000 properties
- **Database Size**: 10-20 GB (including indexes)
- **Monthly File Uploads**: 500-1,000 files (avg 2MB each)
- **Total File Storage**: 50-100 GB growing ~2GB/month
- **Monthly Page Views**: 50,000-100,000 views
- **API Requests**: 200,000-400,000 requests/month
- **Google Maps Loads**: 5,000-10,000 map loads/month
- **Google Places API Calls**: 2,000-4,000 requests/month

---

## 1. Alibaba Cloud Database (ApsaraDB for RDS - PostgreSQL)

### Recommended Configuration
**Product**: ApsaraDB RDS for PostgreSQL  
**Tier**: General Purpose (Entry Level)

| Specification | Details |
|--------------|---------|
| Instance Type | `pg.n2.small.1` (1 vCPU, 2GB RAM) |
| Storage | 100 GB SSD |
| Backup Storage | 50 GB (7-day retention) |
| Region | Singapore / Hong Kong (closest to Philippines) |

### Monthly Cost Breakdown
```
Instance Cost:        $30.00 - $40.00/month
Storage (100GB):      $15.00 - $20.00/month
Backup Storage:       $5.00/month
Data Transfer:        $5.00/month
-------------------------------------------
TOTAL DATABASE:       $55.00 - $70.00/month
```

### Yearly Cost
```
Database Total:       $660.00 - $840.00/year
```

---

## 2. Alibaba Cloud Hosting (ECS - Elastic Compute Service)

### Recommended Configuration

#### Option A: Single Instance (Recommended for Start)
**Product**: ECS General Purpose Instance

| Specification | Details |
|--------------|---------|
| Instance Type | `ecs.t6-c1m2.large` (2 vCPU, 4GB RAM) |
| Storage | 100 GB SSD |
| Bandwidth | 5 Mbps (Pay-by-Traffic) |
| Region | Singapore / Hong Kong |

### Monthly Cost Breakdown
```
Compute Instance:     $35.00 - $50.00/month
Storage (100GB SSD):  $10.00 - $15.00/month
Bandwidth (5Mbps):    $15.00 - $25.00/month
Load Balancer:        $10.00/month (optional)
-------------------------------------------
TOTAL HOSTING:        $70.00 - $100.00/month
```

#### Option B: Dual Instance (Production + High Availability)
For running both frontend and backend separately with redundancy:

```
2x Compute Instances: $100.00 - $140.00/month
Load Balancer (SLB):  $20.00/month
Auto Scaling Setup:   $10.00/month
-------------------------------------------
TOTAL HOSTING (HA):   $130.00 - $170.00/month
```

### Yearly Cost
```
Option A (Single):    $840.00 - $1,200.00/year
Option B (HA):        $1,560.00 - $2,040.00/year
```

---

## 3. Alibaba Cloud DNS

### Product: Alibaba Cloud DNS
**Service**: DNS Standard Edition

| Feature | Details |
|---------|---------|
| DNS Queries | Up to 1 million/month |
| DNS Records | Up to 100 records |
| Subdomains | Unlimited |

### Monthly Cost
```
DNS Service:          $3.00 - $5.00/month
Domain Registration:  $10.00 - $15.00/year (domain cost)
-------------------------------------------
TOTAL DNS:            $3.00 - $5.00/month
```

### Yearly Cost
```
DNS Total:            $36.00 - $60.00/year
Domain (one-time):    $10.00 - $15.00/year
```

---

## 4. Alibaba Cloud Object Storage Service (OSS)

### Recommended Configuration
**Product**: OSS Standard Storage  
**Region**: Singapore / Hong Kong

| Feature | Details |
|---------|---------|
| Storage Capacity | 100 GB (growing 2GB/month) |
| Monthly Uploads | 1,000 files (~2GB) |
| Monthly Downloads | 5,000 file accesses (~10GB transfer) |
| CDN Integration | Optional for faster delivery |

### Monthly Cost Breakdown
```
Storage (100GB):              $2.30/month
PUT/POST Requests (10k):      $0.10/month
GET Requests (50k):           $0.40/month
Data Transfer Out (10GB):     $1.20/month
CDN (optional):               $5.00 - $10.00/month
-------------------------------------------
TOTAL STORAGE (No CDN):       $4.00/month
TOTAL STORAGE (With CDN):     $9.00 - $14.00/month
```

### Yearly Cost
```
Storage (No CDN):     $48.00/year
Storage (With CDN):   $108.00 - $168.00/year

Growth Cost (24GB/year): +$6.00/year
```

---

## 5. Google Maps API

### API Usage Breakdown

Your application uses:
1. **Maps JavaScript API** - Interactive maps
2. **Geocoding API** - Address to coordinates conversion
3. **Places API** - Location search and autocomplete

### Monthly Usage Estimates

#### Maps JavaScript API
```
Monthly Map Loads:    10,000 loads
Cost per 1,000:       $7.00
-------------------------------------------
TOTAL:                $70.00/month
```

#### Geocoding API
```
Monthly Requests:     2,000 requests
Free Tier:            First 40,000 free (with $200 credit)
Cost per 1,000:       $5.00 (after free tier)
-------------------------------------------
TOTAL:                $0.00/month (within free tier)
```

#### Places API (Autocomplete + Details)
```
Autocomplete:         2,000 requests
Place Details:        1,000 requests
Cost per 1,000:       
  - Autocomplete:     $2.83 per 1,000
  - Details:          $17.00 per 1,000
-------------------------------------------
Autocomplete:         $5.66/month
Place Details:        $17.00/month
TOTAL:                $22.66/month
```

### Google Maps Monthly Total
```
Maps JavaScript API:  $70.00/month
Geocoding API:        $0.00/month (free tier)
Places API:           $22.66/month
-------------------------------------------
TOTAL GOOGLE MAPS:    $92.66/month
```

**Note**: Google provides $200 free credit monthly, which covers:
- Up to 28,000 map loads, OR
- Up to 40,000 geocoding requests, OR
- Mixed usage as per pricing

### With $200 Monthly Credit Applied
```
Total Charges:        $92.66/month
Free Credit:          -$200.00/month
-------------------------------------------
NET GOOGLE MAPS:      $0.00/month (within free tier)
```

### Yearly Cost (Without Free Tier)
```
Full Cost:            $1,111.92/year
With Free Credit:     $0.00/year (if usage stays under $200/month)
```

---

## TOTAL COST SUMMARY

### Monthly Costs

#### Scenario A: Starter Setup (Single Instance, No CDN)
```
Alibaba Database:     $55.00 - $70.00
Alibaba Hosting:      $70.00 - $100.00
Alibaba DNS:          $3.00 - $5.00
Alibaba OSS Storage:  $4.00
Google Maps API:      $0.00 (free tier covers usage)
=========================================
MONTHLY TOTAL:        $132.00 - $179.00/month
```

#### Scenario B: Production Setup (Single Instance, With CDN)
```
Alibaba Database:     $55.00 - $70.00
Alibaba Hosting:      $70.00 - $100.00
Alibaba DNS:          $3.00 - $5.00
Alibaba OSS Storage:  $9.00 - $14.00
Google Maps API:      $0.00 (free tier covers usage)
=========================================
MONTHLY TOTAL:        $137.00 - $189.00/month
```

#### Scenario C: High Availability Setup (Dual Instance, With CDN)
```
Alibaba Database:     $55.00 - $70.00
Alibaba Hosting (HA): $130.00 - $170.00
Alibaba DNS:          $3.00 - $5.00
Alibaba OSS Storage:  $9.00 - $14.00
Google Maps API:      $0.00 (free tier covers usage)
=========================================
MONTHLY TOTAL:        $197.00 - $259.00/month
```

---

### Yearly Costs

#### Scenario A: Starter Setup
```
Alibaba Services:     $1,596.00 - $2,136.00/year
Google Maps API:      $0.00/year (within free tier)
=========================================
YEARLY TOTAL:         $1,596.00 - $2,136.00/year
                      (~$133/month - $178/month average)
```

#### Scenario B: Production Setup
```
Alibaba Services:     $1,656.00 - $2,256.00/year
Google Maps API:      $0.00/year (within free tier)
=========================================
YEARLY TOTAL:         $1,656.00 - $2,256.00/year
                      (~$138/month - $188/month average)
```

#### Scenario C: High Availability Setup
```
Alibaba Services:     $2,364.00 - $3,108.00/year
Google Maps API:      $0.00/year (within free tier)
=========================================
YEARLY TOTAL:         $2,364.00 - $3,108.00/year
                      (~$197/month - $259/month average)
```

---

## Cost Optimization Tips

### 1. Reserved Instances (Alibaba Cloud)
Save 30-50% by committing to 1-3 year reserved instances:
```
1-Year Reservation:   -30% discount
3-Year Reservation:   -50% discount
```

**Example Savings (Scenario B, 1-year reservation):**
```
Standard Cost:        $1,656.00 - $2,256.00/year
With 30% Discount:    $1,159.20 - $1,579.20/year
SAVINGS:              $496.80 - $676.80/year
```

### 2. Traffic Management
- Use Alibaba Cloud CDN for static assets (Next.js)
- Enable OSS browser caching headers
- Compress images before upload (reduce storage & bandwidth)

### 3. Google Maps Optimization
- **Cache API responses** (geocoding results can be cached indefinitely)
- **Lazy load maps** (only load when user scrolls to map section)
- **Use Static Maps API** for thumbnails (much cheaper)
- **Implement map clustering** for multiple markers

**Potential Savings:**
```
Current Usage:        10,000 map loads/month
With Optimization:    5,000 map loads/month
Savings:              $35.00/month = $420/year
```

### 4. Database Optimization
- Regular vacuum and analyze operations
- Proper indexing strategy
- Connection pooling (already implemented)
- Archive old data to OSS

### 5. Auto-Scaling
Configure auto-scaling to:
- Scale down during off-peak hours (nights/weekends)
- Pay only for what you use
- Potential savings: 20-30% on compute costs

---

## Growth Projection (Year 2-3)

### Scenario: 5x Growth (500 users, 25,000 properties)

```
Database (upgraded):   $120.00 - $150.00/month
Hosting (scaled):      $200.00 - $300.00/month
DNS:                   $5.00 - $10.00/month
Storage (500GB):       $20.00 - $30.00/month
Google Maps:           $150.00 - $200.00/month (exceeds free tier)
=========================================
MONTHLY TOTAL:         $495.00 - $690.00/month
YEARLY TOTAL:          $5,940.00 - $8,280.00/year
```

---

## Alternative: Current Setup (Railway + Cloudinary)

For comparison, your current setup likely costs:

```
Railway (Hobby):       $5.00/month + usage
Railway (Pro):         $20.00/month + usage
Database:              ~$10.00 - $30.00/month
Total Railway:         ~$30.00 - $80.00/month

Cloudinary (Free):     0GB storage, limited bandwidth
Cloudinary (Plus):     $99.00/month (100GB storage)

Google Maps:           $0.00 (free tier)
=========================================
CURRENT TOTAL:         $130.00 - $180.00/month
```

**Alibaba Cloud is competitive** and provides:
- More control over infrastructure
- Better pricing at scale
- No vendor lock-in
- Better latency for Asia-Pacific region

---

## Recommended Action Plan

### Phase 1: Start with Scenario A (Months 1-6)
**Cost**: $132-179/month
- Single ECS instance (hosting frontend + backend)
- Basic RDS PostgreSQL
- OSS without CDN
- Monitor usage patterns

### Phase 2: Upgrade to Scenario B (Months 6-12)
**Cost**: $137-189/month
- Add CDN for better performance
- Enable OSS lifecycle rules
- Optimize Google Maps usage

### Phase 3: Scale to Scenario C (Year 2+)
**Cost**: $197-259/month
- Dual instances for high availability
- Load balancer for redundancy
- Auto-scaling enabled
- Consider reserved instances for 30% savings

---

## Payment Options

### Alibaba Cloud
- **Pay-as-you-go**: Monthly billing, no commitment
- **Subscription**: 1-3 year commitment, 30-50% discount
- **Recharge**: Pre-pay and get bonus credits

### Google Cloud (Maps API)
- **Monthly billing** via credit card
- **$200 free credit** applies automatically each month
- Only charged when exceeding free tier

---

## Conclusion

**Recommended Starting Point**: **Scenario A**

**Monthly**: $132-179 (~₱7,392-₱10,024 PHP at ₱56/$1)  
**Yearly**: $1,596-2,136 (~₱89,376-₱119,616 PHP)

This gives you:
- Production-ready infrastructure
- Room to grow
- Professional grade database
- Reliable file storage
- Free Google Maps (under usage limits)

**Alibaba Cloud Pros**:
- Excellent Asia-Pacific presence
- Competitive pricing
- Enterprise-grade services
- Good documentation

**Alibaba Cloud Cons**:
- Less familiar than AWS/GCP
- English support may be limited
- Initial setup learning curve

---

## Additional Resources

- [Alibaba Cloud Pricing Calculator](https://www.alibabacloud.com/pricing-calculator)
- [Google Maps Platform Pricing](https://mapsplatform.google.com/pricing/)
- [Alibaba Cloud Philippines](https://www.alibabacloud.com/en/regional_service/philippines)

---

**Generated**: October 7, 2025  
**Project**: BDD Property Tracker  
**Version**: 1.0

