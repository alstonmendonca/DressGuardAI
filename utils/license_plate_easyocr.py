"""
License Plate OCR using EasyOCR
Replaces PaddleOCR with EasyOCR for better accuracy and GPU support
"""

import cv2
import easyocr
import numpy as np
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class LicensePlateOCR:
    """
    License plate OCR using EasyOCR with preprocessing
    """
    
    def __init__(self):
        """Initialize EasyOCR reader with GPU support if available"""
        self.reader = None
        self._initialize_reader()
    
    def _initialize_reader(self):
        """Initialize EasyOCR reader, trying GPU first then falling back to CPU"""
        try:
            logger.info("Initializing EasyOCR with GPU support...")
            self.reader = easyocr.Reader(['en'], gpu=True)
            logger.info("EasyOCR initialized successfully with GPU")
        except Exception as e:
            logger.warning(f"GPU initialization failed: {e}. Falling back to CPU...")
            try:
                self.reader = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized successfully with CPU")
            except Exception as e2:
                logger.error(f"Failed to initialize EasyOCR: {e2}")
                self.reader = None
    
    def preprocess_license_plate(self, crop: np.ndarray) -> Optional[np.ndarray]:
        """
        Preprocess license plate crop for better OCR accuracy
        
        Args:
            crop: Cropped license plate image (BGR format)
            
        Returns:
            Preprocessed image (RGB format) or None if crop is too small
        """
        if crop is None or crop.size == 0:
            return None
        
        # Check minimum size
        h, w = crop.shape[:2]
        if h < 5 or w < 15:
            logger.warning(f"License plate crop too small: {w}x{h}")
            return None
        
        # Upscale for better OCR (3x scale)
        crop = cv2.resize(crop, (w*3, h*3), interpolation=cv2.INTER_LINEAR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Convert back to RGB for EasyOCR
        rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        
        return rgb
    
    def extract_text(self, image: np.ndarray, preprocess: bool = True) -> str:
        """
        Extract text from license plate image
        
        Args:
            image: License plate image (BGR format)
            preprocess: Whether to preprocess the image
            
        Returns:
            Extracted text (alphanumeric characters only)
        """
        if self.reader is None:
            logger.error("EasyOCR reader not initialized")
            return ""
        
        try:
            # Preprocess if requested
            if preprocess:
                processed = self.preprocess_license_plate(image)
                if processed is None:
                    return ""
            else:
                processed = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Perform OCR
            results = self.reader.readtext(processed, detail=0)
            
            # Join all detected text (remove spaces)
            text = "".join(results)
            
            # Clean text: keep only alphanumeric characters
            text = ''.join(c for c in text if c.isalnum())
            
            logger.info(f"OCR extracted text: '{text}'")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""
    
    def extract_from_boxes(self, frame: np.ndarray, boxes: List[dict]) -> List[str]:
        """
        Extract license plate text from multiple detected boxes
        
        Args:
            frame: Full frame image (BGR format)
            boxes: List of detection boxes with xyxy coordinates and labels
            
        Returns:
            List of extracted license plate texts
        """
        lp_texts = []
        h_img, w_img = frame.shape[:2]
        
        for box in boxes:
            label = box.get('label', '').lower()
            
            # Only process license plate detections
            if 'license' in label or 'plate' in label:
                xyxy = box.get('xyxy', [])
                if len(xyxy) != 4:
                    continue
                
                # Add small padding
                pad = 5
                x1 = max(0, int(xyxy[0]) - pad)
                y1 = max(0, int(xyxy[1]) - pad)
                x2 = min(w_img, int(xyxy[2]) + pad)
                y2 = min(h_img, int(xyxy[3]) + pad)
                
                # Crop license plate region
                lp_crop = frame[y1:y2, x1:x2]
                
                # Extract text
                text = self.extract_text(lp_crop, preprocess=True)
                
                if text:
                    lp_texts.append(text)
                    logger.info(f"License plate detected: {text}")
        
        return lp_texts
    
    def is_available(self) -> bool:
        """Check if OCR reader is available"""
        return self.reader is not None


# Global instance
_ocr_instance = None

def get_ocr_instance() -> LicensePlateOCR:
    """Get or create the global OCR instance"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = LicensePlateOCR()
    return _ocr_instance


def extract_license_plate_text(image: np.ndarray) -> str:
    """
    Convenience function to extract license plate text from an image
    
    Args:
        image: License plate image (BGR format)
        
    Returns:
        Extracted text
    """
    ocr = get_ocr_instance()
    return ocr.extract_text(image)
