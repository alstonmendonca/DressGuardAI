"""
DressGuard Configuration
Central configuration for models, compliance rules, and application settings
"""

# ============================================================================
# Model Configuration
# ============================================================================

# Models are now discovered dynamically from the models/ folder
# Just drop your .pt files in models/ and they'll be auto-detected
MODELS_FOLDER = "models"  # Folder containing YOLO model files
DEFAULT_MODEL = None      # Will automatically use the first discovered model

# ============================================================================
# Compliance Configuration
# ============================================================================

# NOTE: Only use class names that actually exist in your models!
# Your models detect: Full Sleeves Shirt, Half Sleeves Shirt, ID Card, Kurti, Pants, Shorts, T-Shirt

# Compliant clothing items (approved for wear) - must match model classes
COMPLIANT_CLOTHES = {
    "full sleeves shirt",  # Actual model class
    "half sleeves shirt",  # Actual model class
    "pants",               # Actual model class
    "kurti",               # Actual model class
    "id card"              # Actual model class
}

# Explicitly non-compliant items (prohibited) - must match model classes
NON_COMPLIANT_CLOTHES = {
    "t-shirt",  # Actual model class
    "shorts"    # Actual model class
}

# Compliance Rules
COMPLIANCE_RULES = {
    "min_confidence": 0.5,           # Minimum confidence threshold for detections
    "require_all_compliant": True,   # All detected items must be compliant
    "strict_mode": False,            # If True, unknown items are non-compliant
}

# ============================================================================
# Application Configuration
# ============================================================================

# File Upload Settings
MAX_FILE_SIZE_MB = 10
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MAX_IMAGE_DIMENSION = 4096
MIN_IMAGE_DIMENSION = 50

# Detection Settings
DEFAULT_CONFIDENCE_THRESHOLD = 0.25  # Lower threshold for YOLO inference
YOLO_IMAGE_SIZE = 640                # Input size for YOLO model

# Webcam Detection Settings
WEBCAM_DETECTION_INTERVAL = 2.0      # Seconds between YOLO detections (only used when distance check disabled)
WEBCAM_ENABLE_DISTANCE_CHECK = True  # Enable distance/position checking before detection
WEBCAM_FPS_LIMIT = 100               # Max FPS for webcam stream (actual will be lower)
WEBCAM_JPEG_QUALITY = 75             # JPEG quality (0-100, lower = faster but lower quality)
WEBCAM_SKIP_FRAMES = 0               # Skip N frames between processing (0 = process all frames, 1 = skip every other, 2 = skip 2 out of 3)

# Distance Check Mode Switching
WEBCAM_REQUIRED_GOOD_FRAMES = 5      # Good frames needed to start real-time detection
WEBCAM_ALLOWED_BAD_FRAMES = 10       # Bad frames allowed before returning to distance check

# API Settings
API_TITLE = "DressGuard API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "AI-powered clothing compliance detection system"

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# Advanced Settings (Optional)
# ============================================================================

# Model Performance Settings
ENABLE_GPU = True                    # Use GPU if available
HALF_PRECISION = False               # Use FP16 for faster inference (GPU only)

# Cache Settings
CACHE_ENABLED = False
CACHE_TTL_SECONDS = 300              # Time-to-live for cached results
