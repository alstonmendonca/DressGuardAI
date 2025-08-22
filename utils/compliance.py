def is_compliant(detected_clothes):
    """
    Check if detected clothing items are compliant based on predefined rules.
    
    Args:
        detected_clothes: List of dictionaries containing detection results
        
    Returns:
        tuple: (is_compliant, non_compliant_items)
    """

    # Compliance Configuration - REMOVE t-shirt and shorts
    COMPLIANT_CLOTHES = {
        "full sleeve shirt", "half sleeve shirt", 
        "pants", "kurthi", "id card"
    }

    # Alternative spellings and variations - REMOVE t-shirt and shorts entries
    COMPLIANT_VARIANTS = {
        "full sleeve shirt": ["full sleeves shirt", "full-sleeve shirt", "long sleeve shirt"],
        "half sleeve shirt": ["half sleeves shirt", "half-sleeve shirt", "short sleeve shirt"],
        "pants": ["trousers", "formal pants"],
        "kurthi": ["kurti", "kurta"],
        "id card": ["id", "identity card", "badge"]
    }

    # Explicitly non-compliant items (optional)
    NON_COMPLIANT_CLOTHES = {
        "t-shirt", "shorts", "tshirt", "tee shirt", "t shirt", "short pants"
    }

    # Compliance Rules
    COMPLIANCE_RULES = {
        "min_confidence": 0.5,  # Minimum confidence threshold for detections
        "require_all_compliant": True  # All detected items must be compliant
    }
    
    non_compliant_items = []
    detected_classes = set()
    
    for item in detected_clothes:
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