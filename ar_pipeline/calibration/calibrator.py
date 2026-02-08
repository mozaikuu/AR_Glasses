"""
CameraCalibrator - Intrinsic and extrinsic camera calibration

Provides chessboard-based camera calibration to compute:
- Camera matrix (intrinsics)
- Distortion coefficients
- Reprojection error for quality assessment
"""

import cv2
import numpy as np
import json
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict
from pathlib import Path


@dataclass
class CalibrationData:
    """Container for calibration results."""
    camera_matrix: np.ndarray  # 3×3 intrinsic matrix
    dist_coeffs: np.ndarray    # Distortion coefficients
    image_size: Tuple[int, int]  # (width, height)
    reprojection_error: float = 0.0
    calibration_images: int = 0
    
    def save(self, filepath: str) -> None:
        """Save calibration to JSON file."""
        data = {
            'camera_matrix': self.camera_matrix.tolist(),
            'dist_coeffs': self.dist_coeffs.tolist(),
            'image_size': list(self.image_size),
            'reprojection_error': float(self.reprojection_error),
            'calibration_images': self.calibration_images
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'CalibrationData':
        """Load calibration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(
            camera_matrix=np.array(data['camera_matrix']),
            dist_coeffs=np.array(data['dist_coeffs']),
            image_size=tuple(data['image_size']),
            reprojection_error=data.get('reprojection_error', 0.0),
            calibration_images=data.get('calibration_images', 0)
        )
    
    def validate(self, max_error: float = 1.0) -> Tuple[bool, float]:
        """
        Validate calibration quality.
        
        Args:
            max_error: Maximum acceptable reprojection error in pixels
            
        Returns:
            (is_valid, error)
        """
        return self.reprojection_error < max_error, self.reprojection_error
    
    def get_focal_lengths(self) -> Tuple[float, float]:
        """Get focal lengths in pixels."""
        return self.camera_matrix[0, 0], self.camera_matrix[1, 1]
    
    def get_principal_point(self) -> Tuple[float, float]:
        """Get principal point coordinates."""
        return self.camera_matrix[0, 2], self.camera_matrix[1, 2]
    
    def get_fov(self) -> Tuple[float, float]:
        """Get field of view in degrees."""
        fx, fy = self.get_focal_lengths()
        w, h = self.image_size
        fov_x = np.degrees(2 * np.arctan2(w, 2 * fx))
        fov_y = np.degrees(2 * np.arctan2(h, 2 * fy))
        return fov_x, fov_y


class CameraCalibrator:
    """
    Camera calibration using chessboard pattern.
    
    Usage:
        calibrator = CameraCalibrator(checkerboard=(9, 6))
        calibrator.capture_images(video_capture, num_images=20)
        result = calibrator.calibrate()
        result.save('calibration.json')
    """
    
    def __init__(
        self,
        checkerboard: Tuple[int, int] = (9, 6),
        square_size: float = 0.025  # 25mm squares
    ):
        """
        Initialize calibrator.
        
        Args:
            checkerboard: (width, height) number of internal corners
            square_size: Size of checkerboard square in meters
        """
        self.checkerboard = checkerboard
        self.square_size = square_size
        
        # Prepare object points (0,0,0), (1,0,0), (2,0,0), ...
        self.object_points = self._create_object_points()
        
        # Storage for calibration images
        self.corners_list: List[np.ndarray] = []
        self.images: List[np.ndarray] = []
    
    def _create_object_points(self) -> np.ndarray:
        """Create 3D object points for checkerboard corners."""
        objp = np.zeros((self.checkerboard[1] * self.checkerboard[0], 3), np.float32)
        objp[:, :2] = np.mgrid[
            0:self.checkerboard[0],
            0:self.checkerboard[1]
        ].T.reshape(-1, 2)
        objp *= self.square_size
        return objp
    
    def capture_images(
        self,
        capture_source,
        num_images: int = 20,
        display: bool = True,
        save_dir: Optional[str] = None
    ) -> int:
        """
        Capture calibration images from video source.
        
        Args:
            capture_source: cv2.VideoCapture or similar
            num_images: Number of images to capture
            display: Show detection preview
            save_dir: Optional directory to save images
            
        Returns:
            Number of successfully captured images
        """
        if save_dir:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        captured = 0
        window_name = "Calibration Capture"
        
        if display:
            cv2.namedWindow(window_name)
        
        print(f"Capturing {num_images} calibration images...")
        print("Press 'c' to capture, 'q' to quit early")
        
        while captured < num_images:
            ret, frame = capture_source.read()
            if not ret:
                print("Failed to capture frame")
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Find checkerboard corners
            ret_corners, corners = cv2.findChessboardCorners(
                gray,
                self.checkerboard,
                None
            )
            
            # Draw preview
            preview = frame.copy()
            if ret_corners:
                cv2.drawChessboardCorners(preview, self.checkerboard, corners, ret_corners)
                cv2.putText(preview, f"Captured: {captured}/{num_images}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(preview, "Place checkerboard in view", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            if display:
                cv2.imshow(window_name, preview)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('c') and ret_corners:
                    # Refine corner positions
                    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                    corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                    
                    self.corners_list.append(corners_refined)
                    self.images.append(frame.copy())
                    captured += 1
                    print(f"Captured {captured}/{num_images}")
                    
                    if save_dir:
                        cv2.imwrite(f"{save_dir}/calib_{captured:03d}.jpg", frame)
                
                elif key == ord('q'):
                    print("Capture cancelled")
                    break
        
        if display:
            cv2.destroyWindow(window_name)
        
        print(f"Captured {captured} images")
        return captured
    
    def calibrate(self) -> Optional[CalibrationData]:
        """
        Perform camera calibration from captured images.
        
        Returns:
            CalibrationData or None if insufficient images
        """
        if len(self.corners_list) < 3:
            print(f"Need at least 3 images, have {len(self.corners_list)}")
            return None
        
        # Stack all object points
        obj_points = [self.object_points] * len(self.corners_list)
        
        # Stack all image points
        img_points = self.corners_list
        
        # Get image size from first image
        h, w = self.images[0].shape[:2]
        image_size = (w, h)
        
        print(f"Calibrating camera ({w}x{h})...")
        print(f"Using {len(self.corners_list)} images")
        
        # Perform calibration
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            obj_points,
            img_points,
            image_size,
            None,
            None
        )
        
        if not ret:
            print("Calibration failed")
            return None
        
        # Calculate reprojection error
        total_error = 0
        for i in range(len(self.corners_list)):
            img_points_reproj, _ = cv2.projectPoints(
                self.object_points,
                rvecs[i],
                tvecs[i],
                camera_matrix,
                dist_coeffs
            )
            error = cv2.norm(self.corners_list[i], img_points_reproj, cv2.NORM_L2) / len(img_points_reproj)
            total_error += error
        
        mean_error = total_error / len(self.corners_list)
        
        print(f"Calibration complete!")
        print(f"Mean reprojection error: {mean_error:.4f} pixels")
        print(f"Focal lengths: fx={camera_matrix[0,0]:.2f}, fy={camera_matrix[1,0]:.2f}")
        print(f"Principal point: cx={camera_matrix[0,2]:.2f}, cy={camera_matrix[1,2]:.2f}")
        
        return CalibrationData(
            camera_matrix=camera_matrix,
            dist_coeffs=dist_coeffs,
            image_size=image_size,
            reprojection_error=mean_error,
            calibration_images=len(self.corners_list)
        )
    
    def calibrate_from_images(self, image_paths: List[str]) -> Optional[CalibrationData]:
        """
        Calibrate from a list of image file paths.
        
        Args:
            image_paths: List of paths to calibration images
            
        Returns:
            CalibrationData or None if failed
        """
        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                print(f"Failed to load: {path}")
                continue
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.checkerboard, None)
            
            if ret:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                self.corners_list.append(corners_refined)
                self.images.append(img)
        
        return self.calibrate()
    
    @staticmethod
    def undistort(
        image: np.ndarray,
        calibration: CalibrationData
    ) -> np.ndarray:
        """
        Undistort an image using calibration parameters.
        
        Args:
            image: Distorted input image
            calibration: CalibrationData with intrinsics
            
        Returns:
            Undistorted image
        """
        h, w = image.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            calibration.camera_matrix,
            calibration.dist_coeffs,
            (w, h),
            1,
            (w, h)
        )
        
        undistorted = cv2.undistort(
            image,
            calibration.camera_matrix,
            calibration.dist_coeffs,
            None,
            new_camera_matrix
        )
        
        # Crop to ROI
        x, y, w, h = roi
        if w > 0 and h > 0:
            undistorted = undistorted[y:y+h, x:x+w]
        
        return undistorted


def save_calibration(
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
    image_size: Tuple[int, int],
    filepath: str,
    reprojection_error: float = 0.0,
    num_images: int = 0
) -> None:
    """Save calibration to JSON file."""
    data = {
        'camera_matrix': camera_matrix.tolist(),
        'dist_coeffs': dist_coeffs.tolist(),
        'image_size': list(image_size),
        'reprojection_error': float(reprojection_error),
        'calibration_images': num_images
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def load_calibration(filepath: str) -> CalibrationData:
    """Load calibration from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return CalibrationData(
        camera_matrix=np.array(data['camera_matrix']),
        dist_coeffs=np.array(data['dist_coeffs']),
        image_size=tuple(data['image_size']),
        reprojection_error=data.get('reprojection_error', 0.0),
        calibration_images=data.get('calibration_images', 0)
    )
