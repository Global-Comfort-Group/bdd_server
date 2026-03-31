# Negotiation Chronicle View Update

## Change Summary

Updated the negotiation chronicle detail page to display uploaded data in a proper table format instead of a timeline view.

## Before vs After

### Before (Timeline View):
```
Negotiations Timeline
├─ Date | Subject Matter
├─ Date | Subject Matter
└─ Date | Subject Matter
```

### After (Table View):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Header | Value | Agreed Negotiation Price | For Negotiation | Difference (%) │
├─────────────────────────────────────────────────────────────────────────────┤
│ Property Price | ₱10,000,000 | ₱9,000,000 | ₱10,000,000 | -10.00% │
│ Lot Area | 1000 sqm | 950 sqm | 1000 sqm | -5.00% │
│ Monthly Rent | ₱50,000 | ₱45,000 | ₱50,000 | -10.00% │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Changed

**`src/app/(dashboard)/nego-table/[id]/page.tsx`**

### Key Updates:

1. **Changed Icon**: `Clock` → `FileText`
2. **Changed Title**: "Negotiations Timeline" → "Negotiation Chronicle Data"
3. **Changed Layout**: Timeline cards → Table format

### Table Structure:

```tsx
<table>
  <thead>
    <tr>
      <th>Header</th>
      <th>Value</th>
      <th>Agreed Negotiation Price</th>
      <th>For Negotiation</th>
      <th>Difference (%)</th>
    </tr>
  </thead>
  <tbody>
    {negoTable.negotiations.map((negotiation) => (
      <tr>
        <td>{negotiation.header}</td>
        <td>{negotiation.value}</td>
        <td>{formatCurrency(negotiation.agreed_amount)}</td>
        <td>{formatCurrency(negotiation.for_nego)}</td>
        <td className={diffColor}>
          {negotiation.difference_percentage}%
        </td>
      </tr>
    ))}
  </tbody>
</table>
```

### Color Coding:

- **Green (font-semibold)**: Negative percentage (BDD wants less - good for BDD)
- **Red (font-semibold)**: Positive percentage (BDD wants more - good for agent)
- **Gray**: No difference or null values

## Data Flow

1. **Upload CSV**: BDD employee uploads negotiation data file
2. **Parse Data**: Server parses and calculates difference percentage
3. **Display Table**: Detail page shows data in structured table format

## Example Data Format

### CSV Input:
```csv
Header,Value,Agreed Negotiation Price,For Negotiation
Property Price,₱10000000,9000000,10000000
Lot Area,1000 sqm,950,1000
Monthly Rent,₱50000,45000,50000
```

### Parsed Data:
```json
[
  {
    "header": "Property Price",
    "value": "₱10,000,000",
    "agreed_amount": 9000000,
    "for_nego": 10000000,
    "difference_percentage": -10.00
  }
]
```

### Table Display:
| Header | Value | Agreed Negotiation Price | For Negotiation | Difference (%) |
|--------|-------|-------------------------|-----------------|----------------|
| Property Price | ₱10,000,000 | ₱9,000,000 | ₱10,000,000 | **-10.00%** ✅ |
| Lot Area | 1000 sqm | 950 sqm | 1000 sqm | **-5.00%** ✅ |

## UI Features

### 1. Hover Effect
```css
hover:bg-gray-50
```
Rows highlight on hover for better readability.

### 2. Conditional Formatting
```tsx
const diffColor = negotiation.difference_percentage 
  ? negotiation.difference_percentage < 0 
    ? 'text-green-600 font-semibold'  // BDD wants less
    : 'text-red-600 font-semibold'    // BDD wants more
  : ''
```

### 3. Currency Formatting
```tsx
formatCurrency(negotiation.agreed_amount, 'PHP')
// Output: ₱9,000,000
```

### 4. Empty State
```tsx
{negoTable.negotiations.length === 0 && (
  <div className="text-center py-8">
    <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
    <p className="text-sm text-muted-foreground">
      No negotiations recorded yet
    </p>
  </div>
)}
```

## Benefits

1. ✅ **Clear Structure**: Table format is easier to read than timeline
2. ✅ **Quick Comparison**: See agreed vs negotiation prices side by side
3. ✅ **Visual Indicators**: Color coding shows favorable/unfavorable differences
4. ✅ **Accurate Calculations**: Proper difference formula applied
5. ✅ **Professional Look**: Matches Excel/spreadsheet format users expect

## Testing

### Test Case 1: BDD Wants Less (Good)
```
Agreed: ₱9,000,000
For Nego: ₱10,000,000
Difference: -10% (GREEN) ✅
```

### Test Case 2: BDD Wants More (Neutral)
```
Agreed: ₱11,000,000
For Nego: ₱10,000,000
Difference: +10% (RED) ⚠️
```

### Test Case 3: Both Agreed
```
Agreed: ₱10,000,000
For Nego: ₱10,000,000
Difference: 0% ✅
```

## Next Steps

1. Refresh your browser to see the new table layout
2. Upload a CSV file with negotiation data
3. View the negotiation chronicle detail page
4. Verify the table displays correctly with proper formatting

## Status

✅ **COMPLETE** - Table view implemented
✅ **READY** - Refresh browser to see changes

The negotiation chronicle detail page now shows your data in the correct table format!

