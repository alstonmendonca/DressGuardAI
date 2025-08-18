# Model Configuration
MODELS = {
    "best": {
        "path": "models/best.pt",
        "display_name": "Best Model",
        "description": "Primary clothing detection model"
    },
    "yolov8n": {
        "path": "models/yolov8n.pt",
        "display_name": "YOLOv8 Nano",
        "description": "Lightweight clothing detection model"
    }
}

DEFAULT_MODEL = "best"  # Key from MODELS dictionary

# Clothing Configuration
ALLOWED_CLOTHES = {
    "shirt", 
    "formal shirt", 
    "formal pants", 
    "trousers", 
    "formal shoes"
}

# Compliance Rules (optional - you could add specific rules here)
COMPLIANCE_RULES = {
    "min_confidence": 0.5,  # Minimum confidence threshold for detections
    "require_formal_shoes": True  # Example rule
}