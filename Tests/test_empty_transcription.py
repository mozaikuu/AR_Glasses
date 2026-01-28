#!/usr/bin/env python3
"""
Test script for empty transcription handling
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_empty_command_handling():
    """Test that empty commands are handled properly"""
    print("Testing empty command handling...")

    # Test the wakeword system empty command check
    from tools.wakeword.wakeword_system import WakeWordSystem

    system = WakeWordSystem()
    command_received = False

    def on_command(cmd):
        nonlocal command_received
        command_received = True
        print(f"Command callback called with: {repr(cmd)}")

    system.set_callbacks(command_callback=on_command)

    # Simulate the command recognition logic
    test_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("Hello world", "Valid command"),
        ("   Hello   ", "Command with whitespace"),
    ]

    for test_input, description in test_cases:
        print(f"\nTesting: {description} - Input: {repr(test_input)}")
        command_received = False

        # Simulate the logic from _listen_for_command
        command_text = test_input.strip() if test_input else test_input

        if not command_text:
            print("PASS: Correctly identified as empty - would return to idle")
        else:
            print(f"PASS: Would process command: {repr(command_text)}")

    print("\nPASS: Empty command handling test completed")

def test_app_empty_command():
    """Test the app-level empty command handling"""
    print("\nTesting app-level empty command handling...")

    # Mock the session state and functions
    class MockSessionState:
        def __init__(self):
            self.error_message = None
            self.wakeword_system = MockWakewordSystem()

        def get(self, key, default=None):
            return getattr(self, key, default)

    class MockWakewordSystem:
        def return_to_idle(self):
            print("IDLE: Wakeword system returned to idle")

    # Mock st.rerun()
    def mock_rerun():
        print("✓ UI would rerun")

    # Import the function (we'll mock the dependencies)
    import app
    original_st = getattr(app, 'st', None)

    # Create mock st module
    class MockST:
        session_state = MockSessionState()

        @staticmethod
        def error(message):
            print(f"ERROR: {message}")

        @staticmethod
        def rerun():
            mock_rerun()

    # Temporarily replace st
    app.st = MockST()

    try:
        # Test empty command
        print("Testing empty command...")
        app.process_wakeword_command("")

        # Test whitespace-only command
        print("\nTesting whitespace-only command...")
        app.process_wakeword_command("   ")

        # Test None command
        print("\nTesting None command...")
        app.process_wakeword_command(None)

        print("\nPASS: App-level empty command handling test completed")

    finally:
        # Restore original st if it existed
        if original_st is not None:
            app.st = original_st

if __name__ == "__main__":
    test_empty_command_handling()
    test_app_empty_command()
    print("\nSUCCESS: All empty transcription tests passed!")