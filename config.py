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

# Compliance Configuration - REMOVE t-shirt and shorts
COMPLIANT_CLOTHES = {
    "full sleeve shirt", "half sleeve shirt", 
    "pants", "kurthi", "id card"
}

# Explicitly non-compliant items
NON_COMPLIANT_CLOTHES = {
    "t-shirt", "shorts", "tshirt", "tee shirt", "t shirt", "short pants"
}

# Alternative spellings and variations (only for compliant items)
COMPLIANT_VARIANTS = {
    "full sleeve shirt": ["full sleeves shirt", "full-sleeve shirt", "long sleeve shirt"],
    "half sleeve shirt": ["half sleeves shirt", "half-sleeve shirt", "short sleeve shirt"],
    "pants": ["trousers", "formal pants"],
    "kurthi": ["kurti", "kurta"],
    "id card": ["id", "identity card", "badge"]
}

# Compliance Rules
COMPLIANCE_RULES = {
    "min_confidence": 0.5,  # Minimum confidence threshold for detections
    "require_all_compliant": True  # All detected items must be compliant
}