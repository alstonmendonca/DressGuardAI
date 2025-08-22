from config import COMPLIANT_CLOTHES, COMPLIANT_VARIANTS, NON_COMPLIANT_CLOTHES, COMPLIANCE_RULES

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
    
    for item in detected_clothes:
        # Apply confidence threshold from rules
        if "confidence" in item and item["confidence"] < COMPLIANCE_RULES["min_confidence"]:
            continue  # Skip low-confidence detections
            
        class_name = item["class"].lower().strip()
        detected_classes.add(class_name)
        
        # Check if explicitly non-compliant
        if class_name in NON_COMPLIANT_CLOTHES:
            non_compliant_items.append(item["class"])
            continue
            
        # Check if this class is directly compliant
        if class_name in COMPLIANT_CLOTHES:
            continue
            
        # Check if this class is a variant of a compliant item
        is_variant_compliant = False
        for compliant_item, variants in COMPLIANT_VARIANTS.items():
            if class_name in variants or class_name == compliant_item:
                is_variant_compliant = True
                break
                
        if not is_variant_compliant:
            non_compliant_items.append(item["class"])
    
    # Remove duplicates while preserving original capitalization
    non_compliant_items = list(dict.fromkeys(non_compliant_items))
    
    if non_compliant_items:
        return False, non_compliant_items
    return True, []