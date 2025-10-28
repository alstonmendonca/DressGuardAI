from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import numpy as np
import cv2
from detector import DressDetector
from utils.compliance import is_compliant, ComplianceManager
from utils.logger import setup_logging
from utils.cache import get_cache
from utils.model_discovery import get_model_discovery
from utils.visibility_checker import get_visibility_checker
from utils.violation_logger import get_violation_logger
from utils.face_recognition_insightface import detect_and_identify_faces
from config import (MODELS_FOLDER, WEBCAM_DETECTION_INTERVAL,
                    WEBCAM_JPEG_QUALITY, WEBCAM_FPS_LIMIT, 
                    WEBCAM_SKIP_FRAMES)
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

# Initialize violation logger
violation_logger = get_violation_logger()

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

@app.get("/device/")
async def get_device_info():
    """Get information about the device being used for inference (GPU/CPU)"""
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={"error": "Detector not initialized"}
        )
    
    device_info = detector.get_device_info()
    
    # Add face detection device info
    try:
        from utils.face_recognition_insightface import get_face_app
        face_app = get_face_app()
        if face_app:
            # Check if using GPU or CPU
            face_device = "CPU"
            try:
                # InsightFace uses ONNX Runtime providers
                import onnxruntime as ort
                providers = ort.get_available_providers()
                if 'CUDAExecutionProvider' in providers:
                    face_device = "GPU (CUDA)"
                elif 'CPUExecutionProvider' in providers:
                    face_device = "CPU"
            except:
                face_device = "CPU"
            
            device_info["face_detection_device"] = face_device
        else:
            device_info["face_detection_device"] = "Not initialized"
    except ImportError:
        # Fallback to old face_recognition (always CPU)
        device_info["face_detection_device"] = "CPU (dlib)"
    
    return device_info

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

# ============================================================================
# Violation Logging Endpoints
# ============================================================================

@app.post("/logging/toggle/")
async def toggle_logging():
    """Toggle violation logging on/off"""
    try:
        new_state = violation_logger.toggle_logging()
        return {
            "success": True,
            "logging_enabled": new_state,
            "message": f"Logging {'enabled' if new_state else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Error toggling logging: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logging/status/")
async def get_logging_status():
    """Get current logging status with statistics"""
    stats = violation_logger.get_stats()
    return {
        "logging_enabled": violation_logger.is_logging_enabled(),
        "cooldown_seconds": stats["cooldown_seconds"],
        "active_violations": stats["active_violations"],
        "log_folder": stats["log_folder"]
    }

@app.get("/logging/stats/")
async def get_logging_stats():
    """Get detailed logging statistics"""
    return violation_logger.get_stats()

@app.post("/logging/cooldown/")
async def set_logging_cooldown(cooldown_seconds: int = Body(..., embed=True)):
    """Set the cooldown period between violation logs"""
    try:
        if cooldown_seconds < 1:
            raise HTTPException(status_code=400, detail="Cooldown must be at least 1 second")
        if cooldown_seconds > 300:
            raise HTTPException(status_code=400, detail="Cooldown cannot exceed 300 seconds (5 minutes)")
        
        violation_logger.set_cooldown(cooldown_seconds)
        return {
            "success": True,
            "cooldown_seconds": cooldown_seconds,
            "message": f"Cooldown set to {cooldown_seconds} seconds"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting cooldown: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/logging/enable/")
async def enable_logging():
    """Enable violation logging"""
    violation_logger.enable_logging()
    return {
        "success": True,
        "logging_enabled": True,
        "message": "Logging enabled"
    }

@app.post("/logging/disable/")
async def disable_logging():
    """Disable violation logging"""
    violation_logger.disable_logging()
    return {
        "success": True,
        "logging_enabled": False,
        "message": "Logging disabled"
    }

# ============================================================================
# Webcam Stream Endpoints
# ============================================================================

# Global variable to control webcam stream
webcam_active = False
webcam_cap = None
selected_camera_index = 0  # Default to camera 0

@app.get("/cameras/list/")
async def list_cameras():
    """List available cameras on the system"""
    available_cameras = []
    
    # Try to detect up to 10 cameras
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Get camera name/info if available
            ret, frame = cap.read()
            if ret:
                available_cameras.append({
                    "index": i,
                    "name": f"Camera {i}",
                    "resolution": f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
                })
            cap.release()
    
    logger.info(f"Found {len(available_cameras)} cameras")
    return {"cameras": available_cameras}

@app.post("/cameras/select/")
async def select_camera(camera_index: int = Body(..., embed=True)):
    """Select which camera to use for streaming"""
    global selected_camera_index, webcam_active, webcam_cap
    
    # Validate camera index
    test_cap = cv2.VideoCapture(camera_index)
    if not test_cap.isOpened():
        test_cap.release()
        raise HTTPException(status_code=400, detail=f"Camera {camera_index} not available")
    test_cap.release()
    
    # Stop current stream if active
    if webcam_active:
        webcam_active = False
        if webcam_cap is not None:
            webcam_cap.release()
            webcam_cap = None
        await asyncio.sleep(0.5)  # Give time for stream to stop
    
    # Update selected camera
    selected_camera_index = camera_index
    logger.info(f"Selected camera index: {camera_index}")
    
    return {
        "success": True, 
        "message": f"Camera {camera_index} selected",
        "camera_index": camera_index
    }

def generate_webcam_frames():
    """Generate MJPEG frames from webcam with YOLO detection and distance checking"""
    global webcam_cap, webcam_active, selected_camera_index
    
    # Initialize webcam with selected camera index
    webcam_cap = cv2.VideoCapture(selected_camera_index)
    
    if not webcam_cap.isOpened():
        logger.error("Could not open webcam")
        yield b''
        return
    
    # Set webcam properties for better performance
    webcam_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    webcam_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    webcam_cap.set(cv2.CAP_PROP_FPS, 30)
    webcam_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag
    
    logger.info("Webcam stream started")
    webcam_active = True
    
    # Frame processing control
    frame_count = 0
    logged_persons = set()  # Track logged persons in current session
    last_face_detection_time = 0
    face_detection_interval = 7.0  # Run face detection every 5 seconds
    current_status = "LOADING"  # Track current operation status
    last_logged_time = {}  # Track when each person was last logged {name: timestamp}
    session_reset_timeout = 20.0  # Reset session tracking after 20 seconds of inactivity
    multiple_people_warning_time = 0  # Track when multiple people warning was shown
    multiple_people_warning_duration = 3.0  # Show warning for 3 seconds
    
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
            
            # Frame skipping for performance (optional)
            if WEBCAM_SKIP_FRAMES > 0 and frame_count % (WEBCAM_SKIP_FRAMES + 1) != 0:
                frame_count += 1
                continue
            
            try:
                frame_count += 1
                current_time = time.time()
                annotated_frame = frame.copy()
                
                # Reset session tracking if person hasn't been seen for a while
                expired_persons = []
                for person_name, last_time in last_logged_time.items():
                    if current_time - last_time > session_reset_timeout:
                        expired_persons.append(person_name)
                
                for person_name in expired_persons:
                    if person_name in logged_persons:
                        logged_persons.remove(person_name)
                        del last_logged_time[person_name]
                        logger.info(f"Session reset for {person_name} - can be logged again if they return")
                
                # Set initial status
                current_status = "DETECTING"
                
                # Always run YOLO detection
                results = detector.detect(frame, confidence_threshold=0.6)
                is_compliant, non_compliant_items, compliance_details = compliance_manager.check_compliance(results)
                
                # Simple face detection every 5 seconds
                if not is_compliant and violation_logger.is_logging_enabled():
                    # Run face detection every 5 seconds
                    if current_time - last_face_detection_time >= face_detection_interval:
                        current_status = "SCANNING FACE..."
                        last_face_detection_time = current_time
                        
                        # Convert frame to RGB for face detection
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        face_results = detect_and_identify_faces(frame_rgb)
                        
                        # Handle face detection
                        if len(face_results) > 0:
                            # Debug: Log what faces were detected
                            detected_names = [f"{face.get('name')} ({face.get('confidence', 0):.1f}%)" for face in face_results]
                            logger.info(f"Face detection results: {detected_names}")
                            
                            # Check if multiple people detected in frame
                            if len(face_results) > 1:
                                logger.warning(f"Multiple people detected in frame: {detected_names}")
                                current_status = "⚠️ MULTIPLE PEOPLE DETECTED - Only one person should be in frame"
                                multiple_people_warning_time = current_time
                                # Don't process or log anything when multiple people detected
                            else:
                                # Only one person detected - proceed with logging
                                known_faces = [face for face in face_results if face.get('name') != 'Unknown']
                                
                                # Process first known face only (one person at a time)
                                if known_faces:
                                    face_info = known_faces[0]
                                    name = face_info.get('name')
                                    confidence = face_info.get('confidence', 0)
                                    
                                    logger.info(f"Processing known face: {name} with confidence {confidence:.1f}%")
                                    
                                    # If Unknown was logged but now we identified a known person, delete Unknown immediately
                                    # This happens regardless of whether we log the known person or not
                                    if 'Unknown' in logged_persons or violation_logger._is_person_logged_today('Unknown'):
                                        logger.info(f"Known person {name} detected - deleting any Unknown logs (session cleanup)")
                                        violation_logger._delete_previous_log('Unknown')
                                        if 'Unknown' in logged_persons:
                                            logged_persons.remove('Unknown')
                                        if 'Unknown' in last_logged_time:
                                            del last_logged_time['Unknown']
                                    
                                    # Check session tracking - only skip if logged very recently (within session timeout)
                                    should_skip = False
                                    if name in logged_persons:
                                        time_since_logged = current_time - last_logged_time.get(name, 0)
                                        if time_since_logged < session_reset_timeout:
                                            # Still within session timeout - skip logging
                                            should_skip = True
                                            time_until_reset = session_reset_timeout - time_since_logged
                                            current_status = f"{name} - Logged (resets in {int(time_until_reset)}s)"
                                            logger.debug(f"{name} already logged this session, {int(time_until_reset)}s until reset")
                                    
                                    if not should_skip:
                                        # Either first time or session timeout expired - can log/update
                                        
                                        # Check if person was logged earlier today (from database)
                                        if violation_logger._is_person_logged_today(name):
                                            current_status = f"UPDATING: {name}..."
                                            logger.info(f"Person {name} already logged today - deleting old log and replacing with new one")
                                            # Delete previous log before saving new one
                                            violation_logger._delete_previous_log(name)
                                        else:
                                            current_status = f"LOGGING: {name}..."
                                        
                                        logger.info(f"About to save violation for {name}")
                                        logger.info(f"Face results being passed to save_violation: {face_results}")
                                        logger.info(f"Non-compliant items: {non_compliant_items}")
                                        
                                        # IMPORTANT: Only pass the known face we're logging, not all face_results
                                        # This prevents Unknown faces from being saved when we detect a known person
                                        known_face_only = [face_info]  # Only the first known face
                                        logger.info(f"Filtered to known face only: {known_face_only}")
                                        
                                        # Log the violation (will replace if person was logged before)
                                        save_result = violation_logger.save_violation(
                                            frame.copy(),
                                            results,
                                            known_face_only,  # Pass only the known face, not all faces
                                            {
                                                'is_compliant': is_compliant,
                                                'non_compliant_items': non_compliant_items
                                            }
                                        )
                                        
                                        if save_result:
                                            logger.info(f"✓ Violation logged successfully: {name}, items: {non_compliant_items}")
                                            logged_persons.add(name)
                                            last_logged_time[name] = current_time  # Track when this person was logged
                                            current_status = f"✓ LOGGED: {name}"
                                        else:
                                            logger.warning(f"✗ Violation NOT logged for {name} - save_violation returned False")
                                            current_status = f"Failed to log: {name}"
                                else:
                                    # Only unknown faces detected - always log (don't replace, could be different people)
                                    if 'Unknown' not in logged_persons:
                                        current_status = "LOGGING: Unknown..."
                                        logger.info("Unknown person detected - logging violation")
                                        violation_logger.save_violation(
                                            frame.copy(),
                                            results,
                                            face_results,
                                            {
                                                'is_compliant': is_compliant,
                                                'non_compliant_items': non_compliant_items
                                            }
                                        )
                                        logged_persons.add('Unknown')
                                        last_logged_time['Unknown'] = current_time
                                        current_status = "✓ LOGGED: Unknown"
                                    else:
                                        # Already logged Unknown in this session
                                        time_since_logged = current_time - last_logged_time.get('Unknown', current_time)
                                        time_until_reset = session_reset_timeout - time_since_logged
                                        if time_until_reset > 0:
                                            current_status = f"Unknown - Logged (resets in {int(time_until_reset)}s)"
                                        else:
                                            current_status = "Unknown - Already logged"
                        else:
                            current_status = "No face detected"
                    else:
                        # Waiting for next scan
                        time_until_next = face_detection_interval - (current_time - last_face_detection_time)
                        if len(logged_persons) > 0:
                            tracked_names = ", ".join(logged_persons)
                            current_status = f"LOGGED: {tracked_names}"
                        else:
                            current_status = f"Next scan in {int(time_until_next)}s"
                
                # Draw bounding boxes
                annotated_frame = draw_detections_on_frame(annotated_frame, results)
                
                # Dynamic status indicator with color coding - TOP LEFT with background
                status_text = current_status
                
                # Color coding based on status
                if "LOADING" in status_text:
                    status_color = (255, 165, 0)  # Orange - loading
                elif "SCANNING" in status_text:
                    status_color = (0, 255, 255)  # Cyan - scanning face
                elif "LOGGING" in status_text:
                    status_color = (255, 255, 0)  # Yellow - actively logging
                elif "✓ LOGGED" in status_text or "LOGGED:" in status_text:
                    status_color = (0, 255, 0)  # Green - successfully logged
                elif "Already logged" in status_text or "Logged today" in status_text:
                    status_color = (255, 165, 0)  # Orange - already logged
                elif "Next scan" in status_text:
                    status_color = (200, 200, 200)  # Light gray - waiting
                elif "No face" in status_text:
                    status_color = (0, 165, 255)  # Light blue - no face found
                else:
                    status_color = (0, 255, 0)  # Green - default detecting
                
                # Draw status with background for better visibility
                h, w = annotated_frame.shape[:2]
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(status_text, font, font_scale, thickness)
                
                # Background rectangle - top left
                padding = 8
                bg_x1, bg_y1 = 5, 5
                bg_x2, bg_y2 = text_width + padding * 2, text_height + padding * 2
                
                overlay = annotated_frame.copy()
                cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.7, annotated_frame, 0.3, 0, annotated_frame)
                
                # Status text
                cv2.putText(annotated_frame, status_text, (padding, text_height + padding),
                           font, font_scale, status_color, thickness)
                
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
    global webcam_active, webcam_cap
    
    logger.info("Stop webcam request received")
    webcam_active = False
    
    # Give time for the stream to stop
    await asyncio.sleep(0.5)
    
    # Release the camera if it's still open
    if webcam_cap is not None:
        try:
            webcam_cap.release()
            logger.info("Webcam released successfully")
        except Exception as e:
            logger.error(f"Error releasing webcam: {e}")
        finally:
            webcam_cap = None
    
    return {"success": True, "message": "Webcam stream stopped"}