#!/usr/bin/env python3
"""
Wake Word Detection System for Smart Glasses AI Assistant

This script implements wake word detection using keyword spotting
with speech recognition for "Nova" and "Hey Nova" wake words.
"""

import os
import sys
import time
import threading
import queue
import numpy as np
from pathlib import Path
import speech_recognition as sr
import pyaudio

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

class WakeWordDetector:
    """Wake word detection using speech recognition keyword spotting"""

    def __init__(self, wake_words=None, sensitivity=0.5):
        """
        Initialize wake word detector

        Args:
            wake_words (list): List of wake words to detect (default: ["nova", "hey nova"])
            sensitivity (float): Detection sensitivity (0.0-1.0)
        """
        if wake_words is None:
            wake_words = ["nova", "hey nova"]

        self.wake_words = [word.lower() for word in wake_words]
        self.sensitivity = sensitivity
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.detection_callback = None

        # Configure microphone
        self.microphone = sr.Microphone()

        # Adjust for ambient noise
        print("Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone calibrated")

    def set_detection_callback(self, callback):
        """Set callback function to call when wake word is detected"""
        self.detection_callback = callback

    def start_listening(self):
        """Start continuous wake word detection"""
        self.is_listening = True
        print("Wake word detection started. Say 'Nova' or 'Hey Nova' to activate.")

        while self.is_listening:
            try:
                with self.microphone as source:
                    # Listen for short audio chunks
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)

                try:
                    # Use Google Speech Recognition for keyword spotting
                    text = self.recognizer.recognize_google(audio).lower().strip()

                    # Check if any wake word is detected
                    for wake_word in self.wake_words:
                        if wake_word in text:
                            confidence = self._calculate_confidence(text, wake_word)
                            if confidence >= self.sensitivity:
                                print(f"Wake word detected: '{wake_word}' (confidence: {confidence:.2f})")
                                if self.detection_callback:
                                    self.detection_callback(wake_word, confidence, text)
                                break

                except sr.UnknownValueError:
                    # No speech detected, continue listening
                    pass
                except sr.RequestError as e:
                    print(f"Speech recognition error: {e}")
                    time.sleep(1)  # Wait before retrying

            except sr.WaitTimeoutError:
                # Timeout, continue listening
                continue
            except KeyboardInterrupt:
                break

        print("Wake word detection stopped")

    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False

    def _calculate_confidence(self, recognized_text, wake_word):
        """
        Calculate confidence score for wake word detection

        Args:
            recognized_text (str): Full recognized text
            wake_word (str): The wake word that was detected

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        # Simple confidence calculation based on text matching
        if recognized_text == wake_word:
            return 1.0
        elif recognized_text.startswith(wake_word):
            return 0.9
        elif wake_word in recognized_text:
            return 0.7
        else:
            return 0.0

def test_wake_word_detection():
    """Test wake word detection functionality"""
    print("Testing wake word detection...")

    def on_wake_word_detected(wake_word, confidence, full_text):
        print(f"Wake word '{wake_word}' detected with confidence {confidence:.2f}")
        print(f"   Full text: '{full_text}'")

    detector = WakeWordDetector(sensitivity=0.3)  # Lower sensitivity for testing
    detector.set_detection_callback(on_wake_word_detected)

    try:
        print("Say 'Nova' or 'Hey Nova' to test detection (Ctrl+C to stop)")
        detector.start_listening()
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    finally:
        detector.stop_listening()

if __name__ == "__main__":
    print("Smart Glasses Wake Word Detection System")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_wake_word_detection()
    else:
        print("Usage:")
        print("  python train_wakeword.py test  # Test wake word detection")
        print("\nThis script provides wake word detection using speech recognition.")
        print("For production use, integrate with the main application.")