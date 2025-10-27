import face_recognition
import redis
import pickle
import numpy as np
import cv2
import os
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # Test connection
    logger.info("Connected to Redis for face recognition")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    r = None

KNOWN_USERS_SET = "known_users"

# Configuration
FACE_MATCH_THRESHOLD = 0.6

def recognize_face(unknown_encoding):
    """
    Finds the best match for an unknown face encoding from the Redis database.
    Returns (name, confidence, best_match_id)
    """
    if r is None:
        return "Unknown", 0.0, None
        
    try:
        best_match_id = None
        best_distance = float('inf')
        
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
                distance = np.linalg.norm(unknown_encoding - stored_encoding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match_id = user_id
        
        confidence = (1 - min(best_distance, 1.0)) * 100  # 0-100%

        if best_distance <= FACE_MATCH_THRESHOLD:
            name = best_match_id.replace("_", " ").title()
            return name, confidence, best_match_id
        else:
            return "Unknown", confidence, None
            
    except Exception as e:
        logger.error(f"Error in face recognition: {e}")
        return "Unknown", 0.0, None

def detect_and_identify_faces(image_array):
    """
    Detect faces in an image and identify them.
    
    Args:
        image_array: numpy array (RGB format) from cv2 or face_recognition
        
    Returns:
        List of dictionaries with face info:
        [
            {
                'name': 'John Doe',
                'confidence': 85.5,
                'bbox': (top, right, bottom, left),
                'user_id': 'john_doe'
            },
            ...
        ]
    """
    if r is None:
        logger.warning("Redis not connected, skipping face detection")
        return []
    
    try:
        # Find face locations and encodings
        face_locations = face_recognition.face_locations(image_array)
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        logger.info(f"Face detection: Found {len(face_locations)} faces in frame")
        
        results = []
        for face_location, face_encoding in zip(face_locations, face_encodings):
            name, confidence, user_id = recognize_face(face_encoding)
            
            results.append({
                'name': name,
                'confidence': confidence,
                'bbox': face_location,  # (top, right, bottom, left)
                'user_id': user_id
            })
        
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
        Modified image with face boxes drawn
    """
    for face in face_results:
        top, right, bottom, left = face['bbox']
        name = face['name']
        confidence = face['confidence']
        
        # Choose color based on recognition
        if name == "Unknown":
            color = (0, 0, 255)  # Red for unknown
        else:
            color = (0, 255, 0)  # Green for recognized
        
        # Draw rectangle
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        
        # Draw label background
        label = f"{name} ({confidence:.1f}%)"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(image, (left, top - label_size[1] - 10), 
                     (left + label_size[0], top), color, -1)
        
        # Draw label text
        cv2.putText(image, label, (left, top - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return image

def process_image(image_path):
    """
    Process a single image and return identification results
    """
    try:
        # Load the image
        image = face_recognition.load_image_file(image_path)
        
        # Find faces and encodings
        face_encodings = face_recognition.face_encodings(image)
        
        results = []
        for face_encoding in face_encodings:
            name, confidence, user_id = recognize_face(face_encoding)
            if name != "Unknown":
                results.append((name, confidence))
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return []

def main():
    """Main function to process all images in a folder"""
    # Configuration - SET YOUR FOLDER PATH HERE
    input_folder = "frames"  # Change this to your folder path
    
    if not os.path.exists(input_folder):
        print(f"Error: Folder '{input_folder}' does not exist.")
        return
    
    # Get all image files in the folder
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(input_folder) 
                  if f.lower().endswith(image_extensions)]
    
    if not image_files:
        print(f"No image files found in '{input_folder}'")
        return
    
    print(f"Found {len(image_files)} images to process in '{input_folder}'")
    print("Processing...")
    
    all_results = []  # Store all (name, confidence) tuples across all images
    
    # Process each image
    for i, image_file in enumerate(image_files, 1):
        image_path = os.path.join(input_folder, image_file)
        print(f"Processing image {i}/{len(image_files)}: {image_file}")
        
        results = process_image(image_path)
        for name, confidence in results:
            all_results.append((name, confidence))
            print(f"  -> Detected {name} ({confidence:.1f}%)")
    
    # Analyze and display final results
    if not all_results:
        print("\nNo identifiable faces found in any images.")
        return
    
    print(f"\n--- FINAL RESULT ---")
    print(f"Total detections across {len(image_files)} images: {len(all_results)}")
    
    # Group results by name and calculate averages
    results_by_name = {}
    for name, confidence in all_results:
        if name not in results_by_name:
            results_by_name[name] = []
        results_by_name[name].append(confidence)
    
    # Calculate average confidence for each person
    for name, confidences in results_by_name.items():
        avg_confidence = sum(confidences) / len(confidences)
        detection_count = len(confidences)
        print(f"{name}: {detection_count} detections, Avg confidence: {avg_confidence:.1f}%")
    
    # Determine the overall result (person with most detections)
    names_only = [result[0] for result in all_results]
    if names_only:
        most_common_name, count = Counter(names_only).most_common(1)[0]
        most_common_confidences = [conf for name, conf in all_results if name == most_common_name]
        final_confidence = sum(most_common_confidences) / len(most_common_confidences)
        
        print(f"\nFINAL IDENTIFICATION: {most_common_name}")
        print(f"OVERALL CONFIDENCE: {final_confidence:.1f}%")
        print(f"Based on {count} detections across {len(image_files)} images")

if __name__ == "__main__":
    main()
