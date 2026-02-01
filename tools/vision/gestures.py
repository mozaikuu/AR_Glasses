"""MediaPipe-based hand gesture detection for hands-free smart glasses control."""
from pathlib import Path
import sys
import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Lazy import MediaPipe to avoid startup issues
_mp_hands = None
_mp_drawing = None
_mp_drawing_styles = None


def _get_media_pipe_modules():
    """Lazy load MediaPipe modules."""
    global _mp_hands, _mp_drawing, _mp_drawing_styles
    if _mp_hands is None:
        import mediapipe as mp
        _mp_hands = mp.solutions.hands
        _mp_drawing = mp.solutions.drawing_utils
        _mp_drawing_styles = mp.solutions.drawing_styles
    return _mp_hands, _mp_drawing, _mp_drawing_styles


class GestureDetector:
    """Hand gesture detection using MediaPipe Hands."""

    def __init__(self, static_image_mode=False, max_hands=1, min_detection_confidence=0.7):
        """Initialize gesture detector.

        Args:
            static_image_mode: Whether to treat input as static images
            max_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum detection confidence threshold
        """
        self.hands = None
        self.static_image_mode = static_image_mode
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence

    def __enter__(self):
        """Context manager entry."""
        mp_hands, _, _ = _get_media_pipe_modules()
        self.hands = mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_hands=self.max_hands,
            min_detection_confidence=self.min_detection_confidence
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.hands:
            self.hands.close()

    def detect_gesture(self, frame):
        """Detect hand gestures in a frame.

        Args:
            frame: BGR image array (from cv2)

        Returns:
            dict with 'gesture' (str), 'handedness' (str), 'landmarks' (list)
        """
        mp_hands, mp_drawing, mp_drawing_styles = _get_media_pipe_modules()

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        # Process frame
        results = self.hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            return {"gesture": "none", "handedness": None, "landmarks": None}

        hand_landmarks = results.multi_hand_landmarks[0]
        handedness = results.multi_handedness[0].label if results.multi_handedness else "Unknown"

        # Detect gesture
        gesture = self._classify_gesture(hand_landmarks)

        # Return with landmarks for visualization
        return {
            "gesture": gesture,
            "handedness": handedness,
            "landmarks": [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
        }

    def _classify_gesture(self, landmarks):
        """Classify hand gesture from landmarks.

        Args:
            landmarks: MediaPipe hand landmarks

        Returns:
            Gesture name string
        """
        # Get key landmark positions
        thumb_tip = landmarks.landmark[4]
        index_tip = landmarks.landmark[8]
        middle_tip = landmarks.landmark[12]
        ring_tip = landmarks.landmark[16]
        pinky_tip = landmarks.landmark[20]

        thumb_ip = landmarks.landmark[3]
        index_pip = landmarks.landmark[6]
        middle_pip = landmarks.landmark[10]
        ring_pip = landmarks.landmark[14]
        pinky_pip = landmarks.landmark[18]

        wrist = landmarks.landmark[0]

        # Calculate finger curl states
        fingers = {}

        # Thumb: check if extended (tip is further from wrist than IP joint)
        thumb_extended = thumb_tip.y < thumb_ip.y
        fingers["thumb"] = thumb_extended

        # Other fingers: check if tip is above PIP joint (curled = tip is below PIP)
        fingers["index"] = index_tip.y < index_pip.y
        fingers["middle"] = middle_tip.y < middle_pip.y
        fingers["ring"] = ring_tip.y < ring_pip.y
        fingers["pinky"] = pinky_tip.y < pinky_pip.y

        extended_count = sum(fingers.values())

        # Gesture classification
        if extended_count == 5 and all(fingers.values()):
            return "open_hand"
        elif extended_count == 0:
            return "fist"
        elif fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            return "pointing"
        elif extended_count == 4:
            return "four_fingers"
        elif extended_count == 3 and fingers["index"] and fingers["middle"] and fingers["ring"]:
            return "three_fingers"
        elif extended_count == 2 and fingers["index"] and fingers["middle"]:
            return "peace_sign"
        elif extended_count == 1 and fingers["thumb"]:
            return "thumbs_up"
        elif not fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]:
            return "call_me"

        # Swipe detection (requires tracking over multiple frames)
        return "unknown"

    def draw_landmarks(self, frame, result):
        """Draw hand landmarks on frame for visualization.

        Args:
            frame: BGR image array
            result: Result dict from detect_gesture()

        Returns:
            Frame with landmarks drawn
        """
        if result["landmarks"] is None:
            return frame

        mp_hands, mp_drawing, mp_drawing_styles = _get_media_pipe_modules()

        # Create a dummy hand landmarks object for drawing
        class DummyLandmarks:
            def __init__(self, landmarks):
                self.landmark = [type('LM', (), {'x': l[0], 'y': l[1], 'z': l[2]})() for l in landmarks]

        dummy_landmarks = DummyLandmarks(result["landmarks"])

        # Draw
        mp_drawing.draw_landmarks(
            frame,
            dummy_landmarks,
            _mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )

        # Add gesture label
        cv2.putText(
            frame,
            f"Gesture: {result['gesture']}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0) if result["gesture"] != "none" else (0, 0, 255),
            2
        )

        return frame


def detect_gesture_from_frame(frame):
    """Convenience function to detect gesture in a single frame.

    Args:
        frame: BGR image array

    Returns:
        Gesture string
    """
    with GestureDetector() as detector:
        result = detector.detect_gesture(frame)
        return result["gesture"]


# Gesture to action mapping for smart glasses control
GESTURE_ACTIONS = {
    "open_hand": "STOP / CANCEL",
    "fist": "CONFIRM / SELECT",
    "pointing": "NEXT / CONTINUE",
    "peace_sign": "PREVIOUS / BACK",
    "thumbs_up": "ACCEPT / YES",
    "call_me": "EMERGENCY CALL",
    "four_fingers": "EXPAND / ZOOM IN",
    "three_fingers": "COLLAPSE / ZOOM OUT",
}


def get_action_for_gesture(gesture: str) -> str:
    """Get the smart glasses action for a detected gesture.

    Args:
        gesture: Detected gesture name

    Returns:
        Action description string
    """
    return GESTURE_ACTIONS.get(gesture, "Unknown gesture")


# Test function
if __name__ == "__main__":
    print("Hand Gesture Detection Test")
    print("=" * 50)
    print("Available gestures and actions:")
    for gesture, action in GESTURE_ACTIONS.items():
        print(f"  {gesture}: {action}")

    # Test with camera if available
    print("\nTesting with camera (press 'q' to exit)...")

    with GestureDetector() as detector:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Detect gesture
            result = detector.detect_gesture(frame)

            # Draw landmarks
            frame = detector.draw_landmarks(frame, result)

            # Display gesture and action
            if result["gesture"] != "none":
                action = get_action_for_gesture(result["gesture"])
                cv2.putText(
                    frame,
                    f"Action: {action}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )

            cv2.imshow("Gesture Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()