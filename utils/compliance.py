from config import COMPLIANT_CLOTHES, NON_COMPLIANT_CLOTHES, COMPLIANCE_RULES
import logging
import json
import os
from typing import Dict, Set, List, Tuple

logger = logging.getLogger(__name__)


class ComplianceManager:
    """Manages compliance rules with ability to dynamically update them"""
    
    def __init__(self, config_file: str = "compliance_config.json"):
        """Initialize compliance manager with optional persistent storage"""
        self.config_file = config_file
        self.compliant_classes = set(COMPLIANT_CLOTHES)
        self.non_compliant_classes = set(NON_COMPLIANT_CLOTHES)
        self.min_confidence = COMPLIANCE_RULES.get("min_confidence", 0.5)
        
        # Load from file if exists
        self.load_config()
    
    def load_config(self):
        """Load compliance configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.compliant_classes = set(config.get("compliant", []))
                    self.non_compliant_classes = set(config.get("non_compliant", []))
                    self.min_confidence = config.get("min_confidence", 0.5)
                    logger.info(f"Loaded compliance config from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading compliance config: {e}")
    
    def save_config(self):
        """Save compliance configuration to file"""
        try:
            config = {
                "compliant": list(self.compliant_classes),
                "non_compliant": list(self.non_compliant_classes),
                "min_confidence": self.min_confidence
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved compliance config to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving compliance config: {e}")
    
    def set_compliant_classes(self, classes: List[str]):
        """Set the list of compliant clothing classes"""
        self.compliant_classes = set(c.lower().strip() for c in classes)
        self.save_config()
        logger.info(f"Updated compliant classes: {self.compliant_classes}")
    
    def set_non_compliant_classes(self, classes: List[str]):
        """Set the list of non-compliant clothing classes"""
        self.non_compliant_classes = set(c.lower().strip() for c in classes)
        self.save_config()
        logger.info(f"Updated non-compliant classes: {self.non_compliant_classes}")
    
    def add_compliant_class(self, class_name: str):
        """Add a single class to compliant list"""
        class_name = class_name.lower().strip()
        self.compliant_classes.add(class_name)
        # Remove from non-compliant if present
        self.non_compliant_classes.discard(class_name)
        self.save_config()
    
    def add_non_compliant_class(self, class_name: str):
        """Add a single class to non-compliant list"""
        class_name = class_name.lower().strip()
        self.non_compliant_classes.add(class_name)
        # Remove from compliant if present
        self.compliant_classes.discard(class_name)
        self.save_config()
    
    def remove_class(self, class_name: str):
        """Remove a class from both lists (make it neutral)"""
        class_name = class_name.lower().strip()
        self.compliant_classes.discard(class_name)
        self.non_compliant_classes.discard(class_name)
        self.save_config()
    
    def get_config(self) -> Dict:
        """Get current compliance configuration"""
        return {
            "compliant_classes": sorted(list(self.compliant_classes)),
            "non_compliant_classes": sorted(list(self.non_compliant_classes)),
            "min_confidence": self.min_confidence
        }
    
    def check_compliance(self, detected_clothes: List[Dict]) -> Tuple[bool, List[str], Dict]:
        """
        Check if detected clothing items are compliant
        
        Args:
            detected_clothes: List of dictionaries containing detection results
            
        Returns:
            tuple: (is_compliant, non_compliant_items, details)
        """
        non_compliant_items = []
        detected_classes = set()
        low_confidence_items = []
        compliant_items = []
        neutral_items = []
        
        for item in detected_clothes:
            class_name = item["class"].lower().strip()
            confidence = item.get("confidence", 0.0)
            
            # Track low confidence detections
            if confidence < self.min_confidence:
                low_confidence_items.append({
                    "class": item["class"],
                    "confidence": confidence
                })
                logger.debug(f"Skipping low-confidence detection: {class_name} ({confidence:.2f})")
                continue
                
            detected_classes.add(class_name)
            
            # Check if explicitly non-compliant
            if class_name in self.non_compliant_classes:
                non_compliant_items.append({
                    "class": item["class"],
                    "confidence": confidence,
                    "reason": "Prohibited item"
                })
                logger.info(f"Non-compliant item detected: {class_name}")
                continue
                
            # Check if compliant
            if class_name in self.compliant_classes:
                compliant_items.append(item["class"])
                continue
            
            # Item is neutral (not in either list)
            neutral_items.append(item["class"])
            logger.info(f"Neutral item detected: {class_name}")
        
        # Detailed report
        details = {
            "total_detections": len(detected_clothes),
            "high_confidence_detections": len(detected_classes),
            "low_confidence_skipped": len(low_confidence_items),
            "compliant_items": compliant_items,
            "non_compliant_items": non_compliant_items,
            "neutral_items": neutral_items,
            "non_compliant_count": len(non_compliant_items)
        }
        
        non_compliant_names = [item["class"] for item in non_compliant_items]
        non_compliant_names = list(dict.fromkeys(non_compliant_names))
        
        is_compliant_result = len(non_compliant_items) == 0
        
        logger.info(f"Compliance check: {'PASSED' if is_compliant_result else 'FAILED'} - "
                    f"{len(compliant_items)} compliant, {len(non_compliant_items)} non-compliant, "
                    f"{len(neutral_items)} neutral")
        
        return is_compliant_result, non_compliant_names, details

def is_compliant(detected_clothes):
    """
    Check if detected clothing items are compliant based on predefined rules.
    
    Args:
        detected_clothes: List of dictionaries containing detection results
        
    Returns:
        tuple: (is_compliant, non_compliant_items)
    """
    
    non_compliant_items = []
    detected_classes = set()
    low_confidence_items = []
    compliant_items = []
    
    min_confidence = COMPLIANCE_RULES.get("min_confidence", 0.5)
    
    for item in detected_clothes:
        class_name = item["class"].lower().strip()
        confidence = item.get("confidence", 0.0)
        
        # Track low confidence detections for logging
        if confidence < min_confidence:
            low_confidence_items.append({
                "class": item["class"],
                "confidence": confidence
            })
            logger.debug(f"Skipping low-confidence detection: {class_name} ({confidence:.2f})")
            continue
            
        detected_classes.add(class_name)
        
        # Check if explicitly non-compliant
        if class_name in NON_COMPLIANT_CLOTHES:
            non_compliant_items.append({
                "class": item["class"],
                "confidence": confidence,
                "reason": "Prohibited item"
            })
            logger.info(f"Non-compliant item detected: {class_name}")
            continue
            
        # Check if this class is directly compliant
        if class_name in COMPLIANT_CLOTHES:
            compliant_items.append(item["class"])
            continue
            
        # Not compliant - mark as non-compliant
        non_compliant_items.append({
            "class": item["class"],
            "confidence": confidence,
            "reason": "Not in approved list"
        })
        logger.info(f"Unknown/non-compliant item: {class_name}")
    
    # Generate detailed compliance report
    compliance_report = {
        "total_detections": len(detected_clothes),
        "high_confidence_detections": len(detected_classes),
        "low_confidence_skipped": len(low_confidence_items),
        "compliant_items": compliant_items,
        "non_compliant_count": len(non_compliant_items)
    }
    
    # Extract just class names for backward compatibility
    non_compliant_names = [item["class"] for item in non_compliant_items]
    
    # Remove duplicates while preserving original capitalization
    non_compliant_names = list(dict.fromkeys(non_compliant_names))
    
    is_compliant_result = len(non_compliant_items) == 0
    
    logger.info(f"Compliance check: {'PASSED' if is_compliant_result else 'FAILED'} - "
                f"{len(compliant_items)} compliant, {len(non_compliant_items)} non-compliant")
    
    return is_compliant_result, non_compliant_names


def get_compliance_details(detected_clothes):
    """
    Get detailed compliance information including statistics and categorization.
    
    Args:
        detected_clothes: List of dictionaries containing detection results
        
    Returns:
        dict: Detailed compliance information
    """
    compliant_items = []
    non_compliant_items = []
    low_confidence_items = []
    unknown_items = []
    
    min_confidence = COMPLIANCE_RULES.get("min_confidence", 0.5)
    
    for item in detected_clothes:
        class_name = item["class"].lower().strip()
        confidence = item.get("confidence", 0.0)
        
        detection_info = {
            "class": item["class"],
            "confidence": confidence,
            "bbox": item.get("bbox", [])
        }
        
        if confidence < min_confidence:
            low_confidence_items.append(detection_info)
            continue
        
        # Check categories
        if class_name in NON_COMPLIANT_CLOTHES:
            detection_info["reason"] = "Prohibited item"
            non_compliant_items.append(detection_info)
        elif class_name in COMPLIANT_CLOTHES:
            detection_info["category"] = "Direct match"
            compliant_items.append(detection_info)
        else:
            # Not in compliant or non-compliant lists - mark as unknown
            detection_info["reason"] = "Not in approved list"
            unknown_items.append(detection_info)
    
    return {
        "is_compliant": len(non_compliant_items) == 0 and len(unknown_items) == 0,
        "summary": {
            "total": len(detected_clothes),
            "compliant": len(compliant_items),
            "non_compliant": len(non_compliant_items),
            "unknown": len(unknown_items),
            "low_confidence": len(low_confidence_items)
        },
        "compliant_items": compliant_items,
        "non_compliant_items": non_compliant_items,
        "unknown_items": unknown_items,
        "low_confidence_items": low_confidence_items,
        "rules_applied": {
            "min_confidence": min_confidence,
            "require_all_compliant": COMPLIANCE_RULES.get("require_all_compliant", True)
        }
    }