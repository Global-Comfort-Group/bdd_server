# Negotiation Chronicle Data on Property Page

## Summary

The negotiation chronicle data is **already displayed** on the property detail page! You don't need to navigate to a separate page to view it.

## How It Works

### Location:
**Property Detail Page** → `/property/[id]`

When you view a property, the page has a section called **"Negotiation Chronicles"** that shows:
1. All chronicles for that property
2. Upload functionality for each chronicle
3. **The negotiation data table** (automatically displayed when you expand a chronicle)

## UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Property Details Page                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Property Images & Map]                                     │
│                                                             │
│ [Property Details]                                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ 📋 Negotiation Chronicles (2)   [+ Create Chronicle]│   │
│ ├─────────────────────────────────────────────────────┤   │
│ │                                                       │   │
│ │ ┌───────────────────────────────────────────────┐   │   │
│ │ │ ✅ ACTIVE  Chronicle #1                       │   │   │
│ │ │ Source: Auto-generated                  [Expand]│   │   │
│ │ ├───────────────────────────────────────────────┤   │   │
│ │ │ Created: Oct 2, 2025  |  0 entries           │   │   │
│ │ ├───────────────────────────────────────────────┤   │   │
│ │ │                                               │   │   │
│ │ │ 📤 Upload Negotiation Data:                   │   │   │
│ │ │ [Choose File] or [Enter Google Sheets Link]  │   │   │
│ │ │                                               │   │   │
│ │ │ ┌─────────────────────────────────────────┐  │   │   │
│ │ │ │ 📊 negotiations.csv                     │  │   │   │
│ │ │ ├─────────────────────────────────────────┤  │   │   │
│ │ │ │ Header | Value | Agreed | For Nego | % │  │   │   │
│ │ │ ├─────────────────────────────────────────┤  │   │   │
│ │ │ │ Property Price | ₱10M | ₱9M | ₱10M | -10% │  │   │   │
│ │ │ │ Lot Area | 1000 sqm | 950 | 1000 | -5%  │  │   │   │
│ │ │ │ Monthly Rent | ₱50K | ₱45K | ₱50K | -10% │  │   │   │
│ │ │ └─────────────────────────────────────────┘  │   │   │
│ │ │                                               │   │   │
│ │ └───────────────────────────────────────────────┘   │   │
│ └─────────────────────────────────────────────────┘   │
│                                                             │
│ [Documents & Attachments]                                   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Collapsible Chronicles
Click **"Expand"** on any chronicle to see:
- Financial summary
- Recent negotiations
- **Upload area**
- **Negotiation data table** (after uploading)

### 2. Upload Options
Two ways to add data:
- **Upload File**: CSV or Excel
- **Google Sheets Link**: Paste a link

### 3. Data Table Display
The uploaded data automatically shows in a table:

| Header | Value | Agreed Negotiation Price | For Negotiation | Difference (%) |
|--------|-------|-------------------------|-----------------|----------------|
| Property Price | ₱10,000,000 | ₱9,000,000 | ₱10,000,000 | **-10.00%** 🟢 |
| Lot Area | 1000 sqm | 950 sqm | 1000 sqm | **-5.00%** 🟢 |
| Monthly Rent | ₱50,000 | ₱45,000 | ₱50,000 | **-10.00%** 🟢 |

### 4. Color Coding
- **Green** = Negative % (BDD wants less - favorable)
- **Red** = Positive % (BDD wants more)

### 5. Summary Statistics
Below each table:
- Total Items
- Items with Amounts
- Average Difference

## How to Use

### Step 1: View Property
1. Go to "All Properties"
2. Click on any property
3. Scroll to "Negotiation Chronicles" section

### Step 2: Expand Chronicle
1. Find the chronicle you want to view
2. Click **"Expand"** button
3. The section expands to show upload area and data table

### Step 3: Upload Data (if not already uploaded)
1. Click **"Choose File"** or enter Google Sheets link
2. Click **"Upload"**
3. Data table appears automatically below

### Step 4: View Data
- The table displays immediately after upload
- No need to navigate away from the property page
- You can view multiple chronicles on the same page

## Components Involved

### 1. PropertyNegoSection
**File**: `src/components/property/property-nego-section.tsx`
- Main container for all chronicles
- Handles expand/collapse
- Manages uploads

### 2. NegotiationChronicleTable
**File**: `src/components/negotiations/negotiation-chronicle-table.tsx`
- Displays the data table
- Shows: Header | Value | Agreed Negotiation Price | For Negotiation | Difference (%)
- Color coding and formatting

### 3. NegotiationChronicleUpload
**File**: `src/components/negotiations/negotiation-chronicle-upload.tsx`
- File upload or Google Sheets link
- Parses CSV/Excel
- Calculates differences

## Updates Made

### Column Header Updated
Changed "Agreed Amount" to "Agreed Negotiation Price" to match your exact requirement.

**Before**:
```
Header | Value | Agreed Amount | For Negotiation | Difference (%)
```

**After**:
```
Header | Value | Agreed Negotiation Price | For Negotiation | Difference (%)
```

## Benefits

1. ✅ **No Navigation Needed**: View everything on the property page
2. ✅ **Multiple Chronicles**: Can see all chronicles for a property
3. ✅ **Inline Upload**: Upload data directly on the property page
4. ✅ **Immediate Display**: Table appears right after upload
5. ✅ **Full Context**: See property details and negotiation data together

## Example Workflow

```
1. Open Property #20 (test property)
   ↓
2. Scroll to "Negotiation Chronicles" section
   ↓
3. Click "Expand" on Chronicle #1
   ↓
4. See upload area and any existing data tables
   ↓
5. Upload CSV file with negotiation data
   ↓
6. Table appears automatically below
   ↓
7. View all negotiation data without leaving the page!
```

## Status

✅ **ALREADY IMPLEMENTED** - The functionality is ready!
✅ **COLUMN HEADER UPDATED** - Changed to "Agreed Negotiation Price"
✅ **READY TO USE** - Just refresh your browser

## Next Steps

1. **Refresh your browser**
2. Go to any property page
3. Scroll to "Negotiation Chronicles"
4. Click "Expand" on a chronicle
5. You'll see the upload area and data table!

**No need to navigate to separate pages - everything is on the property page!** 🎉

