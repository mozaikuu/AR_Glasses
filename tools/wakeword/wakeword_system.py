#!/usr/bin/env python3
"""
Wake Word System for Smart Glasses AI Assistant

Implements a complete wake-word activation system with state management
for hands-free interaction with the AI assistant.
"""

import os
import sys
import time
import threading
import queue
import enum
from pathlib import Path
import speech_recognition as sr
import pygame
import numpy as np

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

class SystemState(enum.Enum):
    """System states for wake-word activation"""
    IDLE = "idle"          # Listening for wake words only
    ACTIVE = "active"      # Processing command after wake word detection
    PROCESSING = "processing"  # Processing AI response

class WakeWordSystem:
    """
    Complete wake-word activation system with state management

    This system continuously listens for wake words ("Nova", "Hey Nova") in IDLE state,
    then transitions to ACTIVE state for command processing.
    """

    def __init__(self, wake_words=None, sensitivity=0.5):
        """
        Initialize wake word system

        Args:
            wake_words (list): List of wake words to detect
            sensitivity (float): Detection sensitivity (0.0-1.0)
        """
        if wake_words is None:
            wake_words = ["nova", "hey nova"]

        self.wake_words = [word.lower() for word in wake_words]
        self.sensitivity = sensitivity

        # State management
        self.state = SystemState.IDLE
        self.state_lock = threading.Lock()

        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Audio playback for acknowledgment
        pygame.mixer.init()
        self.acknowledgment_sound = None
        self._load_acknowledgment_sound()

        # Callbacks
        self.on_wake_word_detected = None
        self.on_command_received = None
        self.on_state_changed = None

        # Threading
        self.listen_thread = None
        self.is_running = False

        # Audio calibration
        self._calibrate_microphone()

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        print("Calibrating microphone...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone calibrated")
        except Exception as e:
            print(f"Warning: Microphone calibration failed: {e}")

    def _load_acknowledgment_sound(self):
        """Load acknowledgment sound effect"""
        try:
            # Create a simple beep sound
            sample_rate = 44100
            duration = 0.2  # 200ms
            frequency = 800  # Hz

            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            beep = np.sin(frequency * 2 * np.pi * t)

            # Convert to 16-bit PCM
            beep = (beep * 32767).astype(np.int16)

            # Create pygame sound (convert numpy array to bytes)
            beep_bytes = beep.tobytes()
            self.acknowledgment_sound = pygame.mixer.Sound(beep_bytes)

        except Exception as e:
            print(f"Warning: Failed to create acknowledgment sound: {e}")
            self.acknowledgment_sound = None

    def set_callbacks(self, wake_word_callback=None, command_callback=None, state_callback=None):
        """
        Set callback functions

        Args:
            wake_word_callback: Called when wake word is detected (wake_word, confidence, text)
            command_callback: Called when command is received (command_text)
            state_callback: Called when system state changes (old_state, new_state)
        """
        self.on_wake_word_detected = wake_word_callback
        self.on_command_received = command_callback
        self.on_state_changed = state_callback

    def _change_state(self, new_state):
        """Change system state and notify callback"""
        with self.state_lock:
            old_state = self.state
            self.state = new_state

            if self.on_state_changed and old_state != new_state:
                self.on_state_changed(old_state, new_state)

    def _play_acknowledgment(self):
        """Play acknowledgment sound"""
        if self.acknowledgment_sound:
            try:
                self.acknowledgment_sound.play()
            except Exception as e:
                print(f"Warning: Failed to play acknowledgment sound: {e}")
        else:
            # Fallback: simple print acknowledgment
            print("(Acknowledgment sound)")

    def _calculate_confidence(self, recognized_text, wake_word):
        """
        Calculate confidence score for wake word detection

        Args:
            recognized_text (str): Full recognized text
            wake_word (str): The wake word that was detected

        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        recognized_text = recognized_text.lower().strip()

        # Exact match gets highest confidence
        if recognized_text == wake_word:
            return 1.0

        # Starts with wake word (good indication)
        if recognized_text.startswith(wake_word):
            return 0.9

        # Contains wake word
        if wake_word in recognized_text:
            return 0.7

        return 0.0

    def _listen_for_wake_words(self):
        """Continuous wake word detection loop (IDLE state)"""
        print("Wake word detection active. Say 'Nova' or 'Hey Nova' to activate.")

        while self.is_running and self.state == SystemState.IDLE:
            try:
                with self.microphone as source:
                    # Listen for short audio chunks with timeout
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=2)

                try:
                    # Use Google Speech Recognition
                    text = self.recognizer.recognize_google(audio).lower().strip()

                    # Check for wake words
                    for wake_word in self.wake_words:
                        if wake_word in text:
                            confidence = self._calculate_confidence(text, wake_word)

                            if confidence >= self.sensitivity:
                                print(f"Wake word detected: '{wake_word}' (confidence: {confidence:.2f})")

                                # Notify callback
                                if self.on_wake_word_detected:
                                    self.on_wake_word_detected(wake_word, confidence, text)

                                # Transition to ACTIVE state
                                self._change_state(SystemState.ACTIVE)

                                # Play acknowledgment
                                self._play_acknowledgment()

                                # Start command listening
                                self._listen_for_command()
                                break

                except sr.UnknownValueError:
                    # No speech detected, continue
                    pass
                except sr.RequestError as e:
                    print(f"⚠️ Speech recognition error: {e}")
                    time.sleep(1)

            except sr.WaitTimeoutError:
                # Timeout, continue listening
                continue
            except Exception as e:
                print(f"⚠️ Wake word listening error: {e}")
                time.sleep(0.5)

    def _listen_for_command(self):
        """Listen for command after wake word detection (ACTIVE state)"""
        print("🎤 Listening for command...")

        try:
            with self.microphone as source:
                # Listen for longer phrase (command)
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)

            try:
                # Recognize the command
                command_text = self.recognizer.recognize_google(audio).strip()

                # Check if command is empty or just whitespace
                if not command_text:
                    print("⚠️ Empty command received, returning to idle")
                    self._change_state(SystemState.IDLE)
                    return

                print(f"📝 Command received: '{command_text}'")

                # Transition to PROCESSING state
                self._change_state(SystemState.PROCESSING)

                # Notify callback
                if self.on_command_received:
                    self.on_command_received(command_text)

            except sr.UnknownValueError:
                print("⚠️ No command detected, returning to idle")
                self._change_state(SystemState.IDLE)
            except sr.RequestError as e:
                print(f"⚠️ Command recognition error: {e}")
                self._change_state(SystemState.IDLE)

        except sr.WaitTimeoutError:
            print("⏰ Command timeout, returning to idle")
            self._change_state(SystemState.IDLE)
        except Exception as e:
            print(f"⚠️ Command listening error: {e}")
            self._change_state(SystemState.IDLE)

    def start(self):
        """Start the wake word system"""
        if self.is_running:
            return

        self.is_running = True
        self._change_state(SystemState.IDLE)

        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_for_wake_words, daemon=True)
        self.listen_thread.start()

        print("Wake word system started")

    def stop(self):
        """Stop the wake word system"""
        self.is_running = False
        self._change_state(SystemState.IDLE)

        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=2)

        pygame.mixer.quit()
        print("Wake word system stopped")

    def return_to_idle(self):
        """Return system to IDLE state (called after command processing)"""
        self._change_state(SystemState.IDLE)
        print("🔄 Returned to idle listening state")

    def get_state(self):
        """Get current system state"""
        with self.state_lock:
            return self.state

    def is_idle(self):
        """Check if system is in IDLE state"""
        return self.get_state() == SystemState.IDLE

    def is_active(self):
        """Check if system is in ACTIVE state"""
        return self.get_state() == SystemState.ACTIVE

    def is_processing(self):
        """Check if system is in PROCESSING state"""
        return self.get_state() == SystemState.PROCESSING


def create_wakeword_system(wake_words=None, sensitivity=0.5):
    """Factory function to create configured wake word system

    Args:
        wake_words: List of wake words (default: ["nova", "hey nova"])
        sensitivity: Detection sensitivity (0.0-1.0, default: 0.5)
    """
    if wake_words is None:
        wake_words = ["nova", "hey nova"]

    system = WakeWordSystem(
        wake_words=wake_words,
        sensitivity=sensitivity
    )
    return system