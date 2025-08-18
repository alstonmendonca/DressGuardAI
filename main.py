from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from detector import DressDetector
from utils.compliance import is_compliant
from fastapi import Body

app = FastAPI()
detector = DressDetector()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/detect/")
async def detect_dress(file: UploadFile = File(...), model: str = None):
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Switch model if specified
    if model and model != detector.current_model:
        detector.switch_model(model)

    detected_clothes = detector.detect(image)
    h, w = image.shape[:2]  # original dimensions

    compliant, non_compliant_items = is_compliant(detected_clothes)

    return {
        "clothes_detected": detected_clothes,
        "image_width": w,
        "image_height": h,
        "compliant": compliant,
        "non_compliant_items": non_compliant_items,
        "model_used": detector.current_model  # Return which model was used
    }

@app.post("/switch-model/")
async def switch_model(model_name: str = Body(..., embed=True)):
    success = detector.switch_model(model_name.lower())
    return {
        "success": success,
        "current_model": detector.current_model,
        "message": f"Switched to {detector.current_model}" if success else "Model switch failed"
    }

@app.get("/current-model/")
async def get_current_model():
    return {"current_model": detector.current_model}