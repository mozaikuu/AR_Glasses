"""
Marker Generator - Create printable ArUco markers

Generates ArUco markers as images for printing.
Supports single markers or grid layouts.
"""

import cv2
import numpy as np
from typing import List, Optional
from pathlib import Path


class ArucoMarkerGenerator:
    """
    Generate printable ArUco marker images.
    
    Usage:
        gen = ArucoMarkerGenerator()
        gen.generate_marker(0, size=200, output="marker_0.png")
        gen.generate_grid([0, 1, 2, 3], size=100, output="markers.png")
    """
    
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
    
    def __init__(self, dictionary_name: str = '6x6_250'):
        """
        Initialize marker generator.
        
        Args:
            dictionary_name: Name of dictionary configuration
        """
        if dictionary_name not in self.DICTIONARY_CONFIGS:
            raise ValueError(f"Unknown dictionary: {dictionary_name}")
        
        self.dictionary_id = self.DICTIONARY_CONFIGS[dictionary_name]
        self.dictionary = cv2.aruco.Dictionary_get(self.dictionary_id)
    
    def generate_marker(
        self,
        marker_id: int,
        pixel_size: int = 200,
        border_bits: int = 1,
        output: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate a single ArUco marker.
        
        Args:
            marker_id: Marker ID to generate
            pixel_size: Size of marker in pixels (before border)
            border_bits: Width of border in bits
            output: Optional file path to save
            
        Returns:
            Marker image as numpy array
        """
        # Total size including border
        total_size = pixel_size + 2 * border_bits * pixel_size // self.dictionary.markerSize
        
        # Generate marker
        marker = np.zeros((total_size, total_size), dtype=np.uint8)
        
        # Get marker bits
        bits = self.dictionary.bytesList[marker_id].reshape(
            self.dictionary.markerSize,
            self.dictionary.markerSize
        )
        
        # Scale and place marker bits
        cell_size = pixel_size // self.dictionary.markerSize
        
        for i in range(self.dictionary.markerSize):
            for j in range(self.dictionary.markerSize):
                if bits[i, j]:
                    x = border_bits * cell_size + j * cell_size
                    y = border_bits * cell_size + i * cell_size
                    marker[y:y+cell_size, x:x+cell_size] = 255
        
        if output:
            cv2.imwrite(output, marker)
        
        return marker
    
    def generate_grid(
        self,
        marker_ids: List[int],
        pixel_size: int = 100,
        cols: int = 4,
        border_bits: int = 1,
        spacing: int = 20,
        output: Optional[str] = None,
        with_labels: bool = True
    ) -> np.ndarray:
        """
        Generate a grid of multiple markers.
        
        Args:
            marker_ids: List of marker IDs to generate
            pixel_size: Size of each marker
            cols: Number of markers per row
            border_bits: Border width in bits
            spacing: Spacing between markers in pixels
            output: Optional file path to save
            with_labels: Add ID labels below markers
            
        Returns:
            Grid image as numpy array
        """
        rows = (len(marker_ids) + cols - 1) // cols
        
        marker_with_border = pixel_size + 2 * border_bits * pixel_size // self.dictionary.markerSize
        label_height = 30 if with_labels else 0
        
        cell_width = marker_with_border + spacing
        cell_height = marker_with_border + spacing + label_height
        
        grid_width = cols * cell_width - spacing
        grid_height = rows * cell_height - spacing + 20  # Extra top margin
        
        grid = np.ones((grid_height, grid_width), dtype=np.uint8) * 255
        
        for idx, marker_id in enumerate(marker_ids):
            row = idx // cols
            col = idx % cols
            
            marker = self.generate_marker(marker_id, pixel_size, border_bits)
            
            x = col * cell_width
            y = row * cell_height + 10  # Top margin
            
            # Place marker
            grid[y:y+marker_with_border, x:x+marker_with_border] = marker
            
            # Add label
            if with_labels:
                label_y = y + marker_with_border + 5
                cv2.putText(
                    grid,
                    f"ID: {marker_id}",
                    (x + 10, label_y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    0,
                    2
                )
        
        if output:
            cv2.imwrite(output, grid)
        
        return grid
    
    def generate_calibration_board(
        self,
        marker_ids: Optional[List[int]] = None,
        marker_size: int = 100,
        rows: int = 4,
        cols: int = 5,
        spacing: float = 0.05,
        output: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate an ArUco calibration board.
        
        Uses ChArUco board (checkerboard + ArUco markers).
        
        Args:
            marker_ids: Marker IDs to use (auto-generated if None)
            marker_size: Marker size in pixels
            rows: Number of checkerboard rows
            cols: Number of checkerboard columns
            spacing: Spacing between markers in meters
            output: Optional file path to save
            
        Returns:
            Calibration board image
        """
        if marker_ids is None:
            marker_ids = list(range(rows * cols))
        
        board_size = (cols * marker_size + (cols + 1) * int(spacing * 1000),
                     rows * marker_size + (rows + 1) * int(spacing * 1000))
        
        board = np.ones((board_size[1], board_size[0]), dtype=np.uint8) * 255
        
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if idx >= len(marker_ids):
                    break
                
                marker = self.generate_marker(marker_ids[idx], marker_size)
                
                x = c * marker_size + (c + 1) * int(spacing * 1000)
                y = r * marker_size + (r + 1) * int(spacing * 1000)
                
                board[y:y+marker.shape[0], x:x+marker.shape[1]] = marker
        
        if output:
            cv2.imwrite(output, board)
        
        return board
    
    def print_instructions(self, output: Optional[str] = None) -> np.ndarray:
        """
        Generate an instruction sheet for calibration.
        
        Returns:
            Instruction image
        """
        height, width = 800, 600
        img = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        cv2.putText(img, "Camera Calibration Instructions", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        instructions = [
            "1. Print this calibration pattern",
            "2. Use the checkerboard pattern for intrinsic calibration",
            "3. Capture 20+ images from different angles",
            "4. Ensure the board is fully visible in each image",
            "5. Cover the board at various distances (0.3m - 1.0m)",
            "6. Good lighting improves accuracy",
            "",
            "Expected accuracy: < 0.5 pixels reprojection error"
        ]
        
        for i, line in enumerate(instructions):
            cv2.putText(img, line, (50, 120 + i * 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
        
        if output:
            cv2.imwrite(output, img)
        
        return img


def generate_marker_dictionary(
    min_id: int = 0,
    max_id: int = 50,
    dictionary_name: str = '6x6_250',
    output_dir: str = "markers"
) -> None:
    """
    Generate a range of markers as individual files.
    
    Args:
        min_id: Starting marker ID
        max_id: Ending marker ID (exclusive)
        dictionary_name: ArUco dictionary to use
        output_dir: Directory to save markers
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    gen = ArucoMarkerGenerator(dictionary_name)
    
    for marker_id in range(min_id, max_id):
        filename = f"{output_dir}/marker_{marker_id:03d}.png"
        gen.generate_marker(marker_id, pixel_size=300, output=filename)
        print(f"Generated: {filename}")


if __name__ == "__main__":
    # Generate sample markers
    gen = ArucoMarkerGenerator('6x6_250')
    
    # Generate single markers
    for i in range(5):
        gen.generate_marker(i, pixel_size=200, output=f"marker_{i}.png")
    
    # Generate grid
    gen.generate_grid(
        list(range(12)),
        pixel_size=100,
        cols=4,
        output="marker_grid.png"
    )
    
    print("Generated marker files")
