# Violation Logging Cooldown System

## Overview

The violation logger includes a **smart cooldown mechanism** to prevent duplicate logging of the same violation. This ensures that:

1. The same person with the same violation isn't logged multiple times in quick succession
2. Log folder doesn't get flooded with duplicate frames
3. System performance remains optimal
4. Storage space is conserved

## How It Works

### Violation Fingerprinting

Each violation is identified by a unique "fingerprint" based on:
- **Detected persons**: Names of all identified faces (or "Unknown")
- **Violation items**: List of non-compliant items detected

Example fingerprints:
```
John Doe:Shorts-T-Shirt
Unknown:Shorts
Jane Smith-John Doe:T-Shirt
```

### Cooldown Period

- **Default**: 10 seconds
- **Range**: 1-300 seconds (configurable)
- **Behavior**: Same violation won't be logged again until cooldown expires

### Smart Cleanup

- Old violations are automatically cleaned up every 5 seconds
- Only violations within cooldown period are tracked
- Memory efficient - doesn't accumulate indefinitely

## Usage Examples

### Scenario 1: Same Person, Same Violation
```
Time: 10:00:00 - John Doe wearing Shorts → ✅ LOGGED
Time: 10:00:03 - John Doe wearing Shorts → ❌ SKIPPED (cooldown)
Time: 10:00:07 - John Doe wearing Shorts → ❌ SKIPPED (cooldown)
Time: 10:00:11 - John Doe wearing Shorts → ✅ LOGGED (cooldown expired)
```

### Scenario 2: Same Person, Different Violation
```
Time: 10:00:00 - John Doe wearing Shorts → ✅ LOGGED
Time: 10:00:03 - John Doe wearing T-Shirt → ✅ LOGGED (different violation)
```

### Scenario 3: Different Person, Same Violation
```
Time: 10:00:00 - John Doe wearing Shorts → ✅ LOGGED
Time: 10:00:03 - Jane Smith wearing Shorts → ✅ LOGGED (different person)
```

### Scenario 4: Multiple Persons
```
Time: 10:00:00 - [John, Jane] wearing Shorts → ✅ LOGGED
Time: 10:00:03 - [John, Jane] wearing Shorts → ❌ SKIPPED (same group)
Time: 10:00:11 - [John] wearing Shorts → ✅ LOGGED (different group)
```

## Configuration

### Via Code

Edit `main.py`:
```python
# Initialize with custom cooldown (in seconds)
violation_logger = get_violation_logger(cooldown_seconds=15)
```

### Via API

```bash
# Set cooldown to 15 seconds
curl -X POST http://localhost:8000/api/logging/cooldown/ \
  -H "Content-Type: application/json" \
  -d '{"cooldown_seconds": 15}'
```

Response:
```json
{
  "success": true,
  "cooldown_seconds": 15,
  "message": "Cooldown set to 15 seconds"
}
```

### Recommended Settings

| Scenario | Cooldown | Reason |
|----------|----------|--------|
| **High Traffic Area** | 5-10s | Quick succession of different people |
| **Single Person Monitoring** | 15-30s | Person unlikely to fix violation quickly |
| **Classroom/Office** | 30-60s | Static environment, violations persist |
| **Event Entry Point** | 3-5s | Many people passing through |

## API Endpoints

### Get Logging Status
```
GET /api/logging/status/
```

Response:
```json
{
  "logging_enabled": true,
  "cooldown_seconds": 10,
  "active_violations": 3,
  "log_folder": "non_compliance_logs"
}
```

### Get Detailed Statistics
```
GET /api/logging/stats/
```

Response:
```json
{
  "logging_enabled": true,
  "cooldown_seconds": 10,
  "active_violations": 3,
  "log_folder": "non_compliance_logs"
}
```

### Set Cooldown Period
```
POST /api/logging/cooldown/
Content-Type: application/json

{
  "cooldown_seconds": 15
}
```

**Constraints:**
- Minimum: 1 second
- Maximum: 300 seconds (5 minutes)

## Benefits

### 1. Prevents Duplicate Logs
❌ **Without Cooldown:**
```
violation_20250125_100000.jpg - John Doe, Shorts
violation_20250125_100001.jpg - John Doe, Shorts
violation_20250125_100002.jpg - John Doe, Shorts
violation_20250125_100003.jpg - John Doe, Shorts
... (60 frames in 1 minute!)
```

✅ **With Cooldown (10s):**
```
violation_20250125_100000.jpg - John Doe, Shorts
violation_20250125_100011.jpg - John Doe, Shorts
violation_20250125_100022.jpg - John Doe, Shorts
... (6 frames in 1 minute)
```

### 2. Saves Storage Space
- Reduces redundant frames by 80-90%
- Keeps only meaningful evidence
- Easier to review logs

### 3. Better Performance
- Less I/O operations
- Reduced face detection overhead (only when logging)
- More responsive system

### 4. Cleaner Audit Trail
- One log per violation occurrence
- Easier to count unique violations
- Better for reporting and analysis

## Technical Details

### Hash Generation

```python
def _generate_violation_hash(self, face_results, non_compliant_items):
    # Sort for consistent hashing
    names = sorted([face['name'] for face in face_results])
    items = sorted(non_compliant_items)
    
    # Create string: "Name1-Name2:Item1-Item2"
    violation_str = f"{'-'.join(names)}:{'-'.join(items)}"
    
    # Generate MD5 hash (first 16 chars)
    return hashlib.md5(violation_str.encode()).hexdigest()[:16]
```

### Cooldown Check

```python
def _should_log_violation(self, face_results, non_compliant_items):
    # Generate hash for this violation
    violation_hash = self._generate_violation_hash(face_results, non_compliant_items)
    
    # Check if recently logged
    if violation_hash in self.recent_violations:
        time_since_last_log = current_time - self.recent_violations[violation_hash]
        
        if time_since_last_log < self.cooldown_seconds:
            return False  # Still in cooldown
    
    # Update timestamp and allow logging
    self.recent_violations[violation_hash] = current_time
    return True
```

### Memory Management

- Automatic cleanup every 5 seconds
- Only stores hash + timestamp (minimal memory)
- Expired entries removed automatically
- No memory leak issues

## Logging

The system logs cooldown events:

```
2025-01-25 10:00:03 - Violation cooldown active: 7.2s remaining
2025-01-25 10:00:11 - Violation logged: violation_20250125_100011_234.jpg
```

## Troubleshooting

### Violations Not Being Logged

1. **Check if logging is enabled**:
   ```bash
   curl http://localhost:8000/api/logging/status/
   ```

2. **Check cooldown period**:
   - May be too long for your use case
   - Try reducing: `POST /api/logging/cooldown/ {"cooldown_seconds": 5}`

3. **Check active violations**:
   ```bash
   curl http://localhost:8000/api/logging/stats/
   ```
   - If `active_violations` is high, many are in cooldown

### Too Many Logs

1. **Increase cooldown**:
   ```bash
   curl -X POST http://localhost:8000/api/logging/cooldown/ \
     -d '{"cooldown_seconds": 30}'
   ```

2. **Check for different persons**:
   - Each unique person creates a separate log
   - This is expected behavior

### Cooldown Not Working

1. **Restart the application**:
   - Cooldown state is in-memory
   - Restarting clears all cooldowns

2. **Check face detection**:
   - If faces aren't detected, each frame gets different hash
   - Verify face detection is working properly

3. **Check logs**:
   - Look for "Violation cooldown active" messages
   - Indicates cooldown is functioning

## Best Practices

1. **Start with default** (10s) and adjust based on your needs
2. **Monitor active_violations** count - should be low (<10)
3. **Increase cooldown** if log folder grows too quickly
4. **Decrease cooldown** if missing important violations
5. **Clear logs** when disabling logging to reset state
6. **Test thoroughly** with your specific use case

## Future Enhancements

Potential improvements:
- Configurable per-person cooldowns
- Different cooldowns for different violation types
- Sliding window for repeat offenders
- Export cooldown statistics
- UI controls for cooldown adjustment

## Summary

The cooldown system:
- ✅ Prevents duplicate logging of same violation
- ✅ Identifies violations by person + items
- ✅ Configurable cooldown period (1-300s)
- ✅ Automatic cleanup of expired entries
- ✅ API endpoints for management
- ✅ Efficient memory usage
- ✅ Better log quality and storage efficiency

Default 10-second cooldown works well for most scenarios!
