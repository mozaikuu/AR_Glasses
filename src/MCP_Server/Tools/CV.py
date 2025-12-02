# wrapper for your CV/YOLO module
try:
    from Computer_Vision.yolo import detect_objects
except Exception:
    def detect_objects(frame_path):
        # stub detection
        return [{"label":"person","conf":0.98,"box":[10,10,100,200]}]

def cv_tool(params):
    frame = params.get("frame_path")
    if not frame:
        return {"error": "no frame_path provided"}
    detections = detect_objects(frame)
    return {"detections": detections}
