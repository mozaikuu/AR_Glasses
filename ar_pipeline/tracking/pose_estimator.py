"""
PoseEstimator - Camera pose estimation from ArUco markers

Computes the transformation matrix from camera to marker/world
using detected marker corners and camera calibration parameters.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
from .aruco_detector import DetectionResult


@dataclass
class PoseResult:
    """Result of pose estimation."""
    # Pose relative to each detected marker
    rvecs: Optional[np.ndarray]  # Shape: (N, 3) - rotation vectors
    tvecs: Optional[np.ndarray]  # Shape: (N, 3) - translation vectors (meters)
    # Homogeneous transformation matrices
    T_cm: Optional[np.ndarray]   # Shape: (N, 4, 4) - camera to marker transforms
    # Success status
    success: bool
    # Number of successful pose estimates
    num_estimates: int = 0
    
    def __post_init__(self):
        if self.success and self.rvecs is not None:
            self.num_estimates = len(self.rvecs)
    
    def is_empty(self) -> bool:
        """Check if any poses were estimated."""
        return not self.success or self.num_estimates == 0


@dataclass
class CameraCalibration:
    """Camera calibration parameters."""
    camera_matrix: np.ndarray  # 3×3 intrinsic matrix
    dist_coeffs: np.ndarray    # Distortion coefficients (4, 5, or 8 elements)
    image_size: Tuple[int, int]  # (width, height)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'CameraCalibration':
        """Load calibration from JSON file."""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return cls(
            camera_matrix=np.array(data['camera_matrix']),
            dist_coeffs=np.array(data['dist_coeffs']),
            image_size=tuple(data['image_size'])
        )
    
    def save(self, filepath: str) -> None:
        """Save calibration to JSON file."""
        import json
        data = {
            'camera_matrix': self.camera_matrix.tolist(),
            'dist_coeffs': self.dist_coeffs.tolist(),
            'image_size': list(self.image_size)
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def validate(self, max_reprojection_error: float = 1.0) -> Tuple[bool, float]:
        """
        Validate calibration quality.
        
        Args:
            max_reprojection_error: Maximum acceptable average error in pixels
            
        Returns:
            (is_valid, reprojection_error)
        """
        # Simple heuristic: check if matrix values are reasonable
        fx, fy = self.camera_matrix[0, 0], self.camera_matrix[1, 1]
        cx, cy = self.camera_matrix[0, 2], self.camera_matrix[1, 2]
        
        # Focal lengths should be positive and reasonable for image size
        w, h = self.image_size
        if not (10 < fx < w * 10 and 10 < fy < h * 10):
            return False, float('inf')
        
        # Principal point should be near image center
        if not (w * 0.2 < cx < w * 0.8 and h * 0.2 < cy < h * 0.8):
            return False, float('inf')
        
        return True, 0.0  # Full validation requires original calibration data


class PoseEstimator:
    """
    Estimate camera pose from detected ArUco markers.
    
    Uses the Perspective-n-Point (PnP) algorithm to compute
    the transformation from camera to marker coordinate frame.
    """
    
    SOLVER_METHODS = {
        'iterative': cv2.SOLVEPNP_ITERATIVE,
        'p3p': cv2.SOLVEPNP_P3P,
        'ap3p': cv2.SOLVEPNP_AP3P,
        'epnp': cv2.SOLVEPNP_EPNP,
        'dls': cv2.SOLVEPNP_DLS,
        'upnp': cv2.SOLVEPNP_UPNP,
    }
    
    def __init__(
        self,
        calibration: CameraCalibration,
        marker_size: float = 0.03,
        solver_method: str = 'iterative'
    ):
        """
        Initialize the pose estimator.
        
        Args:
            calibration: Camera calibration parameters
            marker_size: Side length of marker in meters
            solver_method: PnP solver algorithm ('iterative', 'p3p', 'epnp', etc.)
        """
        self.calibration = calibration
        self.marker_size = marker_size
        self.solver_flag = self.SOLVER_METHODS.get(solver_method, cv2.SOLVEPNP_ITERATIVE)
        
        # Precompute marker object points (4 corners in marker frame)
        # Marker frame: Z-axis points out of marker, origin at center
        half = marker_size / 2
        self.marker_object_points = np.array([
            [-half, -half, 0],   # top-left
            [ half, -half, 0],   # top-right
            [ half,  half, 0],   # bottom-right
            [-half,  half, 0],   # bottom-left
        ], dtype=np.float64)
    
    def estimate(
        self,
        detection: DetectionResult,
        refine_corners: bool = False
    ) -> PoseResult:
        """
        Estimate camera pose from detected markers.
        
        Args:
            detection: DetectionResult from ArucoDetector
            refine_corners: Apply subpixel refinement to corners
            
        Returns:
            PoseResult with rotation, translation, and transformation matrices
            
        Note:
            The returned transformation T_cm transforms points from
            marker frame to camera frame:
                P_camera = T_cm @ P_marker (in homogeneous coordinates)
        """
        if detection.is_empty():
            return PoseResult(
                rvecs=None,
                tvecs=None,
                T_cm=None,
                success=False
            )
        
        rvecs = []
        tvecs = []
        
        mtx = self.calibration.camera_matrix
        dist = self.calibration.dist_coeffs
        
        for corners in detection.corners:
            # corners shape: (1, 4, 2)
            corners_2d = corners.reshape(-1, 2).astype(np.float64)
            
            if refine_corners:
                # Subpixel refinement
                gray = None  # Would need original gray image
                # For now, skip refinement
            
            # Solve PnP
            success, rvec, tvec = cv2.solvePnP(
                self.marker_object_points,
                corners_2d,
                mtx,
                dist,
                flags=self.solver_flag
            )
            
            if success:
                rvecs.append(rvec.flatten())
                tvecs.append(tvec.flatten())
        
        if not rvecs:
            return PoseResult(
                rvecs=None,
                tvecs=None,
                T_cm=None,
                success=False
            )
        
        rvecs = np.array(rvecs)
        tvecs = np.array(tvecs)
        
        # Convert to transformation matrices
        T_cm_list = []
        for rvec, tvec in zip(rvecs, tvecs):
            R, _ = cv2.Rodrigues(rvec)
            T = np.eye(4)
            T[:3, :3] = R
            T[:3, 3] = tvec
            T_cm_list.append(T)
        
        T_cm = np.array(T_cm_list)
        
        return PoseResult(
            rvecs=rvecs,
            tvecs=tvecs,
            T_cm=T_cm,
            success=True,
            num_estimates=len(rvecs)
        )
    
    def estimate_single(
        self,
        corners: np.ndarray,
        marker_id: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Estimate pose for a single marker.
        
        Args:
            corners: 4×2 array of corner coordinates
            marker_id: Marker ID (for logging)
            
        Returns:
            (rvec, tvec) or (None, None) if failed
        """
        result = self.estimate(
            DetectionResult(
                corners=np.array([corners]),
                ids=np.array([marker_id]),
                rejected=None
            )
        )
        
        if result.is_empty():
            return None, None
        
        return result.rvecs[0], result.tvecs[0]
    
    def world_to_camera_transform(
        self,
        T_wm: np.ndarray,
        T_cm: np.ndarray
    ) -> np.ndarray:
        """
        Compute camera pose in world frame.
        
        T_wc = T_wm × T_cm
        
        Where:
            T_wm: Marker pose in world frame (4×4)
            T_cm: Camera pose relative to marker (4×4)
            
        Returns:
            T_wc: Camera pose in world frame (4×4)
        """
        return T_wm @ T_cm
    
    def camera_to_world_transform(self, T_wc: np.ndarray) -> np.ndarray:
        """
        Compute inverse transformation (world to camera).
        
        T_cw = T_wc^(-1)
        """
        return np.linalg.inv(T_wc)
    
    def transform_point(self, point: np.ndarray, T: np.ndarray) -> np.ndarray:
        """
        Transform a 3D point using homogeneous transformation.
        
        Args:
            point: 3D point (x, y, z)
            T: 4×4 transformation matrix
            
        Returns:
            Transformed 3D point
        """
        if point.shape == (3,):
            point_h = np.append(point, 1.0)
        else:
            point_h = point
        
        result = T @ point_h
        return result[:3]
    
    def get_pose_for_marker(
        self,
        detection: DetectionResult,
        pose: PoseResult,
        target_id: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get pose specifically for a marker ID.
        
        Args:
            detection: DetectionResult containing marker IDs
            pose: PoseResult with estimated poses
            target_id: Marker ID to retrieve
            
        Returns:
            (rvec, tvec) for the target marker, or (None, None)
        """
        if detection.ids is None or pose.is_empty():
            return None, None
        
        idx = np.where(detection.ids == target_id)[0]
        if len(idx) == 0:
            return None, None
        
        i = idx[0]
        return pose.rvecs[i], pose.tvecs[i]
    
    def rotation_matrix_to_quaternion(self, R: np.ndarray) -> np.ndarray:
        """Convert 3×3 rotation matrix to quaternion."""
        # Using cv2.Rodrigues inverse
        rvec, _ = cv2.Rodrigues(R)
        q = np.zeros(4)
        q[0] = rvec[0, 0]
        q[1] = rvec[1, 0]
        q[2] = rvec[2, 0]
        # Normalize
        norm = np.linalg.norm(q)
        if norm > 1e-6:
            q /= norm
        # Convert to quaternion
        theta = norm
        if theta > 1e-6:
            q = np.array([
                np.sin(theta/2) * q[0] / theta,
                np.sin(theta/2) * q[1] / theta,
                np.sin(theta/2) * q[2] / theta,
                np.cos(theta/2)
            ])
        return q
    
    def quaternion_to_rotation_matrix(self, q: np.ndarray) -> np.ndarray:
        """Convert quaternion to 3×3 rotation matrix."""
        w, x, y, z = q[3], q[0], q[1], q[2]
        
        R = np.array([
            [1-2*y*y-2*z*z, 2*x*y-2*w*z, 2*x*z+2*w*y],
            [2*x*y+2*w*z, 1-2*x*x-2*z*z, 2*y*z-2*w*x],
            [2*x*z-2*w*y, 2*y*z+2*w*x, 1-2*x*x-2*y*y]
        ])
        return R
