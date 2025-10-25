# 🚀 Quick Start Guide - DressGuard AI

## For First-Time Setup

### 1. Install Dependencies (5 minutes)

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..

# Root (optional)
npm install
```

### 2. Setup Environment Files (2 minutes)

**Backend (.env)**
```bash
cp .env.example .env
# Use default values or customize as needed
```

**Frontend (frontend/.env)**
```bash
cd frontend
cp .env.example .env
# Default: VITE_API_BASE=http://localhost:8000
cd ..
```

### 3. Add Model Files (1 minute)

Place your `.pt` model files in the `models/` directory:
- `models/best.pt`
- `models/Gen1.pt`
- `models/final.pt`

### 4. Start the Application (1 minute)

**Terminal 1 - Backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Application

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## For Network Access

### Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
Update `frontend/.env`:
```
VITE_API_BASE=http://YOUR_IP:8000
```

### Enable Webcam (Chrome/Edge)
1. Go to `chrome://flags`
2. Search: "insecure origins treated as secure"
3. Add: `http://YOUR_IP:5173`
4. Restart browser

---

## Common Commands

### Development
```bash
# Start backend with auto-reload
uvicorn main:app --reload

# Start frontend dev server
cd frontend && npm run dev

# Check for errors
python -m pytest

# Lint frontend code
cd frontend && npm run lint
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Start backend (production)
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Git Operations
```bash
# Check status
git status

# Commit changes
git add .
git commit -m "Your message"
git push

# Pull updates
git pull

# Create branch
git checkout -b feature/your-feature
```

---

## Testing the System

### 1. Health Check
Visit: http://localhost:8000/health/

Expected response:
```json
{
  "status": "healthy",
  "detector": "initialized",
  "current_model": "best",
  "available_models": ["best", "gen1", "final"]
}
```

### 2. Upload Image
1. Open frontend at http://localhost:5173
2. Click "Upload Image"
3. Select a test image
4. View detection results

### 3. Test Webcam
1. Click "Start Webcam"
2. Allow camera permissions
3. View real-time detections

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `ENOENT: no such file` | Run `npm install` in frontend |
| `Model file not found` | Add .pt files to models/ directory |
| `Port already in use` | Change port or stop existing process |
| `Webcam not working` | Check browser flags (see above) |

---

## Next Steps

- ✅ Customize compliance rules in `config.py`
- ✅ Add your own YOLO models
- ✅ Configure logging levels
- ✅ Deploy to production server
- ✅ Add authentication (if needed)

---

For detailed documentation, see [README.md](README.md)
