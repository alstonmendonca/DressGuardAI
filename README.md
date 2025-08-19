## 🖼️ Frontend Image Detection Flow

1. User uploads an image.
2. Image is previewed using `URL.createObjectURL()`.
3. Image sent to `POST /detect/` on FastAPI backend.
4. Backend runs YOLOv8 and returns:
   - `clothes_detected`: list of `{ class, bbox: [x1,y1,x2,y2], confidence }`
   - Original image dimensions used for scaling
5. Frontend:
   - Renders image (scaled by browser)
   - Uses `<canvas>` to draw bounding boxes
   - Scales detection coordinates using `naturalWidth → rendered width`
6. Results displayed with labels and confidence.

> ⚠️ The canvas must match the **rendered image size**, not the original.



After pulling the code from github, pleas make sure to:
1) run 'npm install' in the root directory as well inside the frontend folder
2) run 'pip install fastapi uvicorn' in the root directory
3) Create a folder called 'models' in the root directory. Inside the folder add all your pytorch(.pt) models (YOLO models)
4) Adjust the paths of the models in detector.py and config.py