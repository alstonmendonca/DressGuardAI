"""
Dynamic Model Discovery and Management
Automatically discovers and loads YOLO models from the models folder
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class ModelDiscovery:
    """Discovers and manages YOLO models dynamically"""
    
    def __init__(self, models_folder: str = "models"):
        self.models_folder = models_folder
        self._models_cache = {}
        self._classes_cache = {}
        
    def discover_models(self) -> Dict[str, Dict]:
        """
        Discover all .pt model files in the models folder
        
        Returns:
            Dict mapping model_id to model metadata
        """
        models = {}
        
        if not os.path.exists(self.models_folder):
            logger.warning(f"Models folder not found: {self.models_folder}")
            return models
        
        # Find all .pt files
        model_files = Path(self.models_folder).glob("*.pt")
        
        for model_path in model_files:
            model_id = model_path.stem  # filename without extension
            
            try:
                # Load model to get classes
                classes = self._get_model_classes(str(model_path))
                
                models[model_id] = {
                    "id": model_id,
                    "path": str(model_path),
                    "classes": classes,
                    "class_count": len(classes)
                }
                
                logger.info(f"Discovered model: {model_id} ({len(classes)} classes)")
                
            except Exception as e:
                logger.error(f"Error loading model {model_path}: {e}")
                continue
        
        self._models_cache = models
        return models
    
    def _get_model_classes(self, model_path: str) -> List[str]:
        """
        Extract class names from a YOLO model
        
        Args:
            model_path: Path to .pt model file
            
        Returns:
            List of class names
        """
        # Check cache first
        if model_path in self._classes_cache:
            return self._classes_cache[model_path]
        
        try:
            model = YOLO(model_path)
            
            if hasattr(model, 'names') and model.names:
                # YOLO model.names is a dict {id: name}
                classes = [name for name in model.names.values()]
                self._classes_cache[model_path] = classes
                return classes
            else:
                logger.warning(f"Model {model_path} has no class names")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting classes from {model_path}: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """
        Get information about a specific model
        
        Args:
            model_id: Model identifier (filename without .pt)
            
        Returns:
            Model metadata dict or None if not found
        """
        if not self._models_cache:
            self.discover_models()
        
        return self._models_cache.get(model_id)
    
    def get_all_models(self) -> Dict[str, Dict]:
        """Get all discovered models"""
        if not self._models_cache:
            self.discover_models()
        
        return self._models_cache
    
    def model_exists(self, model_id: str) -> bool:
        """Check if a model exists"""
        if not self._models_cache:
            self.discover_models()
        
        return model_id in self._models_cache
    
    def get_model_path(self, model_id: str) -> Optional[str]:
        """Get the file path for a model"""
        model_info = self.get_model_info(model_id)
        return model_info["path"] if model_info else None
    
    def get_all_unique_classes(self) -> List[str]:
        """
        Get all unique classes across all models
        
        Returns:
            Sorted list of unique class names
        """
        if not self._models_cache:
            self.discover_models()
        
        all_classes = set()
        for model_info in self._models_cache.values():
            all_classes.update(model_info["classes"])
        
        return sorted(list(all_classes))
    
    def refresh(self):
        """Refresh the model cache (re-discover models)"""
        self._models_cache.clear()
        self._classes_cache.clear()
        return self.discover_models()


# Global instance
_model_discovery = None

def get_model_discovery(models_folder: str = "models") -> ModelDiscovery:
    """Get singleton instance of ModelDiscovery"""
    global _model_discovery
    if _model_discovery is None:
        _model_discovery = ModelDiscovery(models_folder)
        _model_discovery.discover_models()
    return _model_discovery
