from ultralytics import YOLO
import cv2
import numpy as np
from config import MODEL_PATH

class DressDetector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def detect(self, image: np.ndarray):
        """
        Accepts a NumPy image, returns bounding boxes and class names.
        """
        results = self.model(image)
        detections = results[0]
        clothes = []

        for box in detections.boxes:
            cls_id = int(box.cls[0])
            class_name = self.model.names[cls_id]
            bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
            clothes.append({
                "class": class_name,
                "bbox": bbox,
                "confidence": float(box.conf[0])
            })

        return clothes
