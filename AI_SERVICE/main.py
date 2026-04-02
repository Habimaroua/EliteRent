import io
import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import numpy as np

app = FastAPI(title="AI Diagnostic Carrosserie")

model = YOLO("yolov8n-seg.pt")

# Classes de dommages réels
DAMAGE_CLASSES = {"scratch", "dent"}
# Classes d'objets pour information
INFO_CLASSES = {"car", "truck", "bus", "motorcycle", "person"}
TARGET_CLASSES = DAMAGE_CLASSES | INFO_CLASSES


@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    contents = await image.read()
    img = Image.open(io.BytesIO(contents)).convert("RGB")

    results = model(img)
    result = results[0]

    detections = []
    total_damages = 0
    if result.boxes is not None:
        for i, box in enumerate(result.boxes):
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            confidence = float(box.conf[0])
            
            if cls_name.lower() in TARGET_CLASSES:
                is_damage = cls_name.lower() in DAMAGE_CLASSES
                if is_damage:
                    total_damages += 1
                
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                det = {
                    "class": cls_name,
                    "confidence": round(confidence, 4),
                    "bbox": [round(x1), round(y1), round(x2), round(y2)],
                    "is_damage": is_damage
                }
                detections.append(det)

    annotated = result.plot()
    annotated_pil = Image.fromarray(annotated)
    buf = io.BytesIO()
    annotated_pil.save(buf, format="JPEG", quality=90)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return JSONResponse(content={
        "status": "success",
        "total_detections": len(detections),
        "total_damages": total_damages,
        "damage_detected": total_damages > 0,
        "detections": detections,
        "annotated_image_base64": img_b64,
    })


@app.get("/health")
async def health():
    return {"status": "ok"}
