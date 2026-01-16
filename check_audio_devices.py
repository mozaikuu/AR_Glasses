#!/usr/bin/env python3
"""Check available audio devices."""

import pyaudio

p = pyaudio.PyAudio()
print('Available audio devices:')
for i in range(p.get_device_count()):
    try:
        device_info = p.get_device_info_by_index(i)
        print(f'Device {i}: {device_info.get("name")} (inputs: {device_info.get("maxInputChannels")})')
    except Exception as e:
        print(f'Error getting device {i} info: {e}')
p.terminate()
