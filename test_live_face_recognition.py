"""
Test face recognition with live camera feed using InsightFace
Press 'q' to quit
"""
import cv2
import time
from utils.face_recognition_insightface import detect_and_identify_faces

def test_live_camera():
    """Test face recognition on live camera feed"""
    print("\n" + "="*60)
    print("Live Camera Face Recognition Test")
    print("="*60)
    print("\nStarting camera...")
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("Camera started successfully!")
    print("\nControls:")
    print("  'q' - Quit")
    print("  's' - Toggle stats display")
    print("\n" + "="*60 + "\n")
    
    fps_counter = 0
    fps_start_time = time.time()
    current_fps = 0
    show_stats = True
    
    # Face detection timing
    last_detection_time = 0
    detection_interval = 0.5  # Run face detection every 0.5 seconds
    last_faces = []  # Cache last detection results
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Failed to grab frame")
            break
        
        current_time = time.time()
        
        # Run face detection at intervals (not every frame)
        if current_time - last_detection_time >= detection_interval:
            last_detection_time = current_time
            
            # Convert BGR to RGB for face detection
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Measure detection time
            detect_start = time.time()
            faces = detect_and_identify_faces(frame_rgb)
            detect_time = (time.time() - detect_start) * 1000  # Convert to ms
            
            last_faces = faces  # Cache results
            
            # Print detection info
            if faces:
                print(f"\rDetected {len(faces)} face(s) in {detect_time:.1f}ms", end='')
                for face in faces:
                    if face['name'] != 'Unknown':
                        print(f" | {face['name']}: {face['confidence']:.1f}%", end='')
        else:
            faces = last_faces  # Use cached results
        
        # Draw face boxes and labels
        for face in faces:
            top, right, bottom, left = face['bbox']
            
            # Color: Green for known, Orange for unknown
            if face['name'] == 'Unknown':
                color = (0, 165, 255)  # Orange (BGR)
                box_thickness = 2
            else:
                color = (0, 255, 0)  # Green (BGR)
                box_thickness = 3
            
            # Draw rectangle
            cv2.rectangle(frame, (left, top), (right, bottom), color, box_thickness)
            
            # Prepare label
            label = f"{face['name']}"
            conf_text = f"{face['confidence']:.1f}%"
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.8, 2)[0]
            conf_size = cv2.getTextSize(conf_text, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1)[0]
            
            # Name label
            cv2.rectangle(frame, (left, top - label_size[1] - 10), 
                         (left + label_size[0] + 10, top), color, -1)
            cv2.putText(frame, label, (left + 5, top - 5),
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 2)
            
            # Confidence label
            cv2.rectangle(frame, (left, bottom), 
                         (left + conf_size[0] + 10, bottom + conf_size[1] + 10), 
                         color, -1)
            cv2.putText(frame, conf_text, (left + 5, bottom + conf_size[1] + 5),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)
            
            # Optional: Show age and gender
            if 'age' in face and 'gender' in face:
                info = f"{face['age']}y, {face['gender']}"
                cv2.putText(frame, info, (left, bottom + 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Calculate FPS
        fps_counter += 1
        if current_time - fps_start_time >= 1.0:
            current_fps = fps_counter
            fps_counter = 0
            fps_start_time = current_time
        
        # Show stats overlay
        if show_stats:
            # Semi-transparent background for stats
            overlay = frame.copy()
            cv2.rectangle(overlay, (10, 10), (350, 120), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            # Stats text
            cv2.putText(frame, f"FPS: {current_fps}", (20, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Faces: {len(faces)}", (20, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Known vs Unknown count
            known_count = sum(1 for f in faces if f['name'] != 'Unknown')
            unknown_count = len(faces) - known_count
            cv2.putText(frame, f"Known: {known_count} | Unknown: {unknown_count}", 
                       (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Display frame
        cv2.imshow('Live Face Recognition Test (Press Q to quit)', frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\n\nQuitting...")
            break
        elif key == ord('s') or key == ord('S'):
            show_stats = not show_stats
            print(f"\nStats display: {'ON' if show_stats else 'OFF'}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Camera stopped.")
    print("\nTest complete!\n")

if __name__ == '__main__':
    try:
        test_live_camera()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
