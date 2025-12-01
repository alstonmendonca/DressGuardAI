# License Plate Reporting Integration

## Overview
License plate numbers detected by the Vehicle Helmet model are now fully integrated into the dashboard and all report generation features.

## What Was Updated

### 1. Daily Logs Structure (`utils/violation_logger.py`)
- **Modified `_mark_person_logged_today()` method:**
  - Added `license_plates` parameter with default empty list
  - Stores license plate texts in `logged_today` dictionary
  - Structure: `{"date": "...", "items": [...], "filepath": "...", "license_plates": [...]}`

- **Updated `_save_violation_async()` method:**
  - Extracts license plate texts from detected plates
  - Passes plate data to `_mark_person_logged_today()`
  - Enhanced logging to show plates in console output

### 2. Dashboard Logs API (`main.py` - `/dashboard/logs/`)
- Extracts `license_plates` from daily logs
- Returns license plates array in log entries
- Response format includes: `"license_plates": ["KA01AB1234", ...]`

### 3. Excel Report Generation (`main.py` - `/dashboard/report/{date}`)
- **New Column:** "License Plates" (Column I)
- Shows comma-separated license plate numbers
- Displays "N/A" if no plates detected
- Updated column widths:
  - Column I (License Plates): 20 characters
  - Column J (Image File): 30 characters
- Title row now spans A1:J1 (instead of A1:I1)

### 4. WhatsApp Report Sending (`main.py` - `/dashboard/send-whatsapp/`)
- Excel report includes license plates column
- Same 10-column format as download report
- Automatically includes plates in WhatsApp-sent reports

## Data Flow

1. **Detection Phase:**
   - PaddleOCR extracts license plate text from vehicle helmet violations
   - License plates logged to `violation_log.txt` and displayed on images

2. **Storage Phase:**
   - License plate texts stored in `logged_today` dictionary
   - Persisted in `daily_logs.json` for historical tracking

3. **Reporting Phase:**
   - Dashboard API returns plates in log entries
   - Excel reports include dedicated "License Plates" column
   - WhatsApp reports include plates in attachment

## Report Format

### Excel Columns (10 total):
| # | Full Name | USN | Department | Branch | Email | Timestamp | Violations | License Plates | Image File |
|---|-----------|-----|------------|--------|-------|-----------|------------|----------------|------------|
| 1 | John Doe  | ... | ...        | ...    | ...   | ...       | No Helmet  | KA01AB1234     | violation_... |

### Dashboard API Response:
```json
{
  "logs": [
    {
      "id": "violation_20250129_143022_001.jpg",
      "filename": "violation_20250129_143022_001.jpg",
      "timestamp": "2025-01-29 14:30:22.001",
      "person": "Unknown",
      "violations": ["No Helmet"],
      "license_plates": ["KA01AB1234", "KA02CD5678"],
      "image_url": "/api/dashboard/image/violation_20250129_143022_001.jpg"
    }
  ]
}
```

## Backward Compatibility
- Old logs without `license_plates` field return empty array `[]`
- Reports show "N/A" for violations without license plates
- System gracefully handles missing license plate data

## Testing Checklist
✅ License plates stored in `logged_today` dictionary
✅ Dashboard API returns license plates in log entries
✅ Excel report download includes "License Plates" column
✅ WhatsApp report includes license plates column
✅ No syntax errors in updated files
✅ Backward compatible with existing logs

## Files Modified
1. `utils/violation_logger.py` - Data storage layer
2. `main.py` - Dashboard and reporting endpoints

## Usage
License plates will automatically appear in:
- Dashboard logs view (`/dashboard/logs/`)
- Excel report downloads (`/dashboard/report/{date}`)
- WhatsApp report attachments (`/dashboard/send-whatsapp/`)

Only applies to Vehicle Helmet model detections (when OCR is enabled).
