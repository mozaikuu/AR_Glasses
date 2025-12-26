from ultralytics import YOLO
import torch
import os
import cv2

torch.multiprocessing.set_start_method('spawn', force=True)

PATH = "./src/mcp_server/tools/Computer_Vision/"

# Load base model
# model = YOLO(PATH + "yolo11n.pt")

# Run inference test
# results = model(PATH + "Tests/Test1.jpg")
# results = model(PATH + "Tests/Test2.jpg")
# results = model(PATH + "Tests/Test3.jpg")
# results = model(PATH + "Tests/Test4.png")

# results = model.predict(source=PATH + "Tests/Test1.jpg", save=True, save_txt=True)
# image from camera
# results = model.predict(frame, save=True, save_txt=True, project='./src/mcp_server/Computer_Vision/Inference_Results', name='camera_output')

# def infer():
#     """Run inference on an image and return results."""
#     # results = model.predict(frame, save=True, save_txt=True, project='./src/mcp_server/Computer_Vision/Inference_Results', name='camera_output')
#     results = model.predict(frame, project='./src/mcp_server/tools/Computer_Vision/Inference_Results', name='camera_output',verbose=False)
#     output_string = str(results[0]) if isinstance(results, list) else str(results)
#     return str(output_string)

def infer():
    # Create a video capture object for camera ID 0
    cap = cv2.VideoCapture(0)

    # Capture a frame
    ret, frame = cap.read()

    # Release the camera
    cap.release()
    
    model = YOLO(PATH + "yolo11n_coco8_trained.pt", verbose=False)

    # # Save the captured image
    # cv2.imwrite("captured_image.jpg", frame)

    # # Display the image in a window for 5 seconds
    # cv2.imshow("Captured Image", frame)
    # cv2.waitKey(5000)
    # cv2.destroyAllWindows()
    """Run inference on an image and return results."""
    # results = model.predict(frame, save=True, save_txt=True, project='./src/mcp_server/Computer_Vision/Inference_Results', name='camera_output')
    results = model(frame)
    names = model.names
    
    detected = set()
    for r in results:
        for c in r.boxes.cls:
            detected.add(names[int(c)])
    if not detected:
        return "No objects detected"
    return "Detected: " + ", ".join(detected)

# infer()

# print("Inference Results:", infer())