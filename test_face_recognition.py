"""
Test face recognition with InsightFace
"""
import cv2
import sys
from utils.face_recognition_insightface import detect_and_identify_faces

def test_image(image_path):
    """Test face recognition on an image"""
    print(f"\n{'='*60}")
    print(f"Testing: {image_path}")
    print('='*60)
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"ERROR: Could not load image from {image_path}")
        return
    
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect and identify faces
    faces = detect_and_identify_faces(image_rgb)
    
    print(f"\nFound {len(faces)} face(s):")
    for i, face in enumerate(faces, 1):
        print(f"\nFace {i}:")
        print(f"  Name: {face['name']}")
        print(f"  Confidence: {face['confidence']:.2f}%")
        print(f"  User ID: {face.get('user_id', 'N/A')}")
        print(f"  BBox: {face['bbox']}")
        if 'age' in face:
            print(f"  Age: {face['age']}")
        if 'gender' in face:
            print(f"  Gender: {face['gender']}")
        
        # Draw on image
        top, right, bottom, left = face['bbox']
        color = (0, 255, 0) if face['name'] != 'Unknown' else (255, 165, 0)
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        
        # Label
        label = f"{face['name']} ({face['confidence']:.1f}%)"
        cv2.putText(image, label, (left, top - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    # Show image
    cv2.imshow('Face Recognition Test', image)
    print("\nPress any key to continue...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python test_face_recognition.py <image_path>")
        print("\nTesting with sample images from database...\n")
        
        # Test with known faces
        test_images = [
            "database/Alston Daniel Mendonca/0.jpg",
            "database/Jenica Deanne Dsouza/0.jpg",
            "database/Nicole Alberta Lasrado/0.jpg",
            "database/Reevan Dmello/0.jpg"
        ]
        
        for img_path in test_images:
            try:
                test_image(img_path)
            except Exception as e:
                print(f"Error testing {img_path}: {e}")
    else:
        test_image(sys.argv[1])
