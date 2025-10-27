# Violation Logging System Improvements

## Overview
Enhanced the violation logging system with intelligent filtering and daily tracking capabilities.

## New Features

### 1. **Minimum Face Confidence Threshold (47%)**
- Faces with confidence below 47% are automatically marked as "Unknown"
- Ensures only reliable face identifications are used for tracking
- Configuration: `min_face_confidence=47.0` in `ViolationLogger`

### 2. **No Face Detection = No Logging**
- Violations are only logged if at least one face is detected
- Prevents logging of empty frames or objects without people
- Ensures accountability by linking violations to specific individuals

### 3. **Daily Logging Limit for Identified Persons**
- Each identified person (name with confidence ≥ 47%) can only be logged **once per day**
- Prevents spam logging of the same person throughout the day
- Resets automatically at midnight for fresh daily tracking
- Persistent tracking via `daily_logs.json` file

### 4. **Unlimited Logging for Unknown Persons**
- "Unknown" persons (faces with confidence < 47% or not in database) have **no daily limit**
- Can be logged multiple times per day
- Useful for tracking unauthorized/unregistered individuals

### 5. **Daily Logs Persistence**
- Daily logging data stored in `non_compliance_logs/daily_logs.json`
- Format: `{"Person_Name": "YYYY-MM-DD"}`
- Automatically cleans up old entries from previous days
- Survives server restarts

## Technical Implementation

### File: `utils/violation_logger.py`

#### New Methods:
- `_load_daily_logs()` - Load persistent daily tracking data
- `_save_daily_logs()` - Save daily tracking data to disk
- `_is_person_logged_today(person_name)` - Check if person already logged today
- `_mark_person_logged_today(person_name)` - Mark person as logged for current day
- `_filter_faces_by_confidence(face_results)` - Apply 47% confidence threshold

#### Modified Methods:
- `__init__()` - Added `min_face_confidence` parameter and daily logs tracking
- `_should_log_violation()` - Enhanced with:
  - No faces detection check
  - Daily limit checking for identified persons
  - Unlimited logging for Unknown persons
  - Returns tuple: `(should_log: bool, reason: str)`
- `save_violation()` - Now filters faces by confidence before logging
- `get_stats()` - Added `min_face_confidence` and `persons_logged_today` fields

#### Configuration:
```python
violation_logger = ViolationLogger(
    log_folder="non_compliance_logs",
    cooldown_seconds=10,
    min_face_confidence=47.0  # NEW: Minimum confidence for face identification
)
```

## Logic Flow

### Violation Logging Decision Tree:
```
1. Is logging enabled? → NO: Skip
                       → YES: Continue

2. Are any faces detected? → NO: Skip (log "No faces detected")
                           → YES: Continue

3. Filter faces by confidence (47% threshold)
   - Below 47% → Mark as "Unknown"
   - Above 47% → Keep original name

4. Get identified persons (non-Unknown)

5. Check if any identified person already logged today
   → YES: Skip (log "Already logged today: [names]")
   → NO: Continue

6. Check cooldown period for rapid re-detection
   → In cooldown: Skip
   → Cooldown expired: Continue

7. Log violation and mark identified persons as logged today
   - Unknown persons are NOT marked (can be logged again)
```

## Benefits

### For Known/Identified Persons:
- ✅ Only logged once per day (reduces duplicate logs)
- ✅ Resets daily for consistent monitoring
- ✅ High confidence threshold ensures accurate identification
- ✅ Linked to specific individuals for accountability

### For Unknown Persons:
- ✅ Can be logged multiple times (important for security)
- ✅ No daily limit (captures all unauthorized violations)
- ✅ Flagged visually with orange boxes
- ✅ Not tracked in daily logs (preserved anonymity)

### System-Wide:
- ✅ Prevents log spam from same person throughout day
- ✅ Ensures violations are tied to actual people
- ✅ Automatic cleanup and daily reset
- ✅ Persistent across server restarts
- ✅ Clear logging reasons for debugging

## Usage Example

### Normal Operation:
1. **8:00 AM** - John (confidence 85%) detected with t-shirt → ✅ **LOGGED**
2. **8:05 AM** - John detected again → ❌ Skipped (cooldown)
3. **9:00 AM** - John detected again → ❌ Skipped (already logged today)
4. **10:00 AM** - Unknown person (confidence 32%) detected → ✅ **LOGGED**
5. **10:30 AM** - Same unknown person detected → ✅ **LOGGED** (no daily limit)
6. **Next day 8:00 AM** - John detected → ✅ **LOGGED** (new day, reset)

### Log Messages:
- `"Violation not logged: No faces detected"` - No faces in frame
- `"Violation not logged: Person(s) already logged today: John Doe"` - Daily limit reached
- `"Marked John Doe as logged for today"` - Successfully logged
- `"Face detection: Found 1 faces in frame"` - Face detection success
- `"Violation cooldown active: 5.2s remaining"` - Rapid re-detection prevented

## API Statistics

Enhanced `GET /api/logging/stats/` endpoint now returns:
```json
{
  "logging_enabled": true,
  "cooldown_seconds": 10,
  "min_face_confidence": 47.0,
  "active_violations": 2,
  "persons_logged_today": 3,
  "log_folder": "non_compliance_logs"
}
```

## Files Created/Modified

### Modified:
- `utils/violation_logger.py` - Core logging logic enhanced

### Created:
- `non_compliance_logs/daily_logs.json` - Persistent daily tracking (auto-generated)

### Log Structure:
```
non_compliance_logs/
├── daily_logs.json              # Daily tracking data
├── violation_20251027_201530_123.jpg
├── violation_20251027_201645_456.jpg
└── violation_log.txt
```

## Configuration

Default values:
- `cooldown_seconds`: 10 (time between rapid re-detection)
- `min_face_confidence`: 47.0 (minimum confidence to identify person)
- `log_folder`: "non_compliance_logs"

## Notes

- Daily reset happens automatically based on date comparison
- Unknown persons are never added to daily logs (unlimited logging)
- `daily_logs.json` is automatically cleaned of old dates on load
- System is resilient to server restarts (persistent storage)
- Face confidence threshold (47%) can be adjusted via initialization

---

**Last Updated**: October 27, 2025
