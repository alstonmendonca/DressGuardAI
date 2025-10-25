from ultralytics import YOLO
import cv2
import numpy as np
from config import DEFAULT_MODEL, MODELS_FOLDER
from utils.model_discovery import get_model_discovery
import logging
import os

logger = logging.getLogger(__name__)

class DressDetector:
    def __init__(self):
        """Initialize the DressDetector with the default model"""
        self.model_discovery = get_model_discovery(MODELS_FOLDER)
        self.current_model = None
        self.model = None
        self.clothing_classes = {}
        
        # Discover available models
        available_models = self.model_discovery.get_all_models()
        logger.info(f"Discovered {len(available_models)} models: {list(available_models.keys())}")
        
        if not available_models:
            raise RuntimeError(f"No models found in {MODELS_FOLDER}")
        
        # Determine which model to load
        model_to_load = DEFAULT_MODEL if DEFAULT_MODEL else list(available_models.keys())[0]
        
        # Load the selected model
        if not self._load_model(model_to_load):
            # Try to load the first available model if selected model fails
            if DEFAULT_MODEL and available_models:
                first_model = list(available_models.keys())[0]
                logger.warning(f"Default model '{DEFAULT_MODEL}' not found, using '{first_model}'")
                if not self._load_model(first_model):
                    raise RuntimeError(f"Failed to initialize detector")
            else:
                raise RuntimeError(f"Failed to initialize detector")
    
    def _load_model(self, model_name: str) -> bool:
        """
        Load a YOLO model by name
        
        Args:
            model_name: Model identifier (filename without .pt)
            
        Returns:
            bool: True if successful, False otherwise
        """
        model_info = self.model_discovery.get_model_info(model_name)
        
        if not model_info:
            logger.error(f"Model '{model_name}' not found in {MODELS_FOLDER}")
            return False
        
        model_path = model_info["path"]
        
        try:
            logger.info(f"Loading model: {model_name} from {model_path}")
            self.model = YOLO(model_path)
            self.current_model = model_name
            
            # Cache the clothing classes for this model
            self.clothing_classes[model_name] = self._get_clothing_classes()
            
            logger.info(f"Successfully loaded model '{model_name}' with {len(self.clothing_classes[model_name])} classes")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}", exc_info=True)
            return False
    
    def _get_clothing_classes(self):
        """
        Helper method to get clothing classes from current model
        
        Returns:
            set: Set of class names from the model
        """
        try:
            if self.model and hasattr(self.model, 'names'):
                return set(self.model.names.values())
            return set()
        except Exception as e:
            logger.error(f"Error getting clothing classes: {e}")
            return set()

    def switch_model(self, model_name: str) -> bool:
        """
        Switch to specified clothing detection model
        
        Args:
            model_name: Key from MODELS config dictionary
            
        Returns:
            bool: True if switch successful, False otherwise
        """
        if model_name == self.current_model:
            logger.info(f"Already using model: {model_name}")
            return True
        
        # Store current model as backup
        backup_model = self.model
        backup_model_name = self.current_model
        
        # Try to load the new model
        if self._load_model(model_name):
            logger.info(f"Successfully switched from '{backup_model_name}' to '{model_name}'")
            return True
        else:
            # Restore the backup model if switch failed
            logger.warning(f"Failed to switch to '{model_name}', keeping '{backup_model_name}'")
            self.model = backup_model
            self.current_model = backup_model_name
            return False
    
    def detect(self, image: np.ndarray, confidence_threshold: float = 0.25):
        """
        Detect clothing items in image using current model
        
        Args:
            image: Input image as numpy array
            confidence_threshold: Minimum confidence for detections (default: 0.25)
            
        Returns:
            list: List of detection dictionaries with class, bbox, confidence, and model
        """
        if self.model is None:
            logger.error("No model loaded for detection")
            return []
        
        try:
            # Run inference
            results = self.model(image, conf=confidence_threshold)
            
            if not results or len(results) == 0:
                logger.debug("No detections found in image")
                return []
            
            detections = results[0]
            clothes = []
            
            # Process each detection
            for box in detections.boxes:
                try:
                    cls_id = int(box.cls[0])
                    class_name = self.model.names[cls_id]
                    bbox = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])

                    clothes.append({
                        "class": class_name,
                        "bbox": bbox,
                        "confidence": confidence,
                        "model": self.current_model
                    })
                except Exception as e:
                    logger.warning(f"Error processing detection box: {e}")
                    continue
            
            logger.info(f"Detected {len(clothes)} items using model '{self.current_model}'")
            return clothes
            
        except Exception as e:
            logger.error(f"Error during detection: {e}", exc_info=True)
            return []

    def get_available_models(self):
        """
        Return list of available clothing detection models
        
        Returns:
            list: List of model keys from MODELS config
        """
        return list(MODELS.keys())
    
    def get_model_info(self, model_name: str = None):
        """
        Get information about a specific model or the current model
        
        Args:
            model_name: Optional model name. If None, returns current model info
            
        Returns:
            dict: Model information including name, path, description, and classes
        """
        target_model = model_name if model_name else self.current_model
        
        if target_model not in MODELS:
            return None
        
        info = MODELS[target_model].copy()
        info['name'] = target_model
        info['is_current'] = (target_model == self.current_model)
        info['classes'] = list(self.clothing_classes.get(target_model, []))
        
        return info