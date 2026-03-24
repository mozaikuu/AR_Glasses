"""QR Code Location Tracking Module for Smart Glasses.

This module handles:
- Parsing QR code data from location markers
- Tracking current user location based on scanned QR codes
- Providing location information to the ESP32 firmware
- Integrating with navigation system
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


# Path to navigation data
NAVIGATION_JSON = "navigation.json"


@dataclass
class LocationData:
    """Data class for location information from QR code."""
    type: str = "location"
    id: str = ""
    name: str = ""
    building: str = ""
    floor: int = 0
    coordinates: Dict[str, float] = None
    description: str = ""
    additional_info: str = ""
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.coordinates is None:
            self.coordinates = {"x": 0, "y": 0}


class QRLocationTracker:
    """Track user location based on scanned QR codes."""
    
    def __init__(self, navigation_path: str = NAVIGATION_JSON):
        self.navigation_path = navigation_path
        self.navigation_data = None
        self.current_location: Optional[LocationData] = None
        self.location_history: List[LocationData] = []
        self._load_navigation_data()
    
    def _load_navigation_data(self) -> None:
        """Load navigation data from JSON file."""
        if os.path.exists(self.navigation_path):
            with open(self.navigation_path, 'r', encoding='utf-8') as f:
                self.navigation_data = json.load(f)
        else:
            print(f"Warning: Navigation file not found: {self.navigation_path}")
            self.navigation_data = None
    
    def reload_data(self) -> None:
        """Reload navigation data from file."""
        self._load_navigation_data()
    
    def parse_qr_data(self, qr_data: str) -> Optional[LocationData]:
        """
        Parse QR code data and return LocationData.
        
        Args:
            qr_data: JSON string from QR code
            
        Returns:
            LocationData object or None if parsing fails
        """
        try:
            data = json.loads(qr_data)
            location = LocationData(
                type=data.get("type", "location"),
                id=data.get("id", ""),
                name=data.get("name", ""),
                building=data.get("building", ""),
                floor=data.get("floor", 0),
                coordinates=data.get("coordinates", {"x": 0, "y": 0}),
                description=data.get("description", ""),
                additional_info=data.get("additional_info", ""),
                timestamp=datetime.utcnow().isoformat()
            )
            return location
        except json.JSONDecodeError as e:
            print(f"Error parsing QR data: {e}")
            return None
    
    def update_location(self, qr_data: str) -> Optional[LocationData]:
        """
        Update current location when a QR code is scanned.
        
        Args:
            qr_data: JSON string from QR code
            
        Returns:
            LocationData object or None if parsing fails
        """
        location = self.parse_qr_data(qr_data)
        if location:
            self.current_location = location
            self.location_history.append(location)
            print(f"Location updated to: {location.name} (Floor {location.floor})")
        return location
    
    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get current location data as dictionary."""
        if self.current_location:
            return asdict(self.current_location)
        return None
    
    def get_location_by_id(self, location_id: str) -> Optional[LocationData]:
        """
        Get location data by ID from navigation data.
        
        Args:
            location_id: The location ID to look up
            
        Returns:
            LocationData object or None if not found
        """
        if not self.navigation_data:
            return None
        
        for location in self.navigation_data.get("locations", []):
            if location.get("id") == location_id:
                return LocationData(
                    type="location",
                    id=location.get("id"),
                    name=location.get("name"),
                    building=self.navigation_data.get("building", {}).get("name", ""),
                    floor=location.get("floor", 0),
                    coordinates=location.get("coordinates", {"x": 0, "y": 0}),
                    description=location.get("description", ""),
                    additional_info=location.get("additional_info", ""),
                    timestamp=None
                )
        return None
    
    def get_all_locations(self) -> List[LocationData]:
        """Get all locations from navigation data."""
        locations = []
        if self.navigation_data:
            for loc in self.navigation_data.get("locations", []):
                locations.append(LocationData(
                    type="location",
                    id=loc.get("id"),
                    name=loc.get("name"),
                    building=self.navigation_data.get("building", {}).get("name", ""),
                    floor=loc.get("floor", 0),
                    coordinates=loc.get("coordinates", {"x": 0, "y": 0}),
                    description=loc.get("description", ""),
                    additional_info=loc.get("additional_info", ""),
                    timestamp=None
                ))
        return locations
    
    def get_navigation_info(self, from_id: str, to_id: str) -> Optional[Dict[str, Any]]:
        """
        Get navigation instructions from one location to another.
        
        Args:
            from_id: Starting location ID
            to_id: Destination location ID
            
        Returns:
            Dictionary with navigation info or None if not possible
        """
        from_location = self.get_location_by_id(from_id)
        to_location = self.get_location_by_id(to_id)
        
        if not from_location or not to_location:
            return None
        
        return {
            "from": asdict(from_location),
            "to": asdict(to_location),
            "distance": self._calculate_distance(
                from_location.coordinates,
                to_location.coordinates
            ),
            "floor_change": to_location.floor - from_location.floor
        }
    
    def _calculate_distance(self, from_coords: Dict[str, float], to_coords: Dict[str, float]) -> float:
        """Calculate Euclidean distance between two coordinates."""
        import math
        return math.sqrt(
            (to_coords["x"] - from_coords["x"])**2 +
            (to_coords["y"] - from_coords["y"])**2
        )
    
    def export_location_history(self) -> List[Dict[str, Any]]:
        """Export location history as list of dictionaries."""
        return [asdict(loc) for loc in self.location_history]


# Global tracker instance
_tracker: Optional[QRLocationTracker] = None


def get_tracker() -> QRLocationTracker:
    """Get or create the global QR location tracker."""
    global _tracker
    if _tracker is None:
        _tracker = QRLocationTracker()
    return _tracker


def update_location_from_qr(qr_data: str) -> Optional[Dict[str, Any]]:
    """
    Update current location from QR code data.
    
    Args:
        qr_data: JSON string from QR code
        
    Returns:
        Dictionary with location info or None if parsing fails
    """
    tracker = get_tracker()
    location = tracker.update_location(qr_data)
    if location:
        return asdict(location)
    return None


def get_current_location_info() -> Optional[Dict[str, Any]]:
    """Get current location info."""
    tracker = get_tracker()
    return tracker.get_current_location()


def get_all_locations_info() -> List[Dict[str, Any]]:
    """Get all available locations."""
    tracker = get_tracker()
    return [asdict(loc) for loc in tracker.get_all_locations()]
