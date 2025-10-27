"""
Sync Face Database to Redis (InsightFace Version)
Uses InsightFace (MobileFaceNet) for faster face encoding
"""

import os
import redis
import pickle
import cv2
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    logger.error("InsightFace not installed. Run: pip install insightface onnxruntime")
    exit(1)

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)
KNOWN_USERS_SET = "known_users"

# Initialize InsightFace
logger.info("Initializing InsightFace...")
app = FaceAnalysis(
    name='buffalo_s',  # Lightweight model
    providers=['CPUExecutionProvider']  # Use CPU only for sync
)
app.prepare(ctx_id=-1, det_size=(640, 640))  # ctx_id=-1 for CPU
logger.info("InsightFace initialized successfully (CPU mode)")

def register_or_update_person(person_name: str, images_folder: str):
    """
    Register or update a person's face encodings in Redis
    
    Args:
        person_name: Name of the person
        images_folder: Path to folder containing person's images
    """
    user_id = person_name.lower().replace(" ", "_")
    encoding_list_key = f"user:{user_id}:encodings"
    
    # Clear existing encodings
    r.delete(encoding_list_key)
    
    # Process all images in folder
    image_files = [f for f in os.listdir(images_folder) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        logger.warning(f"No images found for {person_name}")
        return 0
    
    encodings_count = 0
    
    for image_file in image_files:
        image_path = os.path.join(images_folder, image_file)
        
        try:
            # Read image
            image = cv2.imread(image_path)
            
            if image is None:
                logger.warning(f"Could not read image: {image_path}")
                continue
            
            # Detect faces
            faces = app.get(image)
            
            if len(faces) == 0:
                logger.warning(f"No face found in {image_file}")
                continue
            
            if len(faces) > 1:
                logger.warning(f"Multiple faces found in {image_file}, using largest")
            
            # Use the largest face (most likely the main subject)
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            
            # Get face embedding
            embedding = face.embedding
            
            # Store in Redis
            encoding_bytes = pickle.dumps(embedding)
            r.rpush(encoding_list_key, encoding_bytes)
            encodings_count += 1
            
            logger.info(f"  ✓ Processed {image_file}")
            
        except Exception as e:
            logger.error(f"Error processing {image_file}: {e}")
    
    if encodings_count > 0:
        # Add user to known users set
        r.sadd(KNOWN_USERS_SET, user_id)
        logger.info(f"✓ Registered {person_name} with {encodings_count} encodings")
    else:
        logger.warning(f"✗ Failed to register {person_name} - no valid encodings")
    
    return encodings_count

def get_all_registered_users():
    """Get list of all registered users from Redis"""
    user_ids = [uid.decode('utf-8') for uid in r.smembers(KNOWN_USERS_SET)]
    return [uid.replace("_", " ").title() for uid in user_ids]

def clear_user_from_db(person_name: str):
    """Remove a user from the database"""
    user_id = person_name.lower().replace(" ", "_")
    encoding_list_key = f"user:{user_id}:encodings"
    
    r.delete(encoding_list_key)
    r.srem(KNOWN_USERS_SET, user_id)
    logger.info(f"Removed {person_name} from database")

def main():
    """Main synchronization function"""
    database_folder = "database"
    
    if not os.path.exists(database_folder):
        logger.error(f"Database folder not found: {database_folder}")
        logger.info("Create a 'database' folder with subfolders for each person")
        logger.info("Example: database/John_Doe/0.jpg, 1.jpg, 2.jpg, ...")
        return
    
    logger.info("=" * 60)
    logger.info("Face Database Sync (InsightFace - MobileFaceNet)")
    logger.info("=" * 60)
    
    # Get all person folders
    person_folders = [f for f in os.listdir(database_folder) 
                     if os.path.isdir(os.path.join(database_folder, f)) and f != ".gitkeep"]
    
    if not person_folders:
        logger.warning("No person folders found in database/")
        return
    
    logger.info(f"Found {len(person_folders)} person(s) to sync")
    logger.info("")
    
    total_encodings = 0
    successful_persons = 0
    
    for person_folder in person_folders:
        person_name = person_folder.replace("_", " ")
        folder_path = os.path.join(database_folder, person_folder)
        
        logger.info(f"Processing: {person_name}")
        count = register_or_update_person(person_name, folder_path)
        
        if count > 0:
            successful_persons += 1
            total_encodings += count
        
        logger.info("")
    
    logger.info("=" * 60)
    logger.info(f"Sync Complete!")
    logger.info(f"  Persons registered: {successful_persons}/{len(person_folders)}")
    logger.info(f"  Total encodings: {total_encodings}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Registered users:")
    for user in get_all_registered_users():
        logger.info(f"  - {user}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nSync cancelled by user")
    except Exception as e:
        logger.error(f"Error during sync: {e}", exc_info=True)
