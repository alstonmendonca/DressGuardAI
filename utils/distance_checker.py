"""
Distance/Full Body Checker for Webcam Detection
Validates if person is at appropriate distance before processing frame
"""

import cv2
import numpy as np
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class DistanceChecker:
    """Check if person is at appropriate distance for full outfit detection"""
    
    def __init__(self):
        # Load Haar Cascade for face detection (lightweight, fast)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.last_check_result = None
        self.last_check_time = 0
        self.check_interval = 0.5  # Only run face detection every 0.5 seconds
        
    def check_distance(self, frame: np.ndarray) -> Dict:
        """
        Check if frame shows person at good distance for full body detection
        
        Args:
            frame: BGR image from webcam
            
        Returns:
            dict with:
                - is_good_distance: bool
                - message: str (user feedback)
                - confidence: int (0-100)
                - should_process: bool (whether to send frame for detection)
        """
        import time
        current_time = time.time()
        
        # Use cached result if check was done recently (performance optimization)
        if self.last_check_result and (current_time - self.last_check_time) < self.check_interval:
            return self.last_check_result
        
        if frame is None or frame.size == 0:
            return {
                "is_good_distance": False,
                "message": "No frame",
                "confidence": 0,
                "should_process": False
            }
        
        h, w = frame.shape[:2]
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with optimized parameters
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,  # Faster (was 1.1)
            minNeighbors=4,   # Faster (was 5)
            minSize=(40, 40)  # Slightly larger minimum (was 30x30)
        )
        
        if len(faces) == 0:
            return {
                "is_good_distance": False,
                "message": "Position yourself in frame",
                "confidence": 20,
                "should_process": False,
                "details": {"faces_detected": 0}
            }
        
        # Get largest face (assume it's the person we want to detect)
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        fx, fy, fw, fh = largest_face
        
        # Calculate body metrics
        face_area = fw * fh
        frame_area = w * h
        face_ratio = face_area / frame_area
        
        # Face position (should be in upper portion for 3/4 body visibility)
        face_center_y = fy + (fh / 2)
        face_relative_y = face_center_y / h
        
        # Calculate body estimation (relaxed for 3/4 body instead of full body)
        # For 3/4 body: ~5x head height instead of 7x
        estimated_body_height = fh * 5  # Reduced from 7 for 3/4 body
        estimated_body_bottom = fy + estimated_body_height
        
        # Decision logic
        is_good_distance = False
        message = ""
        confidence = 0
        should_process = False
        
        # Face too large = too close
        if face_ratio > 0.18:  # Increased from 0.15 to allow closer
            message = "Step back - Too close to camera"
            confidence = 30
            
        # Face too small = too far
        elif face_ratio < 0.008:
            message = "Move closer - Too far from camera"
            confidence = 40
            
        # Face in middle/bottom = need to step back
        elif face_relative_y > 0.5:  # Increased from 0.4 to allow face to be lower
            message = "Step back to show outfit"
            confidence = 45
            
        # Body likely cut off at bottom (relaxed threshold for 3/4 visibility)
        elif estimated_body_bottom > h * 1.05:  # Changed from 0.95 to 1.05 (allow bottom 5% to be cut off)
            message = "Step back - More outfit should be visible"
            confidence = 50
            
        # Good distance!
        else:
            is_good_distance = True
            should_process = True
            message = "Good! 3/4 outfit visible"
            confidence = 85
        
        result = {
            "is_good_distance": is_good_distance,
            "message": message,
            "confidence": confidence,
            "should_process": should_process,
            "details": {
                "faces_detected": len(faces),
                "face_ratio": round(face_ratio, 4),
                "face_relative_y": round(face_relative_y, 3),
                "estimated_body_fits": estimated_body_bottom <= h * 1.05
            }
        }
        
        # Cache the result
        self.last_check_result = result
        self.last_check_time = current_time
        
        return result
    
    def draw_distance_feedback(self, frame: np.ndarray, check_result: Dict) -> np.ndarray:
        """
        Draw distance check feedback on frame
        
        Args:
            frame: BGR image
            check_result: Result from check_distance()
            
        Returns:
            Annotated frame with feedback overlay
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Choose color based on status
        if check_result["is_good_distance"]:
            color = (0, 255, 0)  # Green
            bg_color = (0, 100, 0)
        else:
            color = (0, 165, 255)  # Orange
            bg_color = (0, 60, 120)
        
        # Draw semi-transparent background for message
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, 60), bg_color, -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
        
        # Draw message
        message = check_result["message"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        
        # Center the text
        (text_width, text_height), _ = cv2.getTextSize(message, font, font_scale, thickness)
        text_x = (w - text_width) // 2
        text_y = 35
        
        # Draw text with outline for visibility
        cv2.putText(annotated, message, (text_x, text_y),
                   font, font_scale, (0, 0, 0), thickness + 2)
        cv2.putText(annotated, message, (text_x, text_y),
                   font, font_scale, color, thickness)
        
        # Draw confidence indicator
        conf_text = f"Ready: {check_result['confidence']}%"
        cv2.putText(annotated, conf_text, (10, h - 10),
                   font, 0.5, color, 1)
        
        return annotated


# Global instance
_distance_checker = None

def get_distance_checker() -> DistanceChecker:
    """Get singleton instance of DistanceChecker"""
    global _distance_checker
    if _distance_checker is None:
        _distance_checker = DistanceChecker()
    return _distance_checker
