"""
Simple visibility checker using MediaPipe Pose
Shows what's visible (face, shoulders, hips, knees) without blocking detection
"""

import cv2
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available. Install with: pip install mediapipe")


class VisibilityChecker:
    """
    Check what body parts are visible without enforcing distance requirements
    Just shows an informational overlay
    """
    
    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe not available - visibility checking disabled")
            self.pose = None
            return
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        
        # Pose detector with optimized settings
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Lite model for speed
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        logger.info("Visibility checker initialized (informational only)")
    
    def check_visibility(self, frame: np.ndarray, override_message: str = None) -> Dict:
        """
        Check which body parts are visible
        Returns should_log flag based on visibility criteria
        Detection always runs, but logging only when criteria met
        
        Args:
            frame: Input frame
            override_message: Optional message to override default visibility messages
        
        Returns:
            Dict with visibility info and person_present flag (True if any body detected)
        """
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            # If MediaPipe not available, allow logging anyway
            return {"available": False, "should_log": True, "message": override_message or "", "person_present": False}
        
        if frame is None or frame.size == 0:
            return {"available": False, "should_log": False, "message": override_message or "No frame", "person_present": False}
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return {
                "available": True,
                "face_visible": False,
                "shoulders_visible": False,
                "hips_visible": False,
                "knees_visible": False,
                "should_log": False,
                "person_present": False,
                "message": override_message or "Position yourself in frame"
            }
        
        landmarks = results.pose_landmarks.landmark
        
        # Check face visibility (nose, eyes, mouth)
        nose = landmarks[0]
        left_eye = landmarks[2]
        right_eye = landmarks[5]
        mouth_left = landmarks[9]
        mouth_right = landmarks[10]
        
        face_parts_visibility = [
            nose.visibility,
            left_eye.visibility,
            right_eye.visibility,
            mouth_left.visibility,
            mouth_right.visibility
        ]
        avg_face_visibility = sum(face_parts_visibility) / len(face_parts_visibility)
        face_visible = avg_face_visibility > 0.5
        
        # Check shoulders
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulders_visible = (left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5)
        
        # Check hips
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        hips_visible = (left_hip.visibility > 0.5 and right_hip.visibility > 0.5)
        
        # Check knees
        left_knee = landmarks[25]
        right_knee = landmarks[26]
        knees_visible = (left_knee.visibility > 0.5 or right_knee.visibility > 0.5)
        
        # Calculate body metrics for distance feedback
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)
        head_y = nose.y
        
        # Determine if should log based on visibility criteria
        should_log = face_visible and shoulders_visible and hips_visible and knees_visible
        
        # Generate helpful feedback message (can be overridden)
        if override_message:
            message = override_message
        elif not face_visible:
            message = "Face not visible - Look at camera"
        elif not shoulders_visible:
            message = "Center yourself in frame"
        elif not hips_visible:
            message = "Step back - Show more of outfit"
        elif not knees_visible:
            message = "Step back - Show knees for best detection"
        elif shoulder_width > 0.6:
            message = "Step back - Too close to camera"
        elif shoulder_width < 0.15:
            message = "Move closer - Too far from camera"
        elif head_y > 0.35:
            message = "Step back slightly - Show full outfit"
        else:
            message = "Perfect! Ready for logging"
        
        return {
            "available": True,
            "face_visible": face_visible,
            "shoulders_visible": shoulders_visible,
            "hips_visible": hips_visible,
            "knees_visible": knees_visible,
            "should_log": should_log,
            "person_present": True,  # Person detected by MediaPipe
            "message": message
        }
    
    def draw_visibility_overlay(self, frame: np.ndarray, visibility_info: Dict) -> np.ndarray:
        """
        Draw minimalistic visibility checklist with positioning guidance
        Shows helpful feedback message about how to position
        """
        if not visibility_info.get("available"):
            return frame
        
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Get message and should_log status
        message = visibility_info.get("message", "")
        should_log = visibility_info.get("should_log", False)
        
        # Message color: green if ready, orange if needs adjustment
        message_color = (0, 255, 0) if should_log else (0, 165, 255)
        
        # Show feedback message at top center (below status indicator)
        if message:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.65
            thickness = 2
            
            (text_width, text_height), _ = cv2.getTextSize(message, font, font_scale, thickness)
            text_x = (w - text_width) // 2
            text_y = 70  # Moved down from 40 to avoid overlap with top-left status
            padding = 10
            
            # Dark background behind text
            overlay = annotated.copy()
            cv2.rectangle(overlay, 
                         (text_x - padding, text_y - text_height - padding),
                         (text_x + text_width + padding, text_y + padding),
                         (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
            
            # Display message
            cv2.putText(annotated, message, (text_x, text_y),
                       font, font_scale, message_color, thickness)
        
        # Checklist position (bottom-left)
        checklist_x = 15
        checklist_y = h - 130
        
        # Semi-transparent dark background
        overlay = annotated.copy()
        cv2.rectangle(overlay, (10, h - 140), (200, h - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)
        
        # Title
        cv2.putText(annotated, "Visibility", (checklist_x, checklist_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        checklist_y += 25
        
        # Checklist items
        checklist_items = [
            ("Face", visibility_info.get("face_visible", False)),
            ("Shoulders", visibility_info.get("shoulders_visible", False)),
            ("Hips", visibility_info.get("hips_visible", False)),
            ("Knees", visibility_info.get("knees_visible", False))
        ]
        
        for part, visible in checklist_items:
            check_color = (0, 255, 0) if visible else (100, 100, 100)
            check_symbol = "✓" if visible else "○"
            
            cv2.putText(annotated, f"{check_symbol} {part}", (checklist_x + 10, checklist_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.45, check_color, 1)
            checklist_y += 22
        
        return annotated
    
    def cleanup(self):
        """Release resources"""
        if hasattr(self, 'pose') and self.pose:
            self.pose.close()


# Global instance
_visibility_checker = None

def get_visibility_checker() -> VisibilityChecker:
    """Get singleton instance of VisibilityChecker"""
    global _visibility_checker
    if _visibility_checker is None:
        _visibility_checker = VisibilityChecker()
    return _visibility_checker
