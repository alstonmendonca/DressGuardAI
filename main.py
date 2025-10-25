from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import numpy as np
import cv2
from detector import DressDetector
from utils.compliance import is_compliant, ComplianceManager
from utils.logger import setup_logging
from utils.cache import get_cache
from utils.distance_checker import get_distance_checker
from utils.model_discovery import get_model_discovery
from config import (MODELS_FOLDER, WEBCAM_DETECTION_INTERVAL, WEBCAM_ENABLE_DISTANCE_CHECK, 
                    WEBCAM_JPEG_QUALITY, WEBCAM_FPS_LIMIT, WEBCAM_REQUIRED_GOOD_FRAMES, 
                    WEBCAM_ALLOWED_BAD_FRAMES)
import logging
from typing import Optional, List
import os
from contextlib import asynccontextmanager
import asyncio
import time

# Setup logging with rotating file handler
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/dressguard.log")
setup_logging(log_level=log_level, log_file=log_file)

logger = logging.getLogger(__name__)

# Background task for cache cleanup
async def cleanup_task():
    """Periodic cache cleanup task"""
    cache = get_cache()
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        try:
            cache.cleanup_expired()
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting DressGuard API...")
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    logger.info("Shutting down DressGuard API...")
    cleanup_task_handle.cancel()
    try:
        await cleanup_task_handle
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="DressGuard API",
    description="AI-powered clothing compliance detection system",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize detector with error handling
try:
    detector = DressDetector()
    logger.info("DressDetector initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize DressDetector: {e}")
    detector = None

# Initialize compliance manager
compliance_manager = ComplianceManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "DressGuard API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "detect": "/detect/",
            "models": "/models/",
            "health": "/health/",
            "switch_model": "/switch-model/",
            "current_model": "/current-model/"
        }
    }

@app.get("/health/")
async def health_check():
    """Health check endpoint for monitoring"""
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "detector": "not initialized",
                "message": "Detector failed to initialize"
            }
        )
    
    model_discovery = get_model_discovery(MODELS_FOLDER)
    available_models = model_discovery.get_all_models()
    
    return {
        "status": "healthy",
        "detector": "initialized",
        "current_model": detector.current_model,
        "available_models": list(available_models.keys())
    }

@app.get("/models/")
async def get_available_models():
    """Get list of available models with their metadata (dynamically discovered)"""
    try:
        model_discovery = get_model_discovery(MODELS_FOLDER)
        models = model_discovery.get_all_models()
        
        models_info = []
        for model_id, model_data in models.items():
            models_info.append({
                "id": model_id,
                "path": model_data["path"],
                "classes": model_data["classes"],
                "class_count": model_data["class_count"],
                "is_current": model_id == detector.current_model if detector else False
            })
        
        return {
            "models": models_info,
            "current_model": detector.current_model if detector else None,
            "total": len(models_info)
        }
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.post("/detect/")
async def detect_dress(file: UploadFile = File(...), model: Optional[str] = None):
    """Detect clothing items in uploaded image"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    try:
        # Validate file extension
        file_ext = file.filename.split('.')[-1].lower()
        if f".{file_ext}" not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read and validate file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Decode image
        nparr = np.frombuffer(content, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to decode image")
        
        # Validate image dimensions
        h, w = image.shape[:2]
        if w < 50 or h < 50:
            raise HTTPException(status_code=400, detail="Image too small (minimum 50x50 pixels)")
        if w > 4096 or h > 4096:
            raise HTTPException(status_code=400, detail="Image too large (maximum 4096x4096 pixels)")

        # Switch model if specified
        if model and model != detector.current_model:
            success = detector.switch_model(model)
            if not success:
                logger.warning(f"Failed to switch to model: {model}")

        # Perform detection
        detected_clothes = detector.detect(image)
        
        # Check compliance using the compliance manager
        compliant, non_compliant_items, compliance_details = compliance_manager.check_compliance(detected_clothes)
        
        logger.info(f"Detection complete: {len(detected_clothes)} items found, compliant: {compliant}")

        return {
            "clothes_detected": detected_clothes,
            "image_width": w,
            "image_height": h,
            "compliant": compliant,
            "non_compliant_items": non_compliant_items,
            "compliance_details": compliance_details,
            "model_used": detector.current_model,
            "total_detections": len(detected_clothes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.post("/switch-model/")
async def switch_model(model_name: str = Body(..., embed=True)):
    """Switch to a different detection model (dynamically discovered)"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    try:
        logger.info(f"Received model switch request: '{model_name}'")
        
        # Check if model exists using model discovery
        model_discovery = get_model_discovery(MODELS_FOLDER)
        available_models = model_discovery.get_all_models()
        
        # Find model with case-insensitive match
        matched_model_id = None
        for model_id in available_models.keys():
            if model_id.lower() == model_name.lower():
                matched_model_id = model_id
                break
        
        if not matched_model_id:
            logger.warning(f"Model '{model_name}' not found in available models")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model '{model_name}'. Available models: {', '.join(available_models.keys())}"
            )
        
        logger.info(f"Matched model: '{model_name}' -> '{matched_model_id}'")
        success = detector.switch_model(matched_model_id)
        
        if success:
            logger.info(f"Successfully switched to model: {matched_model_id}")
            return {
                "success": True,
                "current_model": detector.current_model,
                "message": f"Successfully switched to {detector.current_model}"
            }
        else:
            logger.error(f"Failed to switch to model: {matched_model_id}")
            raise HTTPException(
                status_code=500,
                detail="Model switch failed. Check server logs for details."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model switch error: {str(e)}")

@app.get("/current-model/")
async def get_current_model():
    """Get the currently active model"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    # Get model info from dynamic discovery
    model_discovery = get_model_discovery(MODELS_FOLDER)
    model_info = model_discovery.get_model_info(detector.current_model)
    
    return {
        "current_model": detector.current_model,
        "model_info": model_info if model_info else {}
    }

@app.get("/stats/")
async def get_stats():
    """Get system statistics including cache and performance metrics"""
    cache = get_cache()
    cache_stats = cache.get_stats()
    cache_size = cache.get_size_estimate()
    
    return {
        "cache": {
            **cache_stats,
            "size_bytes": cache_size,
            "size_mb": round(cache_size / (1024 * 1024), 2)
        },
        "detector": {
            "initialized": detector is not None,
            "current_model": detector.current_model if detector else None,
            "available_models": len(model_discovery.get_all_models())
        }
    }

@app.post("/cache/clear/")
async def clear_cache():
    """Clear the API cache"""
    try:
        cache = get_cache()
        cache.clear()
        logger.info("Cache cleared via API request")
        return {
            "success": True,
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Compliance Configuration Endpoints
# ============================================================================

@app.get("/compliance/config/")
async def get_compliance_config():
    """Get current compliance configuration filtered by current model's classes"""
    config = compliance_manager.get_config()
    
    # Filter to only include classes from the current model
    if detector and hasattr(detector.model, 'names'):
        current_model_classes = set(c.lower() for c in detector.model.names.values())
        
        # Filter compliant and non-compliant classes
        config["compliant_classes"] = [
            c for c in config["compliant_classes"] 
            if c in current_model_classes
        ]
        config["non_compliant_classes"] = [
            c for c in config["non_compliant_classes"] 
            if c in current_model_classes
        ]
    
    return config

@app.post("/compliance/config/")
async def update_compliance_config(
    compliant_classes: List[str] = Body(...),
    non_compliant_classes: List[str] = Body(...),
    min_confidence: Optional[float] = Body(0.5)
):
    """
    Update compliance configuration
    
    Args:
        compliant_classes: List of approved clothing items
        non_compliant_classes: List of prohibited clothing items
        min_confidence: Minimum confidence threshold (0-1)
    """
    try:
        # Normalize all class names
        compliant_set = set(c.lower().strip() for c in compliant_classes)
        non_compliant_set = set(c.lower().strip() for c in non_compliant_classes)
        
        # Remove any duplicates - if a class is in both lists, keep it in non-compliant
        # This ensures safety: we'd rather flag something as non-compliant than miss it
        overlap = compliant_set & non_compliant_set
        if overlap:
            logger.warning(f"Classes in both lists (keeping in non-compliant): {overlap}")
            compliant_set -= overlap
        
        # Update the configuration
        compliance_manager.compliant_classes = compliant_set
        compliance_manager.non_compliant_classes = non_compliant_set
        compliance_manager.min_confidence = min_confidence
        compliance_manager.save_config()
        
        logger.info(f"Compliance config updated: {len(compliant_set)} compliant, "
                   f"{len(non_compliant_set)} non-compliant, "
                   f"{len(overlap)} duplicates removed")
        
        return {
            "success": True,
            "message": "Compliance configuration updated",
            "duplicates_removed": list(overlap) if overlap else [],
            "config": compliance_manager.get_config()
        }
    except Exception as e:
        logger.error(f"Error updating compliance config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compliance/add-compliant/")
async def add_compliant_class(class_name: str = Body(..., embed=True)):
    """Add a class to the compliant list"""
    try:
        compliance_manager.add_compliant_class(class_name)
        return {
            "success": True,
            "message": f"Added '{class_name}' to compliant classes",
            "config": compliance_manager.get_config()
        }
    except Exception as e:
        logger.error(f"Error adding compliant class: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compliance/add-non-compliant/")
async def add_non_compliant_class(class_name: str = Body(..., embed=True)):
    """Add a class to the non-compliant list"""
    try:
        compliance_manager.add_non_compliant_class(class_name)
        return {
            "success": True,
            "message": f"Added '{class_name}' to non-compliant classes",
            "config": compliance_manager.get_config()
        }
    except Exception as e:
        logger.error(f"Error adding non-compliant class: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compliance/remove-class/")
async def remove_class(class_name: str = Body(..., embed=True)):
    """Remove a class from both compliant and non-compliant lists"""
    try:
        compliance_manager.remove_class(class_name)
        return {
            "success": True,
            "message": f"Removed '{class_name}' from compliance lists",
            "config": compliance_manager.get_config()
        }
    except Exception as e:
        logger.error(f"Error removing class: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compliance/detected-classes/")
async def get_all_detected_classes():
    """Get list of all unique classes across all models or current model"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    try:
        # Get model discovery instance
        model_discovery = get_model_discovery(MODELS_FOLDER)
        
        # Get all unique classes across all models
        all_classes = model_discovery.get_all_unique_classes()
        
        # Get classes from current model
        current_model_classes = []
        if hasattr(detector.model, 'names'):
            current_model_classes = list(detector.model.names.values())
        
        return {
            "classes": sorted(all_classes),  # All unique classes across all models
            "current_model_classes": sorted(current_model_classes),  # Current model only
            "count": len(all_classes),
            "current_model": detector.current_model
        }
    except Exception as e:
        logger.error(f"Error getting detected classes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Global variable to control webcam stream
webcam_active = False
webcam_cap = None

def generate_webcam_frames():
    """Generate MJPEG frames from webcam with YOLO detection and distance checking"""
    global webcam_cap, webcam_active
    
    # Initialize webcam
    webcam_cap = cv2.VideoCapture(0)
    
    if not webcam_cap.isOpened():
        logger.error("Could not open webcam")
        yield b''
        return
    
    # Set webcam properties for better performance
    webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    webcam_cap.set(cv2.CAP_PROP_FPS, 30)
    webcam_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
    
    logger.info("Webcam stream started with distance checking")
    webcam_active = True
    
    # Get distance checker instance (only if enabled)
    distance_checker = get_distance_checker() if WEBCAM_ENABLE_DISTANCE_CHECK else None
    
    # State management
    detection_mode = False  # False = distance checking, True = real-time detection
    consecutive_good_frames = 0
    consecutive_bad_frames = 0
    required_good_frames = WEBCAM_REQUIRED_GOOD_FRAMES
    allowed_bad_frames = WEBCAM_ALLOWED_BAD_FRAMES
    
    # Frame processing control
    frame_count = 0
    last_detection_time = time.time()
    
    # JPEG encoding parameters for better performance
    encode_params = [
        cv2.IMWRITE_JPEG_QUALITY, WEBCAM_JPEG_QUALITY,
        cv2.IMWRITE_JPEG_OPTIMIZE, 1    # Optimize encoding
    ]
    
    # FPS control
    frame_delay = 1.0 / WEBCAM_FPS_LIMIT if WEBCAM_FPS_LIMIT > 0 else 0.01
    
    try:
        while webcam_active:
            ret, frame = webcam_cap.read()
            
            if not ret:
                logger.warning("Failed to grab webcam frame")
                break
            
            try:
                frame_count += 1
                current_time = time.time()
                annotated_frame = frame.copy()
                
                if distance_checker:
                    # Check distance on every frame (lightweight)
                    distance_result = distance_checker.check_distance(frame)
                    
                    # Mode switching logic
                    if distance_result["should_process"]:
                        consecutive_good_frames += 1
                        consecutive_bad_frames = 0
                        
                        # Switch to detection mode after enough good frames
                        if not detection_mode and consecutive_good_frames >= required_good_frames:
                            detection_mode = True
                            logger.info("Switched to DETECTION MODE - Real-time processing started")
                    else:
                        consecutive_bad_frames += 1
                        consecutive_good_frames = 0
                        
                        # Switch back to distance mode after too many bad frames
                        if detection_mode and consecutive_bad_frames >= allowed_bad_frames:
                            detection_mode = False
                            logger.info("Switched to DISTANCE CHECK MODE - Repositioning required")
                    
                    # DETECTION MODE: Real-time YOLO detection on every frame
                    if detection_mode:
                        # Run YOLO detection continuously
                        results = detector.detect(frame, confidence_threshold=0.6)
                        
                        # Check compliance
                        is_compliant, non_compliant_items, compliance_details = compliance_manager.check_compliance(results)
                        
                        # Draw bounding boxes
                        annotated_frame = draw_detections_on_frame(annotated_frame, results)
                        
                        # Small status indicator
                        cv2.putText(annotated_frame, "DETECTING", (10, 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # DISTANCE CHECK MODE: Show guidance, no detection
                    else:
                        # Draw distance feedback
                        annotated_frame = distance_checker.draw_distance_feedback(
                            annotated_frame, 
                            distance_result
                        )
                        
                        # Show progress bar for mode switching
                        if consecutive_good_frames > 0:
                            progress = min(100, int((consecutive_good_frames / required_good_frames) * 100))
                            bar_width = 200
                            bar_height = 20
                            bar_x = (annotated_frame.shape[1] - bar_width) // 2
                            bar_y = annotated_frame.shape[0] - 50
                            
                            # Background
                            cv2.rectangle(annotated_frame, (bar_x, bar_y), 
                                        (bar_x + bar_width, bar_y + bar_height), 
                                        (50, 50, 50), -1)
                            # Progress
                            cv2.rectangle(annotated_frame, (bar_x, bar_y), 
                                        (bar_x + int(bar_width * progress / 100), bar_y + bar_height), 
                                        (0, 255, 0), -1)
                            # Text
                            cv2.putText(annotated_frame, f"Starting detection: {progress}%", 
                                      (bar_x, bar_y - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                else:
                    # Distance checker disabled - always run detection
                    results = detector.detect(frame, confidence_threshold=0.6)
                    is_compliant, non_compliant_items, compliance_details = compliance_manager.check_compliance(results)
                    annotated_frame = draw_detections_on_frame(annotated_frame, results)
                
                # Encode frame as JPEG with optimized parameters
                ret, buffer = cv2.imencode('.jpg', annotated_frame, encode_params)
                
                if not ret:
                    continue
                
                frame_bytes = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Dynamic frame rate control
                time.sleep(frame_delay)

                
            except Exception as e:
                logger.error(f"Error processing webcam frame: {e}")
                continue
                
    finally:
        if webcam_cap is not None:
            webcam_cap.release()
            webcam_cap = None
        webcam_active = False
        logger.info("Webcam stream stopped")

def draw_detections_on_frame(frame, detections, compliance_info=None):
    """Draw bounding boxes and labels on frame with compliance color coding
    
    Note: compliance_info parameter is kept for compatibility but not used for banner.
    Color coding is determined by checking compliance_manager directly.
    """
    annotated_frame = frame.copy()
    
    # Determine which classes are compliant/non-compliant for color coding
    compliant_classes = compliance_manager.compliant_classes
    non_compliant_classes = compliance_manager.non_compliant_classes
    
    for det in detections:
        class_name = det['class']
        class_name_lower = class_name.lower().strip()
        confidence = det['confidence']
        bbox = det['bbox']
        
        x1, y1, x2, y2 = map(int, bbox)
        
        # Determine color based on compliance status
        if class_name_lower in non_compliant_classes:
            color = (0, 0, 255)  # Red for non-compliant (BGR format)
            status = "NON-COMPLIANT"
        elif class_name_lower in compliant_classes:
            color = (0, 255, 0)  # Green for compliant
            status = "COMPLIANT"
        else:
            color = (255, 165, 0)  # Orange for neutral/unknown
            status = "NEUTRAL"
        
        # Draw rectangle
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw label with background
        label = f"{class_name}: {confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        
        # Draw background rectangle
        cv2.rectangle(annotated_frame, 
                     (x1, y1 - text_height - 10), 
                     (x1 + text_width, y1), 
                     color, -1)
        
        # Draw text
        cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                   font, font_scale, (255, 255, 255), thickness)
    
    return annotated_frame

@app.get("/webcam/stream/")
async def webcam_stream():
    """Stream webcam feed with real-time YOLO detection (MJPEG format)"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    return StreamingResponse(
        generate_webcam_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.post("/webcam/stop/")
async def stop_webcam():
    """Stop the webcam stream"""
    global webcam_active
    webcam_active = False
    
    return {"success": True, "message": "Webcam stream stopped"}