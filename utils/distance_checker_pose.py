"""
Distance/Full Body Checker using MediaPipe Pose
Much more accurate than Haar Cascades - detects full body skeleton
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("MediaPipe Pose available - using advanced body detection")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available. Install with: pip install mediapipe")


class DistanceCheckerPose:
    """
    Check if person is at appropriate distance using MediaPipe Pose
    Much more accurate than face detection - tracks full body skeleton
    """
    
    def __init__(self, model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe not installed. Run: pip install mediapipe")
        
        # Initialize MediaPipe Pose
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Pose detector with optimized settings
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,  # Video mode (faster)
            model_complexity=model_complexity,  # 0=Lite (fastest), 1=Full, 2=Heavy
            smooth_landmarks=True,     # Smooth tracking
            enable_segmentation=False, # Don't need segmentation (faster)
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        self.last_check_result = None
        self.last_check_time = 0
        self.check_interval = 0.1  # Check every 100ms (10 FPS)
        
        complexity_names = {0: "Lite", 1: "Full", 2: "Heavy"}
        logger.info(f"MediaPipe Pose initialized ({complexity_names.get(model_complexity, 'Unknown')} model)")
    
    def check_distance(self, frame: np.ndarray) -> Dict:
        """
        Check if frame shows person at good distance for 3/4 body detection
        
        Args:
            frame: BGR image from webcam
            
        Returns:
            dict with:
                - is_good_distance: bool
                - message: str (user feedback)
                - confidence: int (0-100)
                - should_process: bool
                - landmarks: pose landmarks (optional)
        """
        import time
        current_time = time.time()
        
        # Use cached result if check was done recently
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
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(rgb_frame)
        
        if not results.pose_landmarks:
            return {
                "is_good_distance": False,
                "message": "Position yourself in frame",
                "confidence": 20,
                "should_process": False,
                "landmarks": None
            }
        
        landmarks = results.pose_landmarks.landmark
        
        # Key body parts (normalized 0-1 coordinates)
        # 0=Nose, 1=Left Eye Inner, 2=Left Eye, 3=Left Eye Outer,
        # 4=Right Eye Inner, 5=Right Eye, 6=Right Eye Outer,
        # 7=Left Ear, 8=Right Ear, 9=Mouth Left, 10=Mouth Right,
        # 11=Left Shoulder, 12=Right Shoulder, 
        # 23=Left Hip, 24=Right Hip, 25=Left Knee, 26=Right Knee
        nose = landmarks[0]
        left_eye = landmarks[2]
        right_eye = landmarks[5]
        left_ear = landmarks[7]
        right_ear = landmarks[8]
        mouth_left = landmarks[9]
        mouth_right = landmarks[10]
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_knee = landmarks[25]
        right_knee = landmarks[26]
        
        # Check face visibility (eyes, nose, mouth)
        face_parts_visibility = [
            nose.visibility,
            left_eye.visibility,
            right_eye.visibility,
            mouth_left.visibility,
            mouth_right.visibility
        ]
        avg_face_visibility = sum(face_parts_visibility) / len(face_parts_visibility)
        face_visible = avg_face_visibility > 0.5
        
        # Calculate visibility scores (0-1, where 1 = fully visible)
        key_parts_visibility = [
            nose.visibility,
            left_shoulder.visibility,
            right_shoulder.visibility,
            left_hip.visibility,
            right_hip.visibility,
            left_knee.visibility,
            right_knee.visibility
        ]
        
        avg_visibility = sum(key_parts_visibility) / len(key_parts_visibility)
        
        # Calculate body metrics
        # Head position (y coordinate, 0=top, 1=bottom)
        head_y = nose.y
        
        # Shoulder width (normalized)
        shoulder_width = abs(right_shoulder.x - left_shoulder.x)
        
        # Body height (from nose to average knee position)
        avg_knee_y = (left_knee.y + right_knee.y) / 2
        body_height = avg_knee_y - nose.y
        
        # Check if knees are visible (for 3/4 body)
        knees_visible = (left_knee.visibility > 0.5 or right_knee.visibility > 0.5)
        
        # Check if hips are visible
        hips_visible = (left_hip.visibility > 0.5 and right_hip.visibility > 0.5)
        
        # Check if shoulders are visible
        shoulders_visible = (left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5)
        
        # Decision logic for 3/4 body visibility
        is_good_distance = False
        message = ""
        confidence = 0
        should_process = False
        
        # Face not visible - critical requirement
        if not face_visible:
            message = "Face not visible - Look at camera"
            confidence = 25
        
        # Overall visibility too low
        elif avg_visibility < 0.5:
            message = "Move to better lighting/position"
            confidence = 30
        
        # Too close - shoulders too wide
        elif shoulder_width > 0.6:
            message = "Step back - Too close to camera"
            confidence = 35
        
        # Too far - shoulders too narrow
        elif shoulder_width < 0.15:
            message = "Move closer - Too far from camera"
            confidence = 40
        
        # Head too low in frame
        elif head_y > 0.35:
            message = "Step back - Show more of your outfit"
            confidence = 45
        
        # Missing shoulders or hips
        elif not shoulders_visible or not hips_visible:
            message = "Center yourself in frame"
            confidence = 50
        
        # Missing knees (need 3/4 body)
        elif not knees_visible:
            message = "Step back - Show at least 3/4 of outfit"
            confidence = 60
        
        # Good position!
        else:
            is_good_distance = True
            should_process = True
            message = "Perfect! 3/4 outfit visible"
            confidence = 90
        
        result = {
            "is_good_distance": is_good_distance,
            "message": message,
            "confidence": confidence,
            "should_process": should_process,
            "landmarks": results.pose_landmarks,
            "details": {
                "avg_visibility": round(avg_visibility, 3),
                "face_visibility": round(avg_face_visibility, 3),
                "face_visible": face_visible,
                "shoulder_width": round(shoulder_width, 3),
                "head_position_y": round(head_y, 3),
                "body_height": round(body_height, 3),
                "knees_visible": knees_visible,
                "hips_visible": hips_visible,
                "shoulders_visible": shoulders_visible
            }
        }
        
        # Cache the result
        self.last_check_result = result
        self.last_check_time = current_time
        
        return result
    
    def draw_distance_feedback(self, frame: np.ndarray, check_result: Dict) -> np.ndarray:
        """
        Draw minimalistic distance check feedback on frame
        Clean, modern UI without clutter
        
        Args:
            frame: BGR image
            check_result: Result from check_distance()
            
        Returns:
            Annotated frame with clean, minimal feedback
        """
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Choose color based on status
        if check_result["is_good_distance"]:
            primary_color = (0, 255, 0)  # Green
            bg_alpha = 0.15
        else:
            primary_color = (0, 165, 255)  # Orange
            bg_alpha = 0.2
        
        # MINIMALISTIC TOP BAR - Super thin colored line only
        cv2.line(annotated, (0, 0), (w, 0), primary_color, 3)
        
        # Main message - centered, clean font
        message = check_result["message"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        
        (text_width, text_height), baseline = cv2.getTextSize(message, font, font_scale, thickness)
        
        # Minimal dark background behind text only
        text_x = (w - text_width) // 2
        text_y = 40
        padding = 15
        
        overlay = annotated.copy()
        cv2.rectangle(overlay, 
                     (text_x - padding, text_y - text_height - padding),
                     (text_x + text_width + padding, text_y + padding),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
        
        # Draw message text - clean and simple
        cv2.putText(annotated, message, (text_x, text_y),
                   font, font_scale, (255, 255, 255), thickness)
        
        # Minimal progress indicator - bottom center
        if not check_result["is_good_distance"]:
            # Simple progress bar
            bar_width = 200
            bar_height = 6
            bar_x = (w - bar_width) // 2
            bar_y = h - 30
            
            # Background bar (subtle)
            cv2.rectangle(annotated, (bar_x, bar_y), 
                         (bar_x + bar_width, bar_y + bar_height),
                         (50, 50, 50), -1)
            
            # Progress fill
            progress = check_result['confidence']
            fill_width = int(bar_width * progress / 100)
            cv2.rectangle(annotated, (bar_x, bar_y),
                         (bar_x + fill_width, bar_y + bar_height),
                         primary_color, -1)
            
            # Small percentage text below bar
            perc_text = f"{progress}%"
            perc_font_scale = 0.4
            (perc_width, perc_height), _ = cv2.getTextSize(perc_text, font, perc_font_scale, 1)
            perc_x = (w - perc_width) // 2
            perc_y = bar_y + bar_height + 15
            
            cv2.putText(annotated, perc_text, (perc_x, perc_y),
                       font, perc_font_scale, (200, 200, 200), 1)
        
        # Success indicator - minimal checkmark
        else:
            # Simple, small checkmark at bottom center
            check_size = 40
            check_x = (w - check_size) // 2
            check_y = h - check_size - 15
            
            # Minimal circle outline
            center = (check_x + check_size//2, check_y + check_size//2)
            cv2.circle(annotated, center, check_size//2, primary_color, 2)
            
            # Simple checkmark
            cv2.putText(annotated, "✓", (check_x + 8, check_y + 32),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, primary_color, 2)
        
        return annotated
    
    def cleanup(self):
        """Release resources"""
        if hasattr(self, 'pose'):
            self.pose.close()


# Global instance
_distance_checker_pose = None

def get_distance_checker_pose() -> DistanceCheckerPose:
    """Get singleton instance of DistanceCheckerPose"""
    global _distance_checker_pose
    if _distance_checker_pose is None:
        if MEDIAPIPE_AVAILABLE:
            # Try to load config settings
            try:
                from config import (MEDIAPIPE_MODEL_COMPLEXITY, 
                                   MEDIAPIPE_MIN_DETECTION_CONFIDENCE, 
                                   MEDIAPIPE_MIN_TRACKING_CONFIDENCE)
                _distance_checker_pose = DistanceCheckerPose(
                    model_complexity=MEDIAPIPE_MODEL_COMPLEXITY,
                    min_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
                    min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE
                )
            except ImportError:
                # Use defaults if config not available
                _distance_checker_pose = DistanceCheckerPose()
        else:
            raise ImportError("MediaPipe not available. Install with: pip install mediapipe")
    return _distance_checker_pose
