# 🛡️ DressGuard AI

AI-powered clothing compliance detection system using YOLOv8 for real-time dress code enforcement.

## 📋 Overview

DressGuard is a full-stack application that uses computer vision to detect and validate clothing items against predefined compliance rules. Built with FastAPI backend and React frontend, it supports real-time detection through webcam, uploaded images, and IP cameras.

## ✨ Features

- 🎯 **Multiple Detection Modes**: Image upload, webcam feed, video file, and IP camera support
- 🤖 **Multi-Model Support**: Switch between different YOLO models for varying speed/accuracy tradeoffs
- ✅ **Compliance Checking**: Automatic validation against configurable dress code rules
- � **Distance Checking**: Smart positioning guidance for webcam to ensure full outfit visibility
- �📊 **Real-time Visualization**: Live bounding box display with confidence scores
- 📝 **Detailed Logging**: Comprehensive logging system with rotation support
- 🚀 **RESTful API**: Well-documented FastAPI endpoints with automatic OpenAPI docs
- 🎨 **Modern UI**: Responsive React interface with professional SVG icons
- ⚡ **Performance Optimized**: Reduced backend stress with intelligent frame processing

## 🏗️ Architecture

```
DressGuard/
├── Backend (FastAPI + YOLOv8)
│   ├── main.py              # API endpoints
│   ├── detector.py          # YOLO detection logic
│   ├── config.py            # Configuration settings
│   └── utils/
│       ├── compliance.py    # Compliance checking logic
│       └── logger.py        # Logging configuration
│
└── Frontend (React + Vite)
    ├── src/
    │   ├── components/      # React components
    │   └── utils/          # Helper functions
    └── public/             # Static assets
```

## 🔧 Prerequisites

### Backend Requirements
- Python 3.8 or higher
- pip (Python package manager)
- CUDA 12.x (optional, for GPU acceleration)

### Frontend Requirements
- Node.js 16+ and npm
- Modern web browser

### Git Configuration
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🚀 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd DressGuard
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create models directory
mkdir models

# Add your YOLO model files (.pt) to the models folder
# Required models: best.pt, Gen1.pt, final.pt

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
# Update VITE_API_BASE if needed (default: http://localhost:8000)

cd ..
```

### 4. Root Directory Setup

```bash
# Install root dependencies (if needed)
npm install
```

## 🎮 Running the Application

### Start Backend Server

```bash
# Standard mode (localhost only)
uvicorn main:app --reload

# Network mode (accessible from other devices)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Local: `http://localhost:8000`
- Network: `http://<your-ip>:8000`
- API Docs: `http://localhost:8000/docs`

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- Local: `http://localhost:5173`
- Network: Check console output for network URL

## 📡 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| GET | `/health/` | Health check and system status |
| GET | `/models/` | List available detection models |
| GET | `/current-model/` | Get currently active model |
| POST | `/detect/` | Detect clothing in uploaded image |
| POST | `/switch-model/` | Switch to different detection model |

### Example API Usage

```python
# Detect clothing in image
import requests

with open('image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/detect/', files=files)
    print(response.json())

# Switch model
response = requests.post(
    'http://localhost:8000/switch-model/',
    json={'model_name': 'gen1'}
)
print(response.json())
```

## ⚙️ Configuration

### Dynamic Model Loading (No Configuration Needed!)

Models are **automatically discovered** from the `models/` folder. Just drop your `.pt` files and they'll be instantly available!

```bash
# Add a new model - that's it!
cp your_new_model.pt models/

# Restart backend (models are auto-discovered on startup)
uvicorn main:app --reload
```

**How it works:**
- Scans `models/` folder for all `.pt` files
- Automatically extracts class names from each model
- No hardcoding needed - just add/remove files!
- Model name = filename (without .pt extension)

**Example:**
```
models/
├── best.pt          → Available as "best" model
├── Gen1.pt          → Available as "Gen1" model  
├── final.pt         → Available as "final" model
└── custom_model.pt  → Available as "custom_model" model
```

### Compliance Rules (`config.py`)

Define compliant and non-compliant clothing:

```python
COMPLIANT_CLOTHES = {
    "full sleeve shirt",
    "pants",
    "id card"
}

NON_COMPLIANT_CLOTHES = {
    "t-shirt",
    "shorts"
}

COMPLIANCE_RULES = {
    "min_confidence": 0.5,
    "require_all_compliant": True
}
```

### Webcam Distance Checking (`config.py`)

Control distance validation and detection frequency:

```python
# Webcam Detection Settings
WEBCAM_ENABLE_DISTANCE_CHECK = True  # Enable distance/position checking
WEBCAM_JPEG_QUALITY = 80             # Video quality (0-100)
WEBCAM_FPS_LIMIT = 100               # Max FPS cap

# Distance Check Mode Switching
WEBCAM_REQUIRED_GOOD_FRAMES = 5      # Good frames needed to start real-time detection
WEBCAM_ALLOWED_BAD_FRAMES = 10       # Bad frames allowed before returning to distance check
```

**How It Works:**

The webcam has **two intelligent modes** that automatically switch based on positioning:

1. **Distance Check Mode** (Initial state)
   - Shows real-time guidance: "Step back", "Move closer", etc.
   - Displays progress bar when positioned correctly
   - No YOLO detection running (no lag)
   - Checks face position and body visibility

2. **Detection Mode** (Activated when properly positioned)
   - Switches automatically after 5 consecutive good frames
   - Runs **real-time YOLO detection** on every frame
   - Shows bounding boxes and compliance status
   - Returns to Distance Check Mode if you move out of range

**Benefits:**
- No lag during positioning - distance check is lightweight
- Smooth real-time detection once positioned
- Automatic mode switching based on your position
- Reduces backend load by not running YOLO when poorly positioned
- Visual feedback shows exactly when detection will start

## 🌐 Network Access Setup

### For Webcam Access over Network

Chrome/Edge requires special permissions for webcam access over HTTP (non-HTTPS):

1. Navigate to `chrome://flags` (or `edge://flags`)
2. Search for "insecure origins treated as secure"
3. Add your network URL (e.g., `http://192.168.1.100:5173`)
4. Click "Enable" and restart browser

### CORS Configuration

For production, update `main.py` to restrict origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Detection Flow

### Image Detection

1. User uploads image via frontend
2. Image previewed using `URL.createObjectURL()`
3. Image sent to `/detect/` endpoint
4. Backend runs YOLOv8 inference
5. Returns detections with bounding boxes and confidence scores
6. Frontend renders boxes scaled to displayed image size
7. Compliance check performed and results displayed

### Video/Webcam Detection

1. Video stream initialized in frontend
2. Frames captured at intervals
3. Each frame sent to `/detect/` endpoint
4. Real-time bounding boxes drawn on canvas overlay
5. Continuous compliance monitoring

## 🐛 Troubleshooting

### Common Issues

**Model file not found**
```
Error: Model file not found: models/best.pt
Solution: Ensure model files are in the models/ directory
```

**CUDA out of memory**
```
Solution: Reduce batch size or use CPU-only mode
Set ENABLE_GPU = False in config.py
```

**Canvas boxes misaligned**
```
Solution: Ensure canvas size matches rendered image size
Check drawBoxes.js scaling logic
```

**Webcam not accessible**
```
Solution: Check browser permissions and flags (see Network Access Setup)
```

## 📝 Development

### Project Structure

- `main.py` - FastAPI application and endpoints
- `detector.py` - YOLO model wrapper and detection logic
- `config.py` - Central configuration
- `utils/compliance.py` - Compliance validation logic
- `utils/logger.py` - Logging configuration
- `frontend/src/` - React application source
- `models/` - YOLO model files (.pt)

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Create pull request

### Code Style

- Python: Follow PEP 8
- JavaScript: ESLint configuration in `frontend/eslint.config.js`
- Use type hints in Python
- Add docstrings to functions

## 📈 Performance Optimization

- Use GPU for faster inference (CUDA required)
- Enable half-precision mode for compatible GPUs
- Adjust confidence thresholds to reduce false positives
- Use lighter models (gen1) for faster processing
- Implement result caching for repeated requests

## 🔒 Security Considerations

- Validate all file uploads (size, type, content)
- Sanitize user inputs
- Use environment variables for sensitive configuration
- Implement rate limiting in production
- Use HTTPS in production
- Restrict CORS origins in production

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

## 📄 License

[Add your license information here]

## 👥 Contributors

[Add contributor information here]

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Note**: Ensure you have proper authorization before using this system for compliance monitoring. Always respect privacy and local regulations.

