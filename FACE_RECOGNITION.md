# Face Recognition Integration

DressGuard now includes face recognition capabilities to identify individuals when compliance violations are detected.

## Prerequisites

1. **Redis Server** - Download and install from [GitHub Releases](https://github.com/microsoftarchive/redis/releases)
   - During installation, check "Add Redis to PATH"
   
2. **CMake** - Download from [cmake.org](https://cmake.org/download/)
   - Required for building dlib
   
3. **Python Dependencies** - Already included in `requirements.txt`:
   ```
   face-recognition==1.3.0
   dlib==19.24.6
   redis==5.2.1
   ```

## Setup Instructions

### 1. Install Dependencies

If you haven't already, install all Python dependencies:

```bash
pip install -r requirements.txt
```

Or install face recognition modules individually:

```bash
pip install dlib --only-binary=all
pip install face-recognition
pip install redis
```

### 2. Start Redis Server

Make sure Redis is running before starting the application:

```bash
# Windows (if added to PATH)
redis-server

# Or start from Redis installation directory
```

### 3. Prepare Face Database

Create a `database` folder in the project root with subfolders for each person:

```
DressGuard/
├── database/
│   ├── Student1/
│   │   ├── 0.jpg
│   │   ├── 1.jpg
│   │   └── 2.jpg
│   ├── Student2/
│   │   ├── 0.jpg
│   │   └── 1.jpg
│   └── Student3/
│       ├── 0.jpg
│       ├── 1.jpg
│       └── 2.jpg
```

**Requirements:**
- Each subfolder name = person's name
- Images should be numbered: 0.jpg, 1.jpg, 2.jpg, etc.
- Images should contain clear, front-facing photos
- Multiple images per person improve accuracy

### 4. Sync Faces to Redis

Run the synchronization script to load faces into Redis:

```bash
python sync_faces.py
```

This will:
- Process all images in the database folder
- Extract face encodings
- Store them in Redis for fast lookup
- Print progress and statistics

### 5. Start the Application

Start the backend server:

```bash
uvicorn main:app --reload
```

## How It Works

### Violation Logging

1. **Enable Logging** - Click the "Start Logging" button in the Actions panel
2. **Detect Violations** - When non-compliant items are detected
3. **Face Detection** - System automatically detects and identifies faces
4. **Save Evidence** - Frames are saved to `non_compliance_logs/` with:
   - Compliance violation boxes (red for non-compliant items)
   - Face detection boxes (magenta for recognized, orange for unknown)
   - Timestamp and metadata overlay
   - Identified persons list

### Log Files

Violation logs are saved in `non_compliance_logs/`:

```
non_compliance_logs/
├── violation_20250125_143020_123.jpg  # Annotated frame
├── violation_20250125_143025_456.jpg
└── violation_log.txt                  # Text log with details
```

Each violation log includes:
- Timestamp
- Non-compliant items detected
- Identified persons with confidence scores
- All clothing detections

### Face Recognition Confidence

- **Green box** = Known person (confidence > 60%)
- **Orange box** = Unknown person (confidence ≤ 60%)
- Confidence score displayed on each face box

## Usage Tips

### Adding New People

1. Create a new folder in `database/` with the person's name
2. Add multiple clear photos (numbered 0.jpg, 1.jpg, etc.)
3. Run `python sync_faces.py` to update the database
4. Restart the application

### Updating Existing People

1. Add/remove photos from their folder in `database/`
2. Run `python sync_faces.py`
3. Old encodings are automatically replaced

### Best Practices

- **Image Quality**: Use clear, well-lit photos
- **Multiple Angles**: Include 3-5 photos per person from different angles
- **Similar Conditions**: Photos should match expected camera conditions
- **Regular Updates**: Re-sync if people change appearance significantly

## Troubleshooting

### Redis Connection Errors

```bash
# Check if Redis is running
redis-cli ping
# Should respond with "PONG"
```

If Redis isn't running:
```bash
redis-server
```

### No Faces Detected

- Check image quality in database folder
- Ensure faces are clearly visible
- Try adding more images per person
- Re-run `python sync_faces.py`

### "Unknown" Faces for Known People

- Lower confidence threshold in `utils/face_recognition_utils.py`:
  ```python
  FACE_MATCH_THRESHOLD = 0.6  # Try 0.7 or 0.8
  ```
- Add more training images
- Ensure training images match camera conditions

### Performance Issues

If face detection slows down the system:
- Face detection only runs when violations are detected
- Only occurs when logging is enabled
- Redis caching provides fast lookups

## API Endpoints

### Logging Control

```
POST /api/logging/toggle/   # Toggle logging on/off
GET  /api/logging/status/   # Get current logging status
POST /api/logging/enable/   # Enable logging
POST /api/logging/disable/  # Disable logging
```

### Example Response

```json
{
  "success": true,
  "logging_enabled": true,
  "message": "Logging enabled"
}
```

## Configuration

### Face Recognition Settings

Edit `utils/face_recognition_utils.py`:

```python
# Adjust face matching threshold (0.0 to 1.0)
FACE_MATCH_THRESHOLD = 0.6  # Lower = stricter matching
```

### Violation Logger Settings

Edit `utils/violation_logger.py` to customize:
- Log folder path
- Frame annotation style
- Metadata overlay format
- Box colors and thickness

## Testing

### Test Face Recognition Standalone

Process a folder of test images:

```bash
python utils/face_recognition_utils.py
```

Edit the `main()` function to specify your test folder.

## Security Notes

- Face encodings are stored in Redis (in-memory)
- Original photos remain in `database/` folder
- Violation logs contain identified faces - secure this folder
- Consider GDPR/privacy regulations for face data storage

## Support

For issues or questions:
1. Check Redis is running: `redis-cli ping`
2. Verify database folder structure
3. Re-sync faces: `python sync_faces.py`
4. Check logs: `logs/dressguard.log`
