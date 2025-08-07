from config import ALLOWED_CLOTHES

def is_compliant(detected_clothes):
    # non_compliant_items = []

    # for item in detected_clothes:
    #     if item["class"].lower() not in ALLOWED_CLOTHES:
    #         non_compliant_items.append(item["class"])

    # if non_compliant_items:
    #     return False, list(set(non_compliant_items))
    return True, []
