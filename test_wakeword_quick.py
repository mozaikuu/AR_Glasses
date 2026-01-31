#!/usr/bin/env python3
"""
Quick test for wake-word system integration
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from tools.wakeword.wakeword_system import create_wakeword_system

def test_wakeword_callbacks():
    """Test wake-word system with callback simulation"""
    print("Testing wake-word system callbacks...")

    # Create system
    system = create_wakeword_system()

    # Set up test callbacks
    wake_word_detected = False
    command_received = False

    def on_wake_word(wake_word, confidence, text):
        nonlocal wake_word_detected
        wake_word_detected = True
        print(f"Wake word detected: {wake_word} (confidence: {confidence:.2f})")
        print(f"Full text: '{text}'")

    def on_command(command_text):
        nonlocal command_received
        command_received = True
        print(f"Command received: '{command_text}'")

        # Simulate processing completion
        time.sleep(1)  # Simulate AI processing
        system.return_to_idle()
        print("Returned to idle state")

    def on_state_change(old_state, new_state):
        print(f"State changed: {old_state} -> {new_state}")

    system.set_callbacks(
        wake_word_callback=on_wake_word,
        command_callback=on_command,
        state_callback=on_state_change
    )

    print("System initialized. Say 'Nova' or 'Hey Nova' to test...")
    print("(This will run for 30 seconds for testing)")

    # Start system
    system.start()

    # Run for 30 seconds
    start_time = time.time()
    try:
        while time.time() - start_time < 30:
            time.sleep(1)
            if wake_word_detected and command_received:
                print("Test completed successfully!")
                break
    except KeyboardInterrupt:
        print("\nTest interrupted")

    # Stop system
    system.stop()
    print("Test completed")

if __name__ == "__main__":
    test_wakeword_callbacks()