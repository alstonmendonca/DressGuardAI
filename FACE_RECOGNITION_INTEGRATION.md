# Face Recognition & Violation Logging Integration - Summary

## 🎯 Overview

DressGuard now includes **automated face recognition and violation logging** capabilities with **smart cooldown** to prevent duplicates. When non-compliant clothing is detected and logging is enabled, the system:

1. Captures the frame
2. Detects and identifies faces using Redis-backed face recognition
3. Checks cooldown period (prevents duplicate logging of same violation)
4. Saves annotated frames with both compliance and face detection boxes
5. Logs violation details with timestamps and identified persons

## 🆕 Key Features

### Smart Cooldown System
- **Prevents duplicate logs** of the same person with same violation
- **Configurable cooldown period** (default: 10 seconds, range: 1-300s)
- **Violation fingerprinting** based on detected persons + violation items
- **Automatic cleanup** of expired entries
- **API endpoints** for cooldown management

See `VIOLATION_COOLDOWN.md` for complete documentation.

## 📁 New Files Created

### Backend

1. **`sync_faces.py`** - Synchronize face database with Redis
   - Processes images from `database/` folder
   - Extracts face encodings and stores in Redis
   - Handles updates and removals

2. **`utils/face_recognition_utils.py`** - Face detection and recognition
   - `detect_and_identify_faces()` - Main detection function
   - `recognize_face()` - Match faces against Redis database
   - `draw_face_boxes()` - Annotate frames with face boxes
   - Uses Redis for fast encoding lookups

3. **`utils/violation_logger.py`** - Violation logging system with cooldown
   - `ViolationLogger` class manages logging state
   - `save_violation()` - Saves annotated frames (with duplicate prevention)
   - Smart cooldown mechanism (hash-based violation tracking)
   - Draws both compliance and face detection boxes
   - Adds metadata overlays with timestamps
   - Maintains text log file
   - Automatic cleanup of expired violations

4. **`test_redis.py`** - Redis connection testing utility
   - Verifies Redis server is running
   - Shows registered users
   - Diagnostic information

5. **Documentation**:
   - **`FACE_RECOGNITION.md`** - Complete setup guide
   - **`VIOLATION_COOLDOWN.md`** - Cooldown system documentation
   - **`FACE_RECOGNITION_INTEGRATION.md`** - This file

### Frontend

1. **Updated `ActionsPanel.jsx`** - Logging control UI
   - "Start/Stop Logging" toggle button
   - Real-time status indicator
   - Color-coded (green=off, red=on)
   - Fetches logging status on mount

2. **Added Icons** to `Icons.jsx`:
   - `HistoryIcon` - For history/logs
   - `FileTextIcon` - For reports

### Configuration

1. **Updated `requirements.txt`**:
   ```
   face-recognition==1.3.0
   dlib==19.24.6
   redis==5.2.1
   ```

2. **Updated `.gitignore`**:
   - Excludes `database/` (personal images)
   - Excludes `non_compliance_logs/` (violation frames)
   - Excludes `frames/` (temporary processing)
   - Excludes Redis dump files

## 🔧 Modified Files

### Backend (`main.py`)

1. **Added imports**:
   ```python
   from utils.violation_logger import get_violation_logger
   from utils.face_recognition_utils import detect_and_identify_faces
   ```

2. **Initialized violation logger**:
   ```python
   violation_logger = get_violation_logger()
   ```

3. **Added logging control endpoints**:
   - `POST /api/logging/toggle/` - Toggle logging
   - `GET /api/logging/status/` - Get logging status
   - `POST /api/logging/enable/` - Enable logging
   - `POST /api/logging/disable/` - Disable logging

4. **Integrated face detection in webcam stream**:
   - Detects faces when violations occur
   - Only runs when logging is enabled
   - Saves annotated frames with both compliance and face boxes
   - Works in both distance-check and normal detection modes

## 📂 Directory Structure

```
DressGuard/
├── database/                    # NEW - Face recognition database
│   ├── .gitkeep
│   ├── Student1/               # Add folders for each person
│   │   ├── 0.jpg
│   │   ├── 1.jpg
│   │   └── 2.jpg
│   └── ...
├── frames/                     # NEW - Temp processing folder
├── non_compliance_logs/        # NEW - Violation logs folder
│   ├── violation_20250125_143020_123.jpg
│   ├── violation_20250125_143025_456.jpg
│   └── violation_log.txt
├── utils/
│   ├── face_recognition_utils.py  # NEW
│   ├── violation_logger.py        # NEW
│   └── ...
├── sync_faces.py               # NEW
├── test_redis.py               # NEW
├── FACE_RECOGNITION.md         # NEW
└── ...
```

## 🚀 Setup Steps

### 1. Install Prerequisites

```bash
# Install Redis (if not already installed)
# Download from: https://github.com/microsoftarchive/redis/releases
# Check "Add Redis to PATH" during installation

# Install CMake (if not already installed)
# Download from: https://cmake.org/download/

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start Redis

```bash
# Start Redis server
redis-server

# Or if configured as Windows service, it may start automatically
```

### 3. Test Redis Connection

```bash
python test_redis.py
```

Should output:
```
✓ Redis connection successful!
  Server: localhost:6379
  Response: PONG
  ...
```

### 4. Prepare Face Database

```bash
# Create database structure
database/
├── Student1/
│   ├── 0.jpg
│   ├── 1.jpg
│   └── 2.jpg
├── Student2/
│   └── ...
└── ...
```

**Requirements:**
- Each subfolder = person's name
- Images numbered: 0.jpg, 1.jpg, 2.jpg, etc.
- Clear, front-facing photos
- 3-5 images per person recommended

### 5. Sync Faces to Redis

```bash
python sync_faces.py
```

Output:
```
Processing: Student1 (student1)
    Found 1 face(s) in 0.jpg
    Found 1 face(s) in 1.jpg
  Successfully updated Student1. Added 2 encodings from 2 images.

Synchronization complete!
Total known users in DB: 4
```

### 6. Start Application

```bash
# Terminal 1: Backend
uvicorn main:app --reload

# Terminal 2: Frontend (if needed)
cd frontend
npm run dev
```

## 💡 How to Use

### Enable Violation Logging

1. Open DressGuard web interface
2. Look for the **Actions** panel on the right
3. Click **"Start Logging"** button
   - Button turns red when active
   - Shows "Stop Logging" label

### What Happens When Logging is Active

1. **Real-time Detection**: Webcam detects clothing items
2. **Compliance Check**: System checks for non-compliant items
3. **If Violation Detected**:
   - Frame is captured
   - Faces are detected and identified
   - Annotated frame is saved to `non_compliance_logs/`
   - Details logged to `violation_log.txt`

### Viewing Logs

```
non_compliance_logs/
├── violation_20250125_143020_123.jpg  # Annotated frame with boxes
├── violation_20250125_143025_456.jpg
└── violation_log.txt                  # Text log with details
```

Each saved frame includes:
- **Red boxes**: Non-compliant clothing items
- **Green boxes**: Compliant items
- **Magenta boxes**: Recognized faces (with confidence %)
- **Orange boxes**: Unknown faces
- **Top overlay**: Timestamp, violations, identified persons

## 🎨 Visual Indicators

### Webcam Stream
- **"DETECTING"** - Normal detection mode
- **"DETECTING + LOGGING"** - Logging enabled, violations will be saved

### Logging Button
- **Green** = Logging disabled
- **Red** = Logging active

### Face Recognition Boxes
- **Magenta** = Known person (confidence > 60%)
- **Orange** = Unknown person
- Label shows: `FACE: Name (85.2%)`

### Compliance Boxes
- **Red** = Non-compliant item
- **Green** = Compliant item
- Label shows: `Item Name 0.95`

## 🔍 API Endpoints

### Logging Control

```javascript
// Toggle logging
POST /api/logging/toggle/
Response: {
  "success": true,
  "logging_enabled": true,
  "message": "Logging enabled"
}

// Get logging status
GET /api/logging/status/
Response: {
  "logging_enabled": false
}

// Enable/disable directly
POST /api/logging/enable/
POST /api/logging/disable/
```

## ⚙️ Configuration

### Face Recognition Threshold

Edit `utils/face_recognition_utils.py`:

```python
FACE_MATCH_THRESHOLD = 0.6  # Lower = stricter, Higher = more lenient
```

### Violation Logger

Edit `utils/violation_logger.py`:

```python
# Change log folder
def __init__(self, log_folder="non_compliance_logs"):

# Customize colors, box thickness, font sizes, etc.
```

## 🐛 Troubleshooting

### Redis Not Connected

```bash
# Test connection
python test_redis.py

# If fails, start Redis
redis-server

# Or check if Redis service is running
```

### No Faces Detected

- Ensure images in `database/` contain clear faces
- Re-run `python sync_faces.py`
- Check lighting conditions match camera
- Add more images per person (3-5 recommended)

### "Unknown" for Known People

- Add more training images
- Lower `FACE_MATCH_THRESHOLD` (try 0.7 or 0.8)
- Ensure training images match camera angle/lighting

### Performance Issues

- Face detection only runs when violations occur
- Only active when logging is enabled
- Redis provides fast cached lookups
- Consider limiting webcam resolution if needed

## 📊 Log File Format

### Text Log (`violation_log.txt`)

```
================================================================================
Violation logged: violation_20250125_143020_123.jpg
Timestamp: 2025-01-25 14:30:20

Non-Compliant Items:
  - Shorts
  - T-Shirt

Identified Persons:
  - Student Name (Confidence: 87.3%)
  - Unknown (Confidence: 45.2%)

All Detections:
  - Shorts: 0.92
  - T-Shirt: 0.88
  - ID Card: 0.76
```

## 🔒 Security & Privacy

- **Face encodings** stored in Redis (in-memory, not persistent by default)
- **Original photos** remain in `database/` folder
- **Violation logs** contain identified faces - secure this folder appropriately
- Consider **GDPR/privacy regulations** for face data storage
- Implement **access controls** on `non_compliance_logs/` folder
- Add **data retention policies** for violation logs

## ✅ Testing Checklist

- [ ] Redis is running (`python test_redis.py`)
- [ ] Database folder contains person subfolders with images
- [ ] Faces synced to Redis (`python sync_faces.py`)
- [ ] Backend running (`uvicorn main:app --reload`)
- [ ] Frontend shows "Start Logging" button
- [ ] Clicking button toggles between Start/Stop
- [ ] Webcam shows "DETECTING + LOGGING" when active
- [ ] Violations create files in `non_compliance_logs/`
- [ ] Saved frames have both compliance and face boxes
- [ ] Text log contains violation details

## 🎓 Usage Example

1. **Start Redis**: `redis-server`
2. **Sync faces**: `python sync_faces.py`
3. **Start backend**: `uvicorn main:app --reload`
4. **Open web interface**: http://localhost:8000
5. **Start webcam**: Click camera button
6. **Enable logging**: Click "Start Logging" in Actions panel
7. **Trigger violation**: Show non-compliant clothing to camera
8. **Check logs**: Open `non_compliance_logs/` folder
9. **View results**: See annotated frames with faces identified

## 📚 Additional Resources

- **Full documentation**: See `FACE_RECOGNITION.md`
- **Setup guide**: See `QUICKSTART.md`
- **API reference**: See `main.py` docstrings
- **Redis docs**: https://redis.io/docs/
- **face-recognition library**: https://github.com/ageitgey/face_recognition

## 🎉 Summary

Your DressGuard system now has:
- ✅ Real-time face detection and recognition
- ✅ Automated violation logging with timestamps
- ✅ Redis-backed fast face matching
- ✅ UI toggle for logging control
- ✅ Annotated frames with both compliance and face boxes
- ✅ Detailed text logs for audit trails
- ✅ Privacy-conscious database structure
- ✅ Easy-to-use sync system for adding new people

Everything is ready to use! Just follow the setup steps above.
