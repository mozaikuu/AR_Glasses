"""
ArucoDetector - Marker detection using OpenCV ArUco

Provides robust detection of ArUco markers with configurable
dictionary and detection parameters.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class DetectionResult:
    """Result of marker detection."""
    corners: Optional[np.ndarray]  # Shape: (N, 4, 2) - N markers, 4 corners each
    ids: Optional[np.ndarray]      # Shape: (N,) - marker IDs
    rejected: Optional[np.ndarray] # Rejected candidates
    
    @property
    def num_detected(self) -> int:
        """Number of successfully detected markers."""
        return len(self.ids) if self.ids is not None else 0
    
    def is_empty(self) -> bool:
        """Check if any markers were detected."""
        return self.num_detected == 0


class ArucoDetector:
    """
    ArUco marker detector with configurable parameters.
    
    Usage:
        detector = ArucoDetector(dictionary_id=cv2.aruco.DICT_6X6_250)
        result = detector.detect(frame)
        if result.ids is not None:
            print(f"Detected {result.num_detected} markers")
    """
    
    # Predefined dictionary configurations
    DICTIONARY_CONFIGS = {
        '4x4_50': cv2.aruco.DICT_4X4_50,
        '4x4_100': cv2.aruco.DICT_4X4_100,
        '4x4_250': cv2.aruco.DICT_4X4_250,
        '4x4_1000': cv2.aruco.DICT_4X4_1000,
        '5x5_50': cv2.aruco.DICT_5X5_50,
        '5x5_100': cv2.aruco.DICT_5X5_100,
        '5x5_250': cv2.aruco.DICT_5X5_250,
        '5x5_1000': cv2.aruco.DICT_5X5_1000,
        '6x6_50': cv2.aruco.DICT_6X6_50,
        '6x6_100': cv2.aruco.DICT_6X6_100,
        '6x6_250': cv2.aruco.DICT_6X6_250,
        '6x6_1000': cv2.aruco.DICT_6X6_1000,
        '7x7_50': cv2.aruco.DICT_7X7_50,
        '7x7_100': cv2.aruco.DICT_7X7_100,
        '7x7_250': cv2.aruco.DICT_7X7_250,
        '7x7_1000': cv2.aruco.DICT_7X7_1000,
    }
    
    def __init__(
        self,
        dictionary_id: int = cv2.aruco.DICT_6X6_250,
        detection_params: Optional[cv2.aruco_DetectorParameters] = None
    ):
        """
        Initialize the detector.
        
        Args:
            dictionary_id: OpenCV ArUco dictionary ID
            detection_params: Optional custom detector parameters
        """
        self.dictionary = cv2.aruco.Dictionary_get(dictionary_id)
        
        if detection_params is None:
            self.params = cv2.aruco.DetectorParameters_create()
            # Configure for robustness
            self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
            self.params.cornerRefinementWinSize = 5
            self.params.cornerRefinementMaxIterations = 50
            self.params.cornerRefinementMinAccuracy = 0.01
            self.params.adaptiveThreshWinSize = 19
            self.params.adaptiveThreshConstant = 7
        else:
            self.params = detection_params
        
        self.dictionary_id = dictionary_id
    
    @classmethod
    def from_name(cls, name: str) -> 'ArucoDetector':
        """Create detector from dictionary name."""
        if name not in cls.DICTIONARY_CONFIGS:
            raise ValueError(f"Unknown dictionary: {name}. Choose from: {list(cls.DICTIONARY_CONFIGS.keys())}")
        return cls(cls.DICTIONARY_CONFIGS[name])
    
    def detect(self, image: np.ndarray) -> DetectionResult:
        """
        Detect ArUco markers in an image.
        
        Args:
            image: BGR or grayscale image (uint8)
            
        Returns:
            DetectionResult with corners, ids, and rejected candidates
            
        Note:
            - Input image should be 8-bit grayscale or BGR
            - Corner order: [top-left, top-right, bottom-right, bottom-left]
            - Corners are in image pixel coordinates
        """
        if image.dtype != np.uint8:
            raise ValueError("Image must be uint8")
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect markers
        corners, ids, rejected = cv2.aruco.detectMarkers(
            gray, self.dictionary, parameters=self.params
        )
        
        return DetectionResult(
            corners= corners,
            ids= ids,
            rejected= rejected
        )
    
    def detect_with_refinement(self, image: np.ndarray) -> DetectionResult:
        """
        Detect markers with additional corner refinement.
        
        Use this for higher precision at the cost of speed.
        """
        # First pass detection
        result = self.detect(image)
        
        if result.num_detected == 0:
            return result
        
        # Refine corner positions using subpixel detection
        refined_corners = []
        refined_ids = []
        
        for corners, marker_id in zip(result.corners, result.ids):
            # OpenCV cornerSubPix for subpixel accuracy
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.0001)
            refined = cv2.cornerSubPix(
                gray=image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
                corners=corners,
                winSize=(3, 3),
                zeroZone=(-1, -1),
                criteria=criteria
            )
            refined_corners.append(refined)
            refined_ids.append(marker_id)
        
        return DetectionResult(
            corners= np.array(refined_corners),
            ids= np.array(refined_ids),
            rejected= result.rejected
        )
    
    def draw_results(
        self,
        image: np.ndarray,
        result: DetectionResult,
        draw_rejected: bool = False,
        draw_axis: bool = False,
        camera_matrix: Optional[np.ndarray] = None,
        dist_coeffs: Optional[np.ndarray] = None,
        marker_size: float = 0.03
    ) -> np.ndarray:
        """
        Draw detection results on image for debugging.
        
        Args:
            image: Input image (will be copied)
            result: DetectionResult from detect()
            draw_rejected: Also draw rejected candidates
            draw_axis: Draw 3D axes on markers (requires calibration)
            camera_matrix: 3×3 camera intrinsic matrix
            dist_coeffs: Distortion coefficients
            marker_size: Marker side length in meters
            
        Returns:
            Image with drawings overlaid
        """
        output = image.copy()
        
        if result.ids is not None:
            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(output, result.corners, result.ids)
            
            # Draw axes if calibration data provided
            if draw_axis and camera_matrix is not None and dist_coeffs is not None:
                for corners in result.corners:
                    # Use center of marker for axis origin
                    center = corners[0].mean(axis=0)
                    # Estimate pose (simplified - use full pose estimator for accuracy)
                    rvec, _ = cv2.Rodrigues(np.eye(3))  # Identity rotation
                    tvec = np.array([[0, 0, marker_size * 2]])
                    cv2.drawFrameAxes(output, camera_matrix, dist_coeffs, rvec, tvec, marker_size * 0.5)
        
        if draw_rejected and result.rejected is not None:
            cv2.aruco.drawDetectedMarkers(output, result.rejected, borderColor=(0, 0, 255))
        
        return output
    
    def get_dictionary_info(self) -> dict:
        """Get information about the current dictionary."""
        return {
            'dictionary_id': self.dictionary_id,
            'marker_bits': self.dictionary.markerSize,
            'max_count': self.dictionary.maxSize,
        }
