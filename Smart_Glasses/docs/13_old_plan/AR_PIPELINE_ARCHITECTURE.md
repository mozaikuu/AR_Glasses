# Custom AR Pipeline Architecture for Smart Glasses

## Executive Summary

This document describes a modular, marker-based AR pipeline for ESP32-class smart glasses where the phone acts as the compute gateway. The architecture prioritizes **debuggability**, **extensibility**, and **full control** over the AR pipeline—avoiding black-box SDKs entirely.

---

## 1. System Architecture Overview

### 1.1 Hardware Topology

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Smart Glasses │────▶│      Phone      │────▶│   Smart Glasses │
│   (ESP32-CAM)   │◀────│   (Gateway)     │◀────│    (Display)    │
│                │     │                 │     │                 │
│  - Camera      │     │  - Pose Est.    │     │  - MicroOLED    │
│  - IMU         │     │  - Rendering    │     │  - Low latency  │
│  - MicroOLED   │     │  - CV Pipeline  │     │    video input  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                       │
        │   H.264/MJPEG          │   Rendered frame     │
        │   ~30 FPS              │   ~30 FPS            │
        │                        │                       │
        └────────────────────────┴───────────────────────┘
```

**Why this topology:**

-  **ESP32 constraints**: No heavy CV processing; limited RAM (~520KB), single-core
-  **Phone capabilities**: Multi-core CPU, GPU acceleration, real-time processing
-  **Latency budget**: 50-100ms round-trip is acceptable for static AR overlays

### 1.2 Software Stack

| Layer           | Technology                      | Purpose                            |
| --------------- | ------------------------------- | ---------------------------------- |
| **Capture**     | OpenCV VideoCapture / picamera2 | Camera frame acquisition           |
| **Tracking**    | OpenCV + ArUco/AprilTag         | Marker detection & pose estimation |
| **Calibration** | OpenCV CalibrateCamera          | Intrinsic/extrinsic parameters     |
| **Rendering**   | Three.js (WebGL) or PyOpenGL    | Virtual object compositing         |
| **Transport**   | WebSocket / HTTP POST           | Frame streaming                    |
| **Display**     | HDMI/MIPI interface             | Framebuffer to glasses             |

---

## 2. Coordinate Systems

Understanding coordinate frames is critical for spatial alignment.

### 2.1 Defined Frames

```
World Frame (W)     : Fixed in environment. Origin at marker center.
Camera Frame (C)    : Moving. Origin at camera optical center.
Marker Frame (M)    : Fixed to each ArUco marker. Z-axis perpendicular to marker.
Glasses Display (D) : Fixed relative to camera (if calibrated together).
Object Frame (O)    : Virtual object's local frame.
```

### 2.2 Transformations

```
T_WC  = Transformation from Camera to World (what we estimate)
T_WM  = Marker pose in world (known, fixed)
T_CM  = Camera to Marker (detected from marker corners)

Relationship: T_WC = T_WM × T_CM
```

**Key insight**: We detect `T_CM` from marker corners, and since `T_WM` is known (marker placed at known world position), we compute `T_WC`.

### 2.3 Pose Representation

Pose is always expressed as:

-  **Rotation**: 3×3 rotation matrix `R` or quaternion `(qx, qy, qz, qw)`
-  **Translation**: 3×1 vector `t` in meters

```
Homogeneous form:
    [ R  t ]
    [ 0  1 ]
```

---

## 3. Data Flow Pipeline

### 3.1 Complete Pipeline Stages

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          AR PIPELINE DATA FLOW                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [GLASSES CAM] ──▶ [PHONE CAPTURE] ──▶ [TRACKING] ──▶ [RENDERING]      │
│       │                   │                     │               │        │
│       ▼                   ▼                     ▼               ▼        │
│  Raw Bayer/        Grayscale           Marker         Three.js      │
│  JPEG frame        conversion          detection      scene graph    │
│                                        + pose                        │
│                                                          │            │
│  [GLASSES DISP] ◀─── [ENCODING] ◀──── [COMPOSITE] ◀─────┘            │
│       │                │                  │                          │
│       ▼                ▼                  ▼                          │
│  Framebuffer    H.264/JPEG          Blended AR                       │
│  output         compression         frame                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Stage Details

#### Stage 1: Camera Capture (Glasses → Phone)

```python
# Pseudocode - glasses firmware
def capture_frame():
    image = camera.capturejpeg()
    # Compress to reduce bandwidth
    jpeg_quality = 70  # Balance quality/bandwidth
    encode_and_send(image, jpeg_quality)
```

**Bandwidth estimate**:

-  640×480 × 3 bytes × 30 fps = 26.4 MB/s raw
-  JPEG @ 70% = ~500 KB/s (50× reduction)

#### Stage 2: Tracking (Pose Estimation)

```python
# Pseudocode - phone processing
def estimate_pose(gray_frame):
    # Detect markers
    corners, ids = aruco_detect(gray_frame, dictionary)

    if ids is not None:
        # Estimate pose for each marker
        rvecs, tvecs, _ = estimate_marker_pose(
            corners, ids, marker_size, camera_matrix, dist_coeffs
        )
        # Return in world frame
        return rvecs, tvecs
    return None, None
```

**OpenCV functions used**:

-  [`aruco.detectMarkers()`](https://docs.opencv.org/4.x/d9/d6a/group__aruco.html) - Corner detection
-  [`aruco.estimatePoseSingleMarkers()`](https://docs.opencv.org/4.x/d9/d6a/group__aruco.html) - Pose from corners

#### Stage 3: Rendering (Virtual Object Placement)

```python
# Pseudocode - Three.js/WebGL
function render_ar_scene(pose_matrix, virtual_objects):
    camera.matrix.fromArray(pose_matrix)
    camera.matrixWorldNeedsUpdate = true

    for obj in virtual_objects:
        # Virtual object position relative to marker/world
        obj.position.set(obj.local_x, obj.local_y, obj.local_z)
        obj.updateMatrixWorld()

    renderer.render(scene, camera)

    # Output: AR composite frame
    return gl_read_pixels()
```

#### Stage 4: Display (Phone → Glasses)

```python
# Pseudocode - display output
def send_to_glasses(composite_frame):
    # Resize to glasses display resolution
    resized = resize(composite_frame, target_resolution)
    # Encode and transmit
    send_frame(resized, compression_level)
```

---

## 4. ArUco Marker System

### 4.1 Why ArUco (vs AprilTag)

| Feature             | ArUco                           | AprilTag                      |
| ------------------- | ------------------------------- | ----------------------------- |
| **OpenCV native**   | ✅ Yes                          | ❌ Requires OpenCV 4.5.1+     |
| **Detection speed** | Fast                            | Slightly faster               |
| **Marker size**     | Small (5×5 to 7×7 bits)         | Larger families               |
| **Robustness**      | Good                            | Better (smaller inner border) |
| **Our choice**      | **ArUco** (simpler integration) |

**Recommended dictionary**: `DICT_6X6_250` (250 unique markers, 6×6 bits)

### 4.2 Marker Size Selection

```
Marker size (mm)    Detection range
─────────────────────────────────────
15mm                0.1 - 0.5m (close)
30mm                0.2 - 1.0m (typical)
50mm                0.3 - 1.5m (far)
```

**Guideline**: Use 30mm markers for general purpose, 50mm for room-scale.

### 4.3 Marker Placement Strategy

```
World Coordinate Definition:

Marker at origin (0,0,0) on wall:
    ┌─────────────────┐
    │   Y↑            │
    │   │            │
    │   │            │
    │   └──────▶X    │
    │  (Z out of wall)│
    │   [ARUCO]      │
    └─────────────────┘

Place additional markers at known offsets for:
- Extended tracking (multiple markers = larger area)
- Redundancy (occlusion handling)
```

---

## 5. Camera Calibration

### 5.1 Why Calibration Matters

Without proper calibration:

-  Virtual objects will **drift** as camera moves
-  **Scale** will be incorrect
-  Objects will appear **distorted** at image edges

### 5.2 Calibration Parameters

**Intrinsics** (per-camera, fixed):

-  `camera_matrix`: 3×3 matrix [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
-  `dist_coeffs`: 5×1 or 8×1 distortion coefficients

**Extrinsics** (camera-to-marker, per-frame):

-  `rvec`: 3×1 rotation vector (Rodrigues)
-  `tvec`: 3×1 translation in meters

### 5.3 Calibration Procedure

```python
# Pseudocode - calibration capture
def capture_calibration_images():
    checkerboard = (9, 6)  # Internal corners
    images = []

    for i in range(20):
        while not checkerboard_detected():
            frame = capture_frame()
            display(frame)  # Show user
        images.append(frame.copy())

    # Calibrate
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
        object_points, image_points, image_size,
        None, None
    )
    save_calibration(mtx, dist)
```

**Printable checkerboard**: Use A4 chessboard pattern.

### 5.4 Calibration Validation

```python
def validate_calibration(mtx, dist, test_images):
    total_error = 0

    for img in test_images:
        # Project points using calibration
        projected, _ = cv.projectPoints(
            object_points, rvec, tvec, mtx, dist
        )
        error = norm(projected - image_points) / len(image_points)
        total_error += error

    avg_error = total_error / len(test_images)

    # Error < 0.5 pixels = good calibration
    return avg_error < 0.5
```

---

## 6. Implementation Plan

### Phase 1: Foundation

-  [ ] Implement camera capture from ESP32-CAM
-  [ ] Set up WebSocket transport layer
-  [ ] Create frame encoding/decoding

### Phase 2: Tracking

-  [ ] Integrate ArUco marker detection
-  [ ] Implement camera calibration procedure
-  [ ] Add pose estimation from marker corners

### Phase 3: Rendering

-  [ ] Set up Three.js scene with camera
-  [ ] Map pose matrix to Three.js camera
-  [ ] Render simple virtual objects

### Phase 4: Integration

-  [ ] End-to-end pipeline test
-  [ ] Latency measurement and optimization
-  [ ] Multi-marker support

### Phase 5: Refinement

-  [ ] Motion smoothing (Kalman filter)
-  [ ] Occlusion handling
-  [ ] Performance profiling

---

## 7. Latency Budget Analysis

```
Pipeline latency breakdown (target 60 FPS = 16.67ms/frame):

Stage                      Time    Cumulative
─────────────────────────────────────────────────
Camera capture             5ms     5ms
Wireless transmission      8ms     13ms
Frame decode               2ms     15ms
ArUco detection            3ms     18ms ⭐ (over budget)
Pose estimation            1ms     19ms
Rendering                  5ms     24ms
Encode & send back         8ms     32ms
─────────────────────────────────────────────────
Total round-trip           ~32ms   (30 FPS achievable)
```

### Latency Optimization Strategies

1. **Resolution scaling**: Reduce processing resolution (480p → 360p)
2. **Marker detection skipping**: Only detect when motion detected
3. **Parallel pipeline**: Capture next frame while processing current
4. **Prediction**: Use IMU data to extrapolate pose during gaps

---

## 8. Code Snippets

### 8.1 ArUco Detection & Pose Estimation

```python
import cv2
import numpy as np

def detect_and_pose(frame, camera_matrix, dist_coeffs, marker_size=0.03):
    """Detect ArUco markers and estimate pose."""

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect markers
    dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters_create()
    corners, ids, rejected = cv2.aruco.detectMarkers(
        gray, dictionary, parameters=parameters
    )

    if ids is not None:
        # Estimate pose for each marker
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners, marker_size, camera_matrix, dist_coeffs
        )
        return corners, ids, rvecs, tvecs

    return None, None, None, None
```

### 8.2 Pose to Transformation Matrix

```python
def pose_to_matrix(rvec, tvec):
    """Convert rotation vector + translation to 4×4 matrix."""

    # Rodrigues rotation vector to rotation matrix
    R, _ = cv2.Rodrigues(rvec)

    # Build homogeneous transformation
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = tvec.flatten()

    return T
```

### 8.3 Three.js Camera from Pose Matrix

```javascript
// Three.js: Set camera from AR pose matrix
function updateCameraFromPose(camera, poseMatrix) {
	// poseMatrix is 4×4 in row-major format
	camera.matrix.set(
		poseMatrix[0],
		poseMatrix[1],
		poseMatrix[2],
		poseMatrix[3],
		poseMatrix[4],
		poseMatrix[5],
		poseMatrix[6],
		poseMatrix[7],
		poseMatrix[8],
		poseMatrix[9],
		poseMatrix[10],
		poseMatrix[11],
		poseMatrix[12],
		poseMatrix[13],
		poseMatrix[14],
		poseMatrix[15],
	);
	camera.matrixWorldNeedsUpdate = true;
}
```

---

## 9. Debugging & Testing

### 9.1 Visualization Tools

-  **Marker debug view**: Overlay detected corners and axes
-  **Pose visualization**: Show camera frustum in 3D
-  **Error heatmap**: Pixel error from calibration reprojection

### 9.2 Common Issues

| Symptom             | Likely Cause     | Fix                            |
| ------------------- | ---------------- | ------------------------------ |
| Objects drift       | Incorrect scale  | Verify marker_size in meters   |
| Distorted edges     | Bad calibration  | Re-calibrate with more angles  |
| No markers detected | Lighting / focus | Increase contrast, check focus |
| Jittery motion      | No smoothing     | Add low-pass filter on pose    |

---

## 10. File Structure

```
ar_pipeline/
├── calibration/
│   ├── calibrate.py           # Camera calibration script
│   └── intrinsics.json        # Saved calibration parameters
├── tracking/
│   ├── aruco_detector.py      # Marker detection
│   └── pose_estimator.py      # Pose from markers
├── rendering/
│   ├── threejs_app/           # WebGL renderer
│   │   ├── index.html
│   │   ├── main.js
│   │   └── shaders/
│   └── opengl_renderer.py     # Native alternative
├── transport/
│   ├── websocket_server.py    # Frame streaming
│   └── video_compression.py   # MJPEG/H.264
├── examples/
│   └── basic_demo.py          # Minimal working example
└── utils/
    ├── visualization.py       # Debug overlays
    └── marker_generator.py    # Print ArUco markers
```

---

## 11. References

-  [OpenCV ArUco Documentation](https://docs.opencv.org/4.x/d9/d6a/group__aruco.html)
-  [OpenCV Camera Calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)
-  [Three.js Camera Documentation](https://threejs.org/docs/#api/en/cameras/Camera)
-  [ArUco Marker Generator](https://chev.me/arucogen/)

---

## 12. Summary

This architecture provides:

-  **Full pipeline control** (no black boxes)
-  **Modular design** (swap tracking/rendering independently)
-  **Explicit coordinate systems** (debuggable transforms)
-  **Marker-based tracking** (reliable, understandable)
-  **Clear latency budget** (optimizable stages)

The pipeline is designed for robotics/CV engineers who need to understand and modify every stage of the AR computation.

# Install dependencies

pip install opencv-python numpy websockets

# Run basic demo

python ar_pipeline/examples/basic_demo.py

# Generate printable markers

python -c "from ar_pipeline.utils import ArucoMarkerGenerator; g = ArucoMarkerGenerator(); g.generate_grid(list(range(12)), output='markers.png')"
