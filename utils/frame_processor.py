"""
Frame processing utilities for backend
Optimizations for handling video frames and batch processing
"""
import cv2
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FrameProcessor:
    """
    Optimized frame processing for video detection
    """
    
    def __init__(self, max_dimension: int = 1280):
        """
        Initialize frame processor
        
        Args:
            max_dimension: Maximum width or height for processed frames
        """
        self.max_dimension = max_dimension
        self.frame_count = 0
        self.skip_count = 0
        
    def preprocess_frame(
        self, 
        frame: np.ndarray,
        target_size: Optional[Tuple[int, int]] = None
    ) -> np.ndarray:
        """
        Preprocess frame for detection
        
        Args:
            frame: Input frame as numpy array
            target_size: Optional target size (width, height)
            
        Returns:
            Preprocessed frame
        """
        try:
            # Resize if too large
            h, w = frame.shape[:2]
            
            if target_size:
                return cv2.resize(frame, target_size, interpolation=cv2.INTER_LINEAR)
            
            # Calculate new dimensions if frame is too large
            if max(w, h) > self.max_dimension:
                scale = self.max_dimension / max(w, h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                
                logger.debug(f"Resizing frame from {w}x{h} to {new_w}x{new_h}")
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error preprocessing frame: {e}")
            return frame
    
    def should_process_frame(self, frame_interval: int = 1) -> bool:
        """
        Determine if current frame should be processed (frame skipping logic)
        
        Args:
            frame_interval: Process every Nth frame
            
        Returns:
            bool: True if frame should be processed
        """
        self.frame_count += 1
        
        if self.frame_count % frame_interval == 0:
            return True
        
        self.skip_count += 1
        return False
    
    def validate_frame(self, frame: np.ndarray) -> bool:
        """
        Validate frame quality and content
        
        Args:
            frame: Input frame
            
        Returns:
            bool: True if frame is valid
        """
        if frame is None or frame.size == 0:
            return False
        
        # Check dimensions
        h, w = frame.shape[:2]
        if w < 50 or h < 50:
            logger.warning(f"Frame too small: {w}x{h}")
            return False
        
        # Check if frame is mostly black (potential camera issue)
        mean_brightness = np.mean(frame)
        if mean_brightness < 10:
            logger.warning("Frame appears to be mostly black")
            return False
        
        return True
    
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply enhancement to improve detection quality
        
        Args:
            frame: Input frame
            
        Returns:
            Enhanced frame
        """
        try:
            # Normalize lighting
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge and convert back
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Frame enhancement failed: {e}")
            return frame
    
    def get_stats(self) -> dict:
        """
        Get processing statistics
        
        Returns:
            dict: Processing statistics
        """
        return {
            "total_frames": self.frame_count,
            "processed_frames": self.frame_count - self.skip_count,
            "skipped_frames": self.skip_count,
            "skip_rate": self.skip_count / self.frame_count if self.frame_count > 0 else 0
        }
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.frame_count = 0
        self.skip_count = 0


def optimize_detection_params(image_size: Tuple[int, int], device: str = 'cpu') -> dict:
    """
    Get optimized detection parameters based on image size and device
    
    Args:
        image_size: Tuple of (width, height)
        device: Device type ('cpu' or 'cuda')
        
    Returns:
        dict: Optimized parameters
    """
    w, h = image_size
    total_pixels = w * h
    
    # Base parameters
    params = {
        'conf': 0.25,
        'iou': 0.45,
        'max_det': 300,
        'half': False
    }
    
    # Adjust based on image size
    if total_pixels < 640 * 480:  # Small image
        params['conf'] = 0.3
        params['max_det'] = 100
    elif total_pixels > 1920 * 1080:  # Large image
        params['conf'] = 0.2
        params['max_det'] = 500
    
    # Enable half precision for GPU
    if device == 'cuda':
        params['half'] = True
    
    return params
