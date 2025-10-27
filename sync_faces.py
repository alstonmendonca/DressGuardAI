import face_recognition
import cv2
import os
import redis
import pickle
from collections import defaultdict

# Connect to Redis.
r = redis.Redis(host='localhost', port=6379, db=0)
KNOWN_USERS_SET = "known_users"

def get_all_registered_users():
    """Returns a set of all user IDs currently in the database."""
    return {uid.decode('utf-8') for uid in r.smembers(KNOWN_USERS_SET)}

def clear_user_from_db(user_id):
    """Completely removes a user and their encodings from the database."""
    encoding_list_key = f"user:{user_id}:encodings"
    r.delete(encoding_list_key)
    r.srem(KNOWN_USERS_SET, user_id)
    print(f"  Removed {user_id} from database.")

def register_or_update_person(name, image_folder_path):
    """
    Registers a new person or updates an existing one by re-processing their folder.
    This replaces the old encodings with new ones.
    """
    user_id = name.lower().replace(" ", "_")
    print(f"Processing: {name} ({user_id})")

    # Clear existing data for this user to avoid duplicates
    clear_user_from_db(user_id)

    all_encodings_for_person = []
    image_count = 0

    # Process all images in the folder
    for image_file in os.listdir(image_folder_path):
        if image_file.startswith('.'):
            continue
        image_path = os.path.join(image_folder_path, image_file)
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            print(f"    No face found in {image_file}. Skipping.")
            continue

        print(f"    Found {len(face_encodings)} face(s) in {image_file}")
        image_count += 1
        for encoding in face_encodings:
            all_encodings_for_person.append(pickle.dumps(encoding))

    if image_count == 0:
        print(f"  Failed to register {name}. No valid images found. Skipping.")
        return

    # Add the new encodings to Redis
    encoding_list_key = f"user:{user_id}:encodings"
    with r.pipeline() as pipe:
        for encoding_bytes in all_encodings_for_person:
            pipe.lpush(encoding_list_key, encoding_bytes)
        pipe.sadd(KNOWN_USERS_SET, user_id)
        pipe.execute()

    print(f"  Successfully updated {name}. Added {len(all_encodings_for_person)} encodings from {image_count} images.\n")

# Main synchronization logic
if __name__ == "__main__":
    dataset_path = "database"  #EDIT PATH HERE TO YOUR DATABASE
    
    # Get current state of the database and file system
    currently_registered_users = get_all_registered_users()
    users_on_disk = {name.lower().replace(" ", "_") for name in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, name))}
    
    # --- Option: Remove users from DB that are no longer on disk ---
    # users_to_remove = currently_registered_users - users_on_disk
    # for user_id in users_to_remove:
    #     print(f"User {user_id} found in DB but not on disk.")
    #     clear_user_from_db(user_id)
    # --- Use this with caution! ---

    # Process every person found in the dataset directory
    for person_name in os.listdir(dataset_path):
        person_dir = os.path.join(dataset_path, person_name)
        if os.path.isdir(person_dir):
            register_or_update_person(person_name, person_dir)
    
    print("Synchronization complete!")
    print(f"Total known users in DB: {r.scard(KNOWN_USERS_SET)}")
