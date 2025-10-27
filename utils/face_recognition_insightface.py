"""
Face Recognition using InsightFace (MobileFaceNet backend)
Much faster than dlib-based face_recognition library
Optimized for real-time detection
"""

import redis
import pickle
import numpy as np
import cv2
import os
import logging

logger = logging.getLogger(__name__)

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logger.warning("InsightFace not available. Install with: pip install insightface onnxruntime")

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # Test connection
    logger.info("Connected to Redis for face recognition (InsightFace)")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    r = None

KNOWN_USERS_SET = "known_users"

# Configuration
FACE_MATCH_THRESHOLD = 0.4  # Cosine similarity threshold (lowered for better matching)
MIN_FACE_SIZE = 40  # Minimum face size to detect

# Initialize InsightFace model (lazy loading)
face_app = None

def get_face_app():
    """Lazy load InsightFace model"""
    global face_app
    
    if not INSIGHTFACE_AVAILABLE:
        logger.error("InsightFace not available")
        return None
    
    if face_app is None:
        try:
            # Try GPU first, fallback to CPU
            try:
                face_app = FaceAnalysis(
                    name='buffalo_s',  # Lightweight model with MobileFaceNet
                    providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
                )
                face_app.prepare(ctx_id=0, det_size=(640, 640))
                logger.info("InsightFace initialized with buffalo_s (GPU mode)")
            except:
                # Fallback to CPU only
                face_app = FaceAnalysis(
                    name='buffalo_s',
                    providers=['CPUExecutionProvider']
                )
                face_app.prepare(ctx_id=-1, det_size=(640, 640))
                logger.info("InsightFace initialized with buffalo_s (CPU mode)")
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace: {e}")
            return None
    
    return face_app

def recognize_face(face_embedding):
    """
    Finds the best match for a face embedding from the Redis database.
    
    Args:
        face_embedding: Face embedding vector from InsightFace
        
    Returns:
        tuple: (name, confidence, best_match_id)
    """
    if r is None:
        return "Unknown", 0.0, None
        
    try:
        # Normalize the input embedding (L2 normalization)
        face_embedding = face_embedding / np.linalg.norm(face_embedding)
        
        best_match_id = None
        best_similarity = 0.0  # Cosine similarity (higher is better)
        
        # Get all known user IDs
        known_user_ids = [uid.decode('utf-8') for uid in r.smembers(KNOWN_USERS_SET)]
        
        if not known_user_ids:
            logger.warning("No users found in Redis database")
            return "Unknown", 0.0, None
        
        for user_id in known_user_ids:
            encoding_list_key = f"user:{user_id}:encodings"
            stored_encodings_bytes = r.lrange(encoding_list_key, 0, -1)
            
            for encoding_bytes in stored_encodings_bytes:
                stored_encoding = pickle.loads(encoding_bytes)
                
                # Normalize stored encoding as well
                stored_encoding = stored_encoding / np.linalg.norm(stored_encoding)
                
                # Compute cosine similarity
                similarity = np.dot(face_embedding, stored_encoding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = user_id
        
        confidence = best_similarity * 100  # Convert to percentage
        
        # Debug logging
        logger.info(f"Face matching - Best similarity: {best_similarity:.3f} ({confidence:.1f}%), Threshold: {FACE_MATCH_THRESHOLD}, Match: {best_match_id if best_similarity >= FACE_MATCH_THRESHOLD else 'None'}")
        
        if best_similarity >= FACE_MATCH_THRESHOLD:
            name = best_match_id.replace("_", " ").title()
            return name, confidence, best_match_id
        else:
            return "Unknown", confidence, None
            
    except Exception as e:
        logger.error(f"Error in face recognition: {e}")
        return "Unknown", 0.0, None

def detect_and_identify_faces(image_array):
    """
    Detect faces in an image and identify them using InsightFace.
    MUCH faster than dlib-based face_recognition library.
    
    Args:
        image_array: numpy array (RGB or BGR format)
        
    Returns:
        List of dictionaries with face info:
        [
            {
                'name': 'John Doe',
                'confidence': 85.5,
                'bbox': (top, right, bottom, left),  # Compatible with old format
                'user_id': 'john_doe',
                'age': 25,  # Optional
                'gender': 'M'  # Optional
            },
            ...
        ]
    """
    app = get_face_app()
    
    if app is None or r is None:
        logger.warning("InsightFace or Redis not available, skipping face detection")
        return []
    
    try:
        # Convert RGB to BGR if needed (InsightFace expects BGR)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # Assume input is RGB, convert to BGR
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        # Detect and analyze faces
        faces = app.get(image_bgr)
        
        logger.info(f"Face detection: Found {len(faces)} faces in frame")
        
        results = []
        for face in faces:
            # Get bounding box (convert to top, right, bottom, left format)
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            top, right, bottom, left = y1, x2, y2, x1
            
            # Get face embedding
            embedding = face.embedding
            
            # Recognize face
            name, confidence, user_id = recognize_face(embedding)
            
            face_info = {
                'name': name,
                'confidence': confidence,
                'bbox': (top, right, bottom, left),  # Compatible format
                'user_id': user_id
            }
            
            # Optional: Add age and gender if available
            if hasattr(face, 'age'):
                face_info['age'] = int(face.age)
            if hasattr(face, 'gender'):
                face_info['gender'] = 'M' if face.gender == 1 else 'F'
            
            results.append(face_info)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in face detection: {e}")
        return []

def draw_face_boxes(image, face_results):
    """
    Draw bounding boxes and labels on detected faces.
    
    Args:
        image: numpy array (BGR format for cv2)
        face_results: List of face detection results from detect_and_identify_faces
        
    Returns:
        numpy array: Image with drawn boxes
    """
    for face in face_results:
        top, right, bottom, left = face['bbox']
        name = face['name']
        confidence = face['confidence']
        
        # Choose color based on recognition
        if name == "Unknown":
            color = (0, 165, 255)  # Orange for unknown
            label_bg = (0, 140, 255)
        else:
            color = (255, 0, 255)  # Magenta for recognized
            label_bg = (200, 0, 200)
        
        # Draw rectangle
        cv2.rectangle(image, (left, top), (right, bottom), color, 3)
        
        # Draw label background
        label = f"{name} ({confidence:.1f}%)"
        
        # Add age/gender if available
        if 'age' in face and 'gender' in face:
            label = f"{name} ({face['gender']}/{face['age']}) {confidence:.1f}%"
        
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(image, (left, bottom), 
                     (left + label_size[0] + 10, bottom + label_size[1] + 10), 
                     label_bg, -1)
        
        # Draw label text
        cv2.putText(image, label, (left + 5, bottom + label_size[1] + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return image

# Backward compatibility function
def get_face_match_threshold():
    """Get current face match threshold"""
    return FACE_MATCH_THRESHOLD
