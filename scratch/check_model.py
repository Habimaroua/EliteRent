from ultralytics import YOLO
import os

model_path = r"c:\Users\delll\Desktop\EliteRent-lynaa\EliteRent-lynaa\AI_SERVICE\best.pt"
if os.path.exists(model_path):
    model = YOLO(model_path)
    print("Classes in best.pt:")
    print(model.names)
else:
    print("best.pt not found")

model_path_seg = r"c:\Users\delll\Desktop\EliteRent-lynaa\EliteRent-lynaa\AI_SERVICE\yolov8n-seg.pt"
if os.path.exists(model_path_seg):
    model_seg = YOLO(model_path_seg)
    print("\nClasses in yolov8n-seg.pt:")
    print(model_seg.names)
