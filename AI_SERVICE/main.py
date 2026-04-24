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

# --- CONFIGURATION PRODUCTION ELITERENT-AI ---

# Sélection automatique du meilleur modèle
def get_active_model_path():
    # Priorité : best.pt (votre favori), puis trained.pt, puis le modèle de base
    for m in ["best.pt", "trained.pt", "yolov8n-seg.pt"]:
        if os.path.exists(m):
            logger.info(f"🚀 Modèle de production activé : {m}")
            return m
    return "yolov8n-seg.pt"

ACTIVE_MODEL = get_active_model_path()
model = YOLO(ACTIVE_MODEL)
fallback_model = YOLO("yolov8n-seg.pt")

# Traduction précise des classes détectées par best.pt
DAMAGE_MAP = {
    "0": "Rayure (Scratch)",
    "1": "Bosse (Dent)",
    "2": "Fissure (Crack)",
    "4": "Dommage Structurel",
    "scratch": "Rayure",
    "dent": "Bosse",
    "crack": "Fissure",
    "shattered_glass": "Vitre Cassée",
    "broken_lamp": "Phare Endommagé",
    "flat_tire": "Pneu Dégonflé"
}

# Objets normaux à ignorer pour le comptage des dommages
INFO_CLASSES = {
    "car", "truck", "wheel", "door", "window", 
    "voiture", "roue", "portière", "tire", "mirror", "glass"
}

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    logger.debug(f"--- ANALYSE EN COURS : {image.filename} ---")
    contents = await image.read()
    
    if not contents:
        return JSONResponse(content={"status": "error", "message": "Fichier vide"})

    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Format image invalide: {e}"})

    # 1. Analyse Contexte (Modèle général)
    general_results = fallback_model.predict(img, conf=0.25, imgsz=640)
    
    # 2. Analyse Spécialisée (Modèle Production)
    # On monte la résolution à 1024 pour la précision, confidence à 0.20 pour éviter les faux reflets
    damage_results = model.predict(img, conf=0.20, imgsz=1024, augment=True) 
    
    detections = []
    total_damages = 0
    
    # Traitement des résultats du modèle spécialisé
    primary_result = damage_results[0]
    if primary_result.boxes is not None:
        for box in primary_result.boxes:
            cls_id = int(box.cls[0])
            cls_name = str(primary_result.names[cls_id]).lower()
            confidence = float(box.conf[0])
            
            # Déterminer si c'est un dommage ou un élément de carrosserie
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

    # Si aucun dommage, on enrichit avec le modèle général pour l'affichage
    if total_damages == 0 and general_results[0].boxes is not None:
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

    # Génération de l'image de sortie
    annotated = primary_result.plot(masks=True, boxes=True, conf=True)
    if total_damages == 0:
        annotated = general_results[0].plot(masks=True, boxes=True)

    if annotated.shape[2] == 3:
        annotated = annotated[:, :, ::-1] # BGR conversion
        
    annotated_pil = Image.fromarray(annotated)
    buf = io.BytesIO()
    annotated_pil.save(buf, format="JPEG", quality=85)
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return JSONResponse(content={
        "status": "success",
        "total_detections": len(detections),
        "total_damages": total_damages,
        "damage_detected": total_damages > 0,
        "detections": detections,
        "annotated_image_base64": img_b64,
        "model_version": ACTIVE_MODEL
    })

@app.get("/health")
async def health():
    return {
        "status": "ready",
        "model": ACTIVE_MODEL,
        "precision_mode": "1024px High-Res"
    }
