# 🛠️ Development Guide - DressGuard AI

## Project Overview

DressGuard is a full-stack AI application for clothing compliance detection using YOLOv8 computer vision models.

**Tech Stack:**
- **Backend**: Python, FastAPI, YOLOv8, OpenCV
- **Frontend**: React, Vite, Tailwind CSS
- **Models**: PyTorch, Ultralytics YOLOv8

---

## Development Setup

### Prerequisites
```bash
# Check versions
python --version  # 3.8+
node --version    # 16+
git --version     # 2.0+
```

### Initial Setup
```bash
# Clone and navigate
git clone <repo-url>
cd DressGuard

# Backend
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd frontend
npm install
cp .env.example .env
cd ..
```

---

## Code Structure

### Backend Architecture

```
Backend/
├── main.py              # FastAPI app, endpoints, middleware
├── detector.py          # YOLO model wrapper
├── config.py            # Configuration settings
└── utils/
    ├── compliance.py    # Compliance validation logic
    └── logger.py        # Logging configuration
```

**Key Components:**

1. **main.py** - API Layer
   - Endpoint definitions
   - Request validation
   - Error handling
   - CORS configuration

2. **detector.py** - Model Layer
   - Model loading and switching
   - Inference execution
   - Result processing

3. **compliance.py** - Business Logic
   - Rule application
   - Validation logic
   - Reporting

### Frontend Architecture

```
Frontend/
├── src/
│   ├── App.jsx              # Main component
│   ├── components/
│   │   ├── CameraPanel.jsx  # Camera controls
│   │   ├── ModelPanel.jsx   # Model selection
│   │   ├── StatusPanel.jsx  # Compliance status
│   │   └── ...
│   └── utils/
│       ├── drawBoxes.js     # Canvas drawing
│       └── detectFrame.js   # Frame processing
```

---

## Adding Features

### Add a New Model

1. **Place model file** in `models/` directory:
   ```bash
   models/your_model.pt
   ```

2. **Update config.py**:
   ```python
   MODELS = {
       "your_model": {
           "path": "models/your_model.pt",
           "display_name": "Your Model Name",
           "description": "Model description"
       }
   }
   ```

3. **Update frontend** (`ModelPanel.jsx`):
   ```jsx
   {
       id: "your_model",
       name: "Your Model Name",
       available: true,
       description: "Model description"
   }
   ```

### Add a New API Endpoint

1. **Define endpoint** in `main.py`:
   ```python
   @app.get("/your-endpoint/")
   async def your_endpoint():
       try:
           # Your logic
           return {"data": "result"}
       except Exception as e:
           logger.error(f"Error: {e}")
           raise HTTPException(status_code=500, detail=str(e))
   ```

2. **Update documentation**:
   - Add to README.md API Endpoints section
   - Update root endpoint info

3. **Frontend integration**:
   ```javascript
   const response = await fetch('/api/your-endpoint/');
   const data = await response.json();
   ```

### Modify Compliance Rules

1. **Update config.py**:
   ```python
   COMPLIANT_CLOTHES.add("new_item")
   NON_COMPLIANT_CLOTHES.add("prohibited_item")
   ```

2. **Test changes**:
   ```bash
   # Run with test image
   python -c "from utils.compliance import is_compliant; ..."
   ```

---

## Testing

### Manual Testing

**Backend Health Check:**
```bash
curl http://localhost:8000/health/
```

**Test Detection:**
```bash
curl -X POST -F "file=@test_image.jpg" http://localhost:8000/detect/
```

**Test Model Switch:**
```bash
curl -X POST http://localhost:8000/switch-model/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "gen1"}'
```

### Automated Testing (Future)

```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend && npm test

# Coverage report
pytest --cov=. tests/
```

---

## Debugging

### Backend Debugging

**Enable DEBUG logging:**
```python
# In .env or main.py
LOG_LEVEL=DEBUG
```

**View logs:**
```bash
tail -f logs/dressguard.log
```

**Common Issues:**

| Issue | Debug Steps |
|-------|------------|
| Model not loading | Check file exists, check logs, verify path |
| Low accuracy | Adjust confidence threshold, try different model |
| Slow inference | Enable GPU, use lighter model, reduce image size |

### Frontend Debugging

**Console logging:**
```javascript
console.log('Detection results:', detections);
```

**Network tab:**
- Check API calls in browser DevTools
- Verify request/response payloads
- Check for CORS errors

**Common Issues:**

| Issue | Debug Steps |
|-------|------------|
| Canvas misalignment | Check image dimensions, verify scaling |
| No detections | Check API response, verify image upload |
| Webcam not working | Check permissions, browser flags |

---

## Performance Optimization

### Backend

1. **Enable GPU:**
   ```python
   # config.py
   ENABLE_GPU = True
   ```

2. **Adjust confidence threshold:**
   ```python
   DEFAULT_CONFIDENCE_THRESHOLD = 0.3  # Lower = more detections
   ```

3. **Use lighter models:**
   ```python
   DEFAULT_MODEL = "gen1"  # Faster but less accurate
   ```

### Frontend

1. **Reduce detection frequency:**
   ```javascript
   const DETECTION_UPDATE_INTERVAL = 1000; // ms between detections
   ```

2. **Optimize image size:**
   ```javascript
   // Resize before sending to API
   canvas.toBlob(blob => {...}, 'image/jpeg', 0.8);
   ```

---

## Code Style

### Python (Backend)

**Follow PEP 8:**
```python
# Good
def detect_clothing(image: np.ndarray) -> list:
    """Detect clothing items in image."""
    pass

# Bad
def detectClothing(img):
    pass
```

**Use type hints:**
```python
from typing import List, Dict, Optional

def process_results(data: List[Dict]) -> Optional[Dict]:
    pass
```

**Docstrings:**
```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        bool: Description of return value
    """
    pass
```

### JavaScript (Frontend)

**Follow ESLint config:**
```javascript
// Use const/let, not var
const API_BASE = '/api';

// Use arrow functions
const fetchData = async () => {
    // implementation
};

// Destructure props
export default function Component({ prop1, prop2 }) {
    // implementation
}
```

---

## Git Workflow

### Branch Strategy

```bash
# Feature branch
git checkout -b feature/new-feature

# Bug fix
git checkout -b fix/bug-description

# Enhancement
git checkout -b enhance/improvement
```

### Commit Messages

**Format:**
```
<type>: <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Examples:**
```bash
feat: Add batch processing endpoint

Implement /batch-detect/ endpoint to process multiple images
in a single request.

Closes #123

fix: Resolve canvas scaling issue

Update drawBoxes to use naturalWidth for accurate scaling.

docs: Update README with API examples

chore: Update dependencies
```

### Pre-commit Checklist

- [ ] Code follows style guide
- [ ] No console.log in production code
- [ ] Updated documentation if needed
- [ ] Tested changes locally
- [ ] No sensitive data in commits
- [ ] .gitignore is up to date

---

## Deployment

### Production Checklist

- [ ] Set CORS to specific origins
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set appropriate log levels
- [ ] Configure file size limits
- [ ] Add rate limiting
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Test on production-like environment

### Environment Variables

**Production .env:**
```bash
# Security
ALLOWED_ORIGINS=https://yourdomain.com
SECRET_KEY=your-secret-key

# Performance
LOG_LEVEL=WARNING
ENABLE_GPU=True
CACHE_ENABLED=True

# Limits
MAX_FILE_SIZE_MB=5
```

---

## Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [React Docs](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [VS Code](https://code.visualstudio.com/) - IDE
- [GitHub Desktop](https://desktop.github.com/) - Git GUI

### Community
- GitHub Issues - Bug reports and feature requests
- Project Wiki - Detailed documentation
- Team Chat - Development discussions

---

## Support

For development questions:
1. Check this guide
2. Review README.md
3. Check CHANGELOG.md
4. Search existing issues
5. Ask the team

Happy coding! 🚀
