import io
import base64
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from ultralytics import YOLO
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
import os
import consul
import socket
import logging

# Configuration des logs
logging.basicConfig(
    filename='ai_service.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Diagnostic Carrosserie Elite")

# --- CONFIGURATION DES MODÈLES ---

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_custom_model(path):
    """Charge le modèle PyTorch (ViT, ResNet ou EfficientNet) basé sur best_model.pt."""
    if not os.path.exists(path):
        return None, "Aucun"
    
    # On tente ViT-B-16 (Taille attendue ~340MB)
    try:
        model = models.vit_b_16(weights=None)
        model.heads.head = nn.Linear(model.heads.head.in_features, 2) # [damage, whole]
        model.load_state_dict(torch.load(path, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        logger.info(f"✅ Modèle ViT chargé avec succès depuis {path}")
        return model, "Vision Transformer (ViT)"
    except Exception as e:
        logger.warning(f"Échec chargement ViT, tentative ResNet50... Error: {e}")
        
    # On tente ResNet50 (Taille attendue ~100MB)
    try:
        model = models.resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, 2)
        model.load_state_dict(torch.load(path, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        logger.info(f"✅ Modèle ResNet50 chargé avec succès depuis {path}")
        return model, "ResNet50"
    except Exception as e:
        logger.warning(f"Échec chargement ResNet50, tentative EfficientNet... Error: {e}")

    # On tente EfficientNet-B0 (Taille attendue ~20MB)
    try:
        model = models.efficientnet_b0(weights=None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
        model.load_state_dict(torch.load(path, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        logger.info(f"✅ Modèle EfficientNet chargé avec succès depuis {path}")
        return model, "EfficientNet-B0"
    except Exception as e:
        logger.error(f"❌ Impossible de charger le modèle personnalisé : {e}")
        return None, "Erreur"

# Chargement du modèle de classification principal
CLASSIFIER, CLASSIFIER_NAME = load_custom_model("best_model.pt")

# Modèle YOLO pour la segmentation visuelle (wow effect)
try:
    yolo_model = YOLO("yolov8n-seg.pt")
except:
    yolo_model = None

# Prétraitement pour la classification
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

CLASS_NAMES = ["00-damage", "01-whole"]

def register_to_consul():
    try:
        c = consul.Consul(host=os.getenv('CONSUL_HOST', 'localhost'))
        service_id = f"ai-service-{socket.gethostname()}"
        c.agent.service.register(
            "ai-service",
            service_id=service_id,
            address="127.0.0.1",
            port=8000,
            tags=["ai", "v2"],
            check=consul.Check.http("http://127.0.0.1:8000/health", interval="10s")
        )
    except:
        pass

@app.on_event("startup")
async def startup_event():
    register_to_consul()

@app.get("/health")
def health():
    return {
        "status": "ready",
        "model": CLASSIFIER_NAME,
        "precision_mode": "ViT Deep Analysis" if "ViT" in CLASSIFIER_NAME else "CNN Analysis"
    }

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    contents = await image.read()
    if not contents:
        return JSONResponse(content={"status": "error", "message": "Fichier vide"})

    try:
        img_pil = Image.open(io.BytesIO(contents)).convert("RGB")
    except:
        return JSONResponse(content={"status": "error", "message": "Format image invalide"})

    # 1. Classification via le nouveau modèle (ViT/ResNet/EffNet)
    damage_detected = False
    confidence = 0.0
    
    if CLASSIFIER:
        with torch.no_grad():
            input_tensor = preprocess(img_pil).unsqueeze(0).to(DEVICE)
            outputs = CLASSIFIER(input_tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            conf, pred = torch.max(probs, 0)
            
            # Index 0 = '00-damage'
            damage_detected = (pred.item() == 0)
            confidence = float(conf.item())
    
    # 2. Visualisation via YOLO (pour les boîtes et masques)
    detections = []
    total_damages = 1 if damage_detected else 0
    img_b64 = ""

    if yolo_model:
        results = yolo_model.predict(img_pil, conf=0.25)
        primary_result = results[0]
        
        # On ajoute la classification globale en tête
        detections.append({
            "class": "Diagnostic Global" if not damage_detected else "DOMMAGE DÉTECTÉ (IA)",
            "confidence": round(confidence, 4),
            "is_damage": damage_detected,
            "bbox": [0, 0, img_pil.width, img_pil.height]
        })

        # On récupère les détails YOLO si possible
        if primary_result.boxes is not None:
            for box in primary_result.boxes:
                cls_name = primary_result.names[int(box.cls[0])].lower()
                if cls_name not in ["car", "wheel", "window", "door"]:
                    detections.append({
                        "class": f"Zone Suspecte ({cls_name})",
                        "confidence": round(float(box.conf[0]), 4),
                        "bbox": box.xyxy[0].tolist(),
                        "is_damage": True
                    })

        # Image annotée
        annotated = primary_result.plot()
        annotated_pil = Image.fromarray(annotated[:, :, ::-1])
        buf = io.BytesIO()
        annotated_pil.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return JSONResponse(content={
        "status": "success",
        "damage_detected": damage_detected,
        "confidence": confidence,
        "total_damages": total_damages,
        "detections": detections,
        "annotated_image_base64": img_b64,
        "model_version": CLASSIFIER_NAME
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
