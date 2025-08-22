from ultralytics import YOLO
import cv2
import numpy as np
from config import MODELS, DEFAULT_MODEL

class DressDetector:
    def __init__(self):
        # Default to your best clothing detection model
        self.current_model = DEFAULT_MODEL
        self.model = YOLO(MODELS[self.current_model]["path"])
        self.clothing_classes = {
            self.current_model: self._get_clothing_classes()
        }
    
    def _get_clothing_classes(self):
        """Helper method to get clothing classes from current model"""
        return set(self.model.names.values()) if hasattr(self.model, 'names') else set()

    def switch_model(self, model_name: str):
        """Switch to specified clothing detection model"""
        if model_name in MODELS:
            try:
                self.current_model = model_name
                self.model = YOLO(MODELS[model_name]["path"])
                # Update clothing classes for the new model
                self.clothing_classes[model_name] = self._get_clothing_classes()
                return True
            except Exception as e:
                print(f"Error loading model {model_name}: {e}")
                return False
        return False
    
    def detect(self, image: np.ndarray):
        """Detect clothing items in image using current model"""
        results = self.model(image)
        detections = results[0]

        clothes = []
        for box in detections.boxes:
            cls_id = int(box.cls[0])
            class_name = self.model.names[cls_id]
            bbox = box.xyxy[0].tolist()
            confidence = float(box.conf[0])

            # Only include if it's a clothing item (should be all for your specialized models)
            clothes.append({
                "class": class_name,
                "bbox": bbox,
                "confidence": confidence,
                "model": self.current_model
            })

        return clothes

    def get_available_models(self):
        """Return list of available clothing detection models"""
        return list(MODELS.keys())