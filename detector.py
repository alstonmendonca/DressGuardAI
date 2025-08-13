# detector.py
from ultralytics import YOLO
import cv2
import numpy as np

class DressDetector:
    def __init__(self):
        self.model = YOLO("models/best.pt")  # Load default YOLOv8 model hehehehe

    def detect(self, image: np.ndarray):
        results = self.model(image)
        detections = results[0]

        clothes = []
        for box in detections.boxes:
            cls_id = int(box.cls[0])
            class_name = self.model.names[cls_id]
            bbox = box.xyxy[0].tolist()
            confidence = float(box.conf[0])

            clothes.append({
                "class": class_name,
                "bbox": bbox,
                "confidence": confidence
            })

        return clothes
