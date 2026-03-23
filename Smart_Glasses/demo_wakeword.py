#!/usr/bin/env python3
"""
Wake-Word Activation Demo for Smart Glasses AI Assistant

This demo showcases the complete wake-word activation system with:
- Continuous wake-word detection ("Nova", "Hey Nova")
- State management (IDLE → ACTIVE → PROCESSING → IDLE)
- Audio acknowledgment
- Command processing simulation
- Real-time status updates
"""

import time
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from tools.wakeword.wakeword_system import create_wakeword_system, SystemState

def demo_wakeword_system():
    """Complete wake-word system demonstration"""
    print("=" * 60)
    print("🎯 SMART GLASSES AI ASSISTANT - WAKE-WORD DEMO")
    print("=" * 60)
    print()

    # Create wake-word system
    print("Initializing wake-word system...")
    system = create_wakeword_system(sensitivity=0.4)  # Slightly lower sensitivity for demo

    # Demo statistics
    wake_words_detected = 0
    commands_processed = 0

    def on_wake_word_detected(wake_word, confidence, text):
        nonlocal wake_words_detected
        wake_words_detected += 1

        print(f"\n🔔 WAKE WORD DETECTED #{wake_words_detected}")
        print(f"   Word: '{wake_word}'")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Full Text: '{text}'")
        print(f"   State: {system.get_state()} → ACTIVE")
        print("   (Acknowledgment beep would play here)"
    def on_command_received(command_text):
        nonlocal commands_processed
        commands_processed += 1

        print(f"\n📝 COMMAND RECEIVED #{commands_processed}")
        print(f"   Command: '{command_text}'")
        print(f"   State: ACTIVE → PROCESSING")

        # Simulate AI processing
        print("   🤖 Processing command with AI...")
        time.sleep(2)  # Simulate AI response time

        # Mock AI response based on command
        if "time" in command_text.lower():
            response = "The current time is 2:30 PM"
        elif "weather" in command_text.lower():
            response = "It's sunny with a temperature of 72°F"
        elif "remind" in command_text.lower():
            response = "I'll remind you about that meeting at 3 PM"
        else:
            response = f"I understood: '{command_text}'. How can I help you further?"

        print(f"   🤖 AI Response: {response}")
        print(f"   State: PROCESSING → IDLE")
        print("   Ready for next wake word...")

        # Return to idle (this would be called by the real app after processing)
        system.return_to_idle()

    def on_state_changed(old_state, new_state):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] System state: {old_state} → {new_state}")

    # Set up callbacks
    system.set_callbacks(
        wake_word_callback=on_wake_word_detected,
        command_callback=on_command_received,
        state_callback=on_state_changed
    )

    print("\n🚀 STARTING WAKE-WORD SYSTEM")
    print("System is now in IDLE state, listening for wake words...")
    print()
    print("INSTRUCTIONS:")
    print("- Say 'Nova' or 'Hey Nova' to activate")
    print("- Then speak a command (e.g., 'What time is it?', 'What's the weather?')")
    print("- The system will process your command and return to listening")
    print("- Press Ctrl+C to stop the demo")
    print()
    print("-" * 60)

    try:
        # Start the system
        system.start()

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\n{'='*60}")
        print("DEMO COMPLETED")
        print(f"{'='*60}")
        print(f"Wake words detected: {wake_words_detected}")
        print(f"Commands processed: {commands_processed}")
        print("Thank you for trying the Smart Glasses AI Assistant!")

    finally:
        # Clean shutdown
        print("\nShutting down wake-word system...")
        system.stop()
        print("Demo ended.")

if __name__ == "__main__":
    demo_wakeword_system()