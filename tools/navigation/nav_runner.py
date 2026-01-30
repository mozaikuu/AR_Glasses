"""Navigation session manager for step-by-step indoor guidance."""
import uuid
from typing import Optional, Dict, Any
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.navigation.navigation import load_graph, astar


class NavigationSession:
    """Manages a navigation session with step-by-step guidance."""

    def __init__(self, start: str, destination: str):
        self.session_id: str = str(uuid.uuid4())[:8]
        self.start = start
        self.destination = destination
        self.current_step_index = -1  # -1 means not started yet
        self.path: list = []
        self.steps: list = []
        self.total_distance = 0
        self.completed = False
        self._calculate_route()

    def _calculate_route(self):
        """Calculate the route from start to destination."""
        graph = load_graph()
        self.path, self.total_distance, self.steps = astar(graph, self.start, self.destination)

    def get_total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)

    def get_current_step(self) -> Optional[Dict[str, Any]]:
        """Get current step information (before starting, returns welcome message)."""
        if self.current_step_index == -1:
            return {
                "step": 0,
                "type": "welcome",
                "instruction": f"Ready to navigate from {self.start} to {self.destination}",
                "total_steps": self.get_total_steps(),
                "distance": self.total_distance
            }
        elif self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        else:
            return {
                "step": self.current_step_index + 1,
                "type": "arrival",
                "instruction": f"You have arrived at {self.destination}",
                "from": self.destination
            }

    def next_step(self) -> Dict[str, Any]:
        """Advance to the next step and return its information."""
        if self.completed:
            return {
                "step": self.current_step_index + 1,
                "type": "arrival",
                "instruction": f"You have already arrived at {self.destination}",
                "from": self.destination
            }

        self.current_step_index += 1

        if self.current_step_index >= len(self.steps):
            self.completed = True
            return {
                "step": self.current_step_index + 1,
                "type": "arrival",
                "instruction": f"You have arrived at {self.destination}",
                "from": self.destination
            }

        return self.steps[self.current_step_index]

    def get_progress(self) -> Dict[str, Any]:
        """Get current navigation progress."""
        return {
            "session_id": self.session_id,
            "start": self.start,
            "destination": self.destination,
            "current_step": self.current_step_index + 1,
            "total_steps": self.get_total_steps(),
            "completed": self.completed,
            "progress_percent": round((self.current_step_index + 1) / max(len(self.steps), 1) * 100, 1)
        }

    def get_audio_text(self) -> str:
        """Get the current instruction text formatted for TTS audio."""
        current = self.get_current_step()
        if current and "instruction" in current:
            return current["instruction"]
        return ""

    def is_started(self) -> bool:
        """Check if navigation has started."""
        return self.current_step_index >= 0

    def is_finished(self) -> bool:
        """Check if navigation is complete."""
        return self.completed


# Global session storage (for single-user scenario)
# For multi-user, consider using a dictionary with session IDs
_nav_sessions: Dict[str, NavigationSession] = {}


def start_navigation(start: str, destination: str) -> Dict[str, Any]:
    """Start a new navigation session.

    Args:
        start: Starting location
        destination: Target destination

    Returns:
        Navigation session details
    """
    global _nav_sessions

    session = NavigationSession(start, destination)

    if not session.path:
        return {
            "success": False,
            "error": f"No path found from '{start}' to '{destination}'",
            "start": start,
            "destination": destination
        }

    _nav_sessions[session.session_id] = session

    return {
        "success": True,
        "session_id": session.session_id,
        "start": session.start,
        "destination": session.destination,
        "total_steps": session.get_total_steps(),
        "total_distance": session.total_distance,
        "first_step": session.get_current_step(),
        "message": "Navigation started. Say 'next' or 'continue' for the first instruction."
    }


def next_navigation_step(session_id: str = None) -> Dict[str, Any]:
    """Advance to the next navigation step.

    Args:
        session_id: Optional session ID. If not provided, uses the most recent session.

    Returns:
        Next step information
    """
    global _nav_sessions

    # Get session
    if session_id and session_id in _nav_sessions:
        session = _nav_sessions[session_id]
    elif _nav_sessions:
        session = list(_nav_sessions.values())[-1]
        session_id = session.session_id
    else:
        return {
            "success": False,
            "error": "No active navigation session. Say 'navigate to [destination]' to start."
        }

    step_info = session.next_step()

    # Check if arrived
    if step_info.get("type") == "arrival":
        # Clean up session after arrival
        del _nav_sessions[session_id]

    return {
        "success": True,
        "session_id": session_id,
        "step": step_info,
        "progress": session.get_progress(),
        "audio_text": step_info.get("instruction", "")
    }


def get_navigation_status(session_id: str = None) -> Dict[str, Any]:
    """Get current navigation status.

    Args:
        session_id: Optional session ID. If not provided, uses the most recent session.

    Returns:
        Current navigation status
    """
    global _nav_sessions

    if session_id and session_id in _nav_sessions:
        session = _nav_sessions[session_id]
        return {
            "success": True,
            "session": session.get_progress(),
            "current_instruction": session.get_current_step()
        }
    elif _nav_sessions:
        session = list(_nav_sessions.values())[-1]
        return {
            "success": True,
            "session": session.get_progress(),
            "current_instruction": session.get_current_step()
        }
    else:
        return {
            "success": False,
            "error": "No active navigation session",
            "current_instruction": None
        }


def cancel_navigation(session_id: str = None) -> Dict[str, Any]:
    """Cancel the current navigation session.

    Args:
        session_id: Optional session ID. If not provided, cancels the most recent session.

    Returns:
        Cancellation confirmation
    """
    global _nav_sessions

    if session_id and session_id in _nav_sessions:
        session = _nav_sessions.pop(session_id)
        return {
            "success": True,
            "message": f"Navigation from {session.start} to {session.destination} cancelled"
        }
    elif _nav_sessions:
        session = _nav_sessions.popitem()
        return {
            "success": True,
            "message": f"Navigation from {session[1].start} to {session[1].destination} cancelled"
        }

    return {
        "success": False,
        "error": "No active navigation session to cancel"
    }