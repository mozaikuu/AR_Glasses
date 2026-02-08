"""
Minimal AR Pipeline Demo

Demonstrates the complete AR pipeline:
1. Camera capture
2. ArUco marker detection
3. Pose estimation
4. Virtual object rendering

Usage:
    python examples/basic_demo.py
"""

import cv2
import numpy as np
import time
from pathlib import Path

from typing import Optional, Tuple

from ar_pipeline.tracking import ArucoDetector, PoseEstimator
from ar_pipeline.calibration import CameraCalibrator, CalibrationData
from ar_pipeline.utils import ArucoMarkerGenerator


class ARDemo:
    """Minimal AR demonstration."""
    
    def __init__(
        self,
        camera_index: int = 0,
        marker_size: float = 0.03,  # 30mm
        calibration_path: Optional[str] = None
    ):
        """
        Initialize demo.
        
        Args:
            camera_index: Webcam index
            marker_size: Marker size in meters
            calibration_path: Path to calibration file (optional)
        """
        self.marker_size = marker_size
        self.camera_index = camera_index
        
        # Setup detector
        self.detector = ArucoDetector()
        
        # Setup calibration
        if calibration_path and Path(calibration_path).exists():
            self.calibration = CalibrationData.load(calibration_path)
            print(f"Loaded calibration from {calibration_path}")
        else:
            # Use default calibration (you should calibrate for your camera)
            self.calibration = self.create_default_calibration()
            print("Using default calibration (calibrate for accuracy)")
        
        # Setup pose estimator
        self.pose_estimator = PoseEstimator(self.calibration, marker_size)
        
        # Setup camera
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Virtual object properties
        self.show_debug = False
    
    def create_default_calibration(self) -> CalibrationData:
        """Create a default calibration for testing."""
        # These are example values - calibrate for your camera!
        camera_matrix = np.array([
            [500, 0, 320],
            [0, 500, 240],
            [0, 0, 1]
        ], dtype=np.float64)
        
        dist_coeffs = np.zeros(5, dtype=np.float64)
        
        return CalibrationData(
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            image_size=(640, 480),
            reprojection_error=0.5,
            calibration_images=0
        )
    
    def run(self):
        """Run the demo loop."""
        print("\n=== AR Pipeline Demo ===")
        print("Controls:")
        print("  'd' - Toggle debug overlay")
        print("  'c' - Calibrate camera")
        print("  's' - Save current frame")
        print("  'q' - Quit\n")
        
        window_name = "AR Pipeline Demo"
        cv2.namedWindow(window_name)
        
        frame_count = 0
        last_fps_time = time.time()
        fps = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame")
                break
            
            # Detect markers
            detection = self.detector.detect(frame)
            
            # Estimate pose
            pose = self.pose_estimator.estimate(detection)
            
            # Draw results
            output = frame.copy()
            
            if detection.ids is not None:
                # Draw detected markers
                output = self.detector.draw_results(
                    output, detection, draw_axis=self.show_debug
                )
                
                # Draw virtual objects
                if not pose.is_empty():
                    output = self.draw_virtual_objects(output, detection, pose)
            
            # Draw FPS
            frame_count += 1
            if time.time() - last_fps_time >= 1.0:
                fps = frame_count
                frame_count = 0
                last_fps_time = time.time()
            
            cv2.putText(output, f"FPS: {fps}", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if self.show_debug:
                cv2.putText(output, "DEBUG MODE", (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow(window_name, output)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('d'):
                self.show_debug = not self.show_debug
            elif key == ord('c'):
                self.run_calibration()
            elif key == ord('s'):
                cv2.imwrite(f"frame_{time.time():.0f}.jpg", output)
                print("Frame saved")
            elif key == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
    
    def draw_virtual_objects(
        self,
        image: np.ndarray,
        detection,
        pose
    ) -> np.ndarray:
        """
        Draw virtual objects at detected marker positions.
        
        This is a simple overlay - for full AR, use Three.js.
        """
        for i, (corners, rvec, tvec) in enumerate(
            zip(detection.corners, pose.rvecs, pose.tvecs)
        ):
            marker_id = detection.ids[i]
            
            # Draw a cube at marker position
            # This is a 2D projection approximation
            center = corners[0].mean(axis=0).astype(int)
            
            # Draw a colored circle at marker center
            color = (0, 255, 0) if not self.show_debug else (0, 255, 255)
            cv2.circle(image, tuple(center), 10, color, -1)
            
            # Draw label
            label = f"ID:{marker_id} z:{tvec[2][0]*100:.1f}cm"
            cv2.putText(image, label, (center[0] + 15, center[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # If debug mode, draw axis
            if self.show_debug:
                # Draw simple axis
                axis_length = 30
                # Project axis endpoints (simplified)
                cv2.line(image, tuple(center), 
                        (center[0] + axis_length, center[1]), (0, 0, 255), 2)
                cv2.line(image, tuple(center),
                        (center[0], center[1] + axis_length), (0, 255, 0), 2)
        
        return image
    
    def run_calibration(self):
        """Run camera calibration."""
        print("\nStarting calibration...")
        print("Place checkerboard in view and press 'c' to capture")
        print("Press 'q' to cancel\n")
        
        calibrator = CameraCalibrator(checkerboard=(9, 6), square_size=0.025)
        num_captured = calibrator.capture_images(self.cap, num_images=20)
        
        if num_captured >= 3:
            result = calibrator.calibrate()
            if result:
                result.save("camera_calibration.json")
                print("Calibration saved to camera_calibration.json")
                self.calibration = result
                self.pose_estimator = PoseEstimator(result, self.marker_size)
        else:
            print("Not enough images captured")


def main():
    """Run the demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AR Pipeline Demo')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--marker-size', type=float, default=0.03, help='Marker size in meters')
    parser.add_argument('--calibration', type=str, help='Path to calibration file')
    
    args = parser.parse_args()
    
    demo = ARDemo(
        camera_index=args.camera,
        marker_size=args.marker_size,
        calibration_path=args.calibration
    )
    demo.run()


if __name__ == "__main__":
    main()
