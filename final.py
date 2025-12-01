import cv2
from ultralytics import YOLO
import easyocr
import numpy as np

# -----------------------------
MODEL_PATH = r"C:\Users\alsto\Desktop\DressGuard\models\Vehicle Helmet.pt"
INPUT_IMAGE = r"C:\Users\alsto\Desktop\How-do-you-ride-a-Scooty-perfectly.jpg"
OUTPUT_IMAGE = "output_image.jpg"
# -----------------------------

# Initialize YOLO (CPU)
model = YOLO(MODEL_PATH)
class_names = model.names

# Initialize EasyOCR reader (GPU if available, else CPU)
try:
    reader = easyocr.Reader(['en'], gpu=True)
except:
    reader = easyocr.Reader(['en'], gpu=False)

# -----------------------------
# Optional: preprocess LP crop
# -----------------------------
def preprocess_lp(crop):
    """Upscale, enhance contrast, optional deskew for license plate OCR."""
    if crop.shape[0] < 5 or crop.shape[1] < 15:
        return None  # skip too tiny crops

    h, w = crop.shape[:2]
    crop = cv2.resize(crop, (w*3, h*3), interpolation=cv2.INTER_LINEAR)  # upscale more

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # Optional: convert back to RGB for EasyOCR
    rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return rgb

# -----------------------------
# Read image
# -----------------------------
frame = cv2.imread(INPUT_IMAGE)
h_img, w_img = frame.shape[:2]

# YOLO inference
results = model(frame, conf=0.25, device='cpu')[0]

# Store license plate texts
lp_texts = []

for b in results.boxes:
    xyxy = b.xyxy[0].cpu().numpy().astype(int)
    cls = int(b.cls[0])
    label = class_names[cls]

    # Add small padding around the box
    pad = 5
    x1 = max(0, xyxy[0] - pad)
    y1 = max(0, xyxy[1] - pad)
    x2 = min(w_img, xyxy[2] + pad)
    y2 = min(h_img, xyxy[3] + pad)

    # Draw box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
    cv2.putText(frame, label, (x1, y1-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)

    # OCR for license plate
    if label.lower() == "license plate":
        lp_crop = frame[y1:y2, x1:x2]
        processed_crop = preprocess_lp(lp_crop)
        if processed_crop is not None:
            result = reader.readtext(processed_crop)
            text = "".join([res[1] for res in result])  # join without extra spaces
            if text.strip():
                lp_texts.append(text.strip())

# -----------------------------
# Save annotated image
# -----------------------------
cv2.imwrite(OUTPUT_IMAGE, frame)
print("Annotated image saved:", OUTPUT_IMAGE)

# -----------------------------
# Print OCR results
# -----------------------------
if lp_texts:
    print("License plate texts detected:", lp_texts)
else:
    print("No license plate text detected.")
