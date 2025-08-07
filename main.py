from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import cv2
from detector import DressDetector
from utils.compliance import is_compliant

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
async def detect_dress(file: UploadFile = File(...)):
    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    detected_clothes = detector.detect(image)
    compliant, non_compliant_items = is_compliant(detected_clothes)

    return {
        "clothes_detected": detected_clothes,
        "compliant": compliant,
        "non_compliant_items": non_compliant_items
    }
