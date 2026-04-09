import io
import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import numpy as np

import os
import consul
import socket

import logging

# Configuration des logs dans un fichier pour le débogage permanent
logging.basicConfig(
    filename='ai_service.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Diagnostic Carrosserie")

def register_to_consul():
    try:
        # En mode local hors Docker, on essaie 'localhost'
        c = consul.Consul(host=os.getenv('CONSUL_HOST', 'localhost'))
        service_id = f"ai-service-{socket.gethostname()}"
        c.agent.service.register(
            "ai-service",
            service_id=service_id,
            address="127.0.0.1",
            port=8000,
            tags=["ai", "v1"],
            check=consul.Check.http("http://127.0.0.1:8000/health", interval="10s")
        )
        print(f"✅ Service IA enregistré dans Consul sous l'ID : {service_id}")
    except Exception as e:
        print(f"⚠️ Impossible de se connecter à Consul (normal si vous n'utilisez pas Docker) : {e}")

@app.on_event("startup")
async def startup_event():
    register_to_consul()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Utilise le modèle spécialisé s'il existe, sinon le modèle général
MODEL_PATH = "best.pt" if os.path.exists("best.pt") else "yolov8n-seg.pt"
model = YOLO(MODEL_PATH)
# Modèle de secours toujours chargé
fallback_model = YOLO("yolov8n-seg.pt")

# Cartographie précise pour le modèle entraîné (gaetano v4)
DAMAGE_MAP = {
    "0": "Rayure (Scratch)",
    "1": "Bosse (Dent)",
    "2": "Fissure (Crack)",
    "3": "Vitre/Phare Brisé",
    "4": "Dommage Structurel",
    "scratch": "Rayure",
    "dent": "Bosse",
    "crack": "Fissure",
    "broken_glass": "Vitre Cassée"
}

INFO_CLASSES = {"car", "truck", "wheel", "door", "window", "voiture", "roue", "portière"}

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    logger.debug(f"--- Requête d'analyse reçue: {image.filename} ---")
    contents = await image.read()
    
    if len(contents) == 0:
        return JSONResponse(content={"status": "error", "message": "Image vide"})

    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Erreur image: {e}"})

    # 1. Analyse avec le modèle de DECOURS (YOLOv8 Générique) pour le contexte
    # On l'utilise pour détecter les composants normaux (roues, carrosserie)
    general_results = fallback_model.predict(img, conf=0.25, imgsz=640)
    
    # 2. Analyse avec VOTRE MODÈLE (best.pt) pour les DOMMAGES
    # On utilise une résolution de 1024px ("Mode Loupe") pour les micro-détails
    # On active 'augment=True' pour aider à détecter les objets minuscules
    damage_results = model.predict(img, conf=0.05, imgsz=900, augment=True) 
    
    detections = []
    total_damages = 0
    
    # Priorité aux détections de VOTRE modèle (best.pt)
    primary_result = damage_results[0]
    if primary_result.boxes is not None:
        for box in primary_result.boxes:
            cls_id = int(box.cls[0])
            cls_name = str(primary_result.names[cls_id]).lower()
            confidence = float(box.conf[0])
            
            # Tout ce qui sort de best.pt est considéré comme un dommage potentiel
            # sauf si c'est explicitement une classe d'objet connue
            is_damage = cls_name not in INFO_CLASSES
            
            if is_damage:
                total_damages += 1
                display_name = DAMAGE_MAP.get(cls_name, f"Dommage ({cls_name})")
            else:
                display_name = cls_name

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "class": display_name,
                "confidence": round(confidence, 4),
                "bbox": [round(x1), round(y1), round(x2), round(y2)],
                "is_damage": is_damage
            })

    # Si votre modèle n'a rien vu, on ajoute les objets du modèle général pour l'affichage
    if total_damages == 0 and general_results[0].boxes is not None:
        logger.warning("best.pt n'a rien détecté, utilisation du modèle général pour le rapport.")
        for box in general_results[0].boxes:
            cls_id = int(box.cls[0])
            cls_name = str(general_results[0].names[cls_id]).lower()
            if cls_name in INFO_CLASSES:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append({
                    "class": cls_name,
                    "confidence": round(float(box.conf[0]), 4),
                    "bbox": [round(x1), round(y1), round(x2), round(y2)],
                    "is_damage": False
                })

    # Génération de l'image annotée : on fusionne visuellement les résultats
    # On utilise plot() du modèle de dommages car c'est lui qui nous importe le plus
    annotated = primary_result.plot(masks=True, boxes=True, conf=True)
    
    # Si le modèle de dommages est vide, on plot le modèle général
    if total_damages == 0:
        annotated = general_results[0].plot(masks=True, boxes=True)

    if annotated.shape[2] == 3:
        annotated = annotated[:, :, ::-1] # BGR to RGB
        
    annotated_pil = Image.fromarray(annotated)
    buf = io.BytesIO()
    annotated_pil.save(buf, format="JPEG", quality=90)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    logger.debug(f"DEBUG: Analyse terminée. {total_damages} dommages identifiés.")

    return JSONResponse(content={
        "status": "success",
        "total_detections": len(detections),
        "total_damages": total_damages,
        "damage_detected": total_damages > 0,
        "detections": detections,
        "has_segmentation": primary_result.masks is not None or general_results[0].masks is not None,
        "annotated_image_base64": img_b64,
    })


@app.get("/health")
async def health():
    return {"status": "ok"}
