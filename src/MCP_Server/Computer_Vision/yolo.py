from ultralytics import YOLO
import torch
import os
import cv2

torch.multiprocessing.set_start_method('spawn', force=True)

PATH = "./src/MCP_Server/Computer_Vision/"

# Load base model
model = YOLO(PATH + "yolo11n.pt")

# Create a video capture object for camera ID 0
cap = cv2.VideoCapture(0)

# Capture a frame
ret, frame = cap.read()

# Release the camera
cap.release()

# # Save the captured image
# cv2.imwrite("captured_image.jpg", frame)

# # Display the image in a window for 5 seconds
# cv2.imshow("Captured Image", frame)
# cv2.waitKey(5000)
# cv2.destroyAllWindows()

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

# results = model.predict(source=PATH + "Tests/Test1.jpg", save=True, save_txt=True)
# image from camera
# results = model.predict(frame, save=True, save_txt=True, project='./src/MCP_Server/Computer_Vision/Inference_Results', name='camera_output')

def infer():
    """Run inference on an image and return results."""
    # results = model.predict(frame, save=True, save_txt=True, project='./src/MCP_Server/Computer_Vision/Inference_Results', name='camera_output')
    results = model(frame, project='./src/MCP_Server/Computer_Vision/Inference_Results', name='camera_output')
    return results

data = infer()
print(data)  # or process the results as needed