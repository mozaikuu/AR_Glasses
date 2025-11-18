from ultralytics import YOLO
import torch
import os

torch.multiprocessing.set_start_method('spawn', force=True)

PATH = "./Computer_Vision/"

# Load base model
model = YOLO(PATH + "yolo11n.pt")

if not os.path.exists(PATH + "yolo11n_coco8_trained.pt"):
    # Train without overwriting the model variable !!!
    results = model.train(data=PATH + "coco8.yaml", epochs=100, imgsz=640)

    # Save trained model
    model.save(PATH + "yolo11n_coco8_trained.pt")
else:
    # Load trained model
    model = YOLO(PATH + "yolo11n_coco8_trained.pt")

# Run inference test
# results = model(PATH + "Tests/Test1.jpg")
# results = model(PATH + "Tests/Test2.jpg")
# results = model(PATH + "Tests/Test3.jpg")
# results = model(PATH + "Tests/Test4.png")
