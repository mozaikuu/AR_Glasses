"""
AR Pipeline for Smart Glasses

A modular, marker-based AR pipeline using OpenCV and Three.js.
Designed for ESP32-class smart glasses with phone gateway compute.

Modules:
- tracking: Marker detection and pose estimation
- calibration: Camera calibration utilities
- rendering: WebGL/Three.js rendering
- transport: WebSocket-based frame streaming
- utils: Helper utilities (marker generation, etc.)
"""

from .tracking import ArucoDetector, PoseEstimator
from .calibration import CameraCalibrator, CalibrationData
from .transport import FrameStreamer, FrameReceiver

__version__ = '0.1.0'
__author__ = 'Smart Glasses Team'

__all__ = [
    'ArucoDetector',
    'PoseEstimator',
    'CameraCalibrator',
    'CalibrationData',
    'FrameStreamer',
    'FrameReceiver',
]
