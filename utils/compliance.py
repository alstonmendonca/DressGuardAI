def is_compliant(detected_clothes):
    """
    Check if detected clothing items are compliant based on predefined rules.
    
    Args:
        detected_clothes: List of dictionaries containing detection results
        
    Returns:
        tuple: (is_compliant, non_compliant_items)
    """
    # Define compliant clothing classes (case-insensitive matching)
    COMPLIANT_CLOTHES = {
        "full sleeve shirt", "half sleeve shirt", "t-shirt", 
        "pants", "shorts", "kurthi", "id card"
    }
    
    # Alternative spellings and variations that should be considered compliant
    COMPLIANT_VARIANTS = {
        "full sleeve shirt": ["full sleeves shirt", "full-sleeve shirt", "long sleeve shirt"],
        "half sleeve shirt": ["half sleeves shirt", "half-sleeve shirt", "short sleeve shirt"],
        "t-shirt": ["tshirt", "tee shirt", "t shirt"],
        "pants": ["trousers", "formal pants"],
        "shorts": ["short pants"],
        "kurthi": ["kurti", "kurta"],
        "id card": ["id", "identity card", "badge"]
    }
    
    non_compliant_items = []
    detected_classes = set()
    
    for item in detected_clothes:
        class_name = item["class"].lower().strip()
        detected_classes.add(class_name)
        
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