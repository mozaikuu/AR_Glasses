/**
 * Smart Glasses Mobile Gateway
 * Configuration settings.
 *
 * Edit this file to configure your server and BLE settings.
 */

class Config {
  // Server configuration
  // IMPORTANT: Replace YOUR_PC_IP with your computer's IP address
  // You can find this by running `ipconfig` on Windows or `ifconfig` on Mac/Linux
  // The server must be running on your PC for the app to work
  static const String serverUrl = 'http://YOUR_PC_IP:8001';

  // For testing on PC (use localhost)
  static const String localServerUrl = 'http://localhost:8001';

  // To auto-detect server IP, set this to true
  // The app will try to detect the server automatically
  static const bool autoDetectServer = true;

  // List of possible server IPs to try (in order of likelihood)
  static const List<String> possibleServerIPs = [
    '192.168.1.100',  // Common PC IP
    '192.168.1.101',  // Alternative
    '192.168.1.102',
    '10.0.0.1',
    '10.0.0.100',
  ];

  // BLE UUIDs (must match ESP32 firmware)
  static const String bleServiceUuid = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
  static const String bleCharacteristicUuid = 'beb5483e-36e1-4688-b7f5-ea07361b26a8';

  // Device name to scan for
  static const String targetDeviceName = 'Smart Glasses Nova';

  // Navigation settings
  static const double navigationUpdateInterval = 3.0; // seconds

  // Camera settings
  static const int cameraWidth = 320;
  static const int cameraHeight = 240;
  static const int cameraQuality = 15; // 0-100, lower is better quality

  // Audio settings
  static const int audioSampleRate = 16000;
  static const int audioDuration = 2000; // milliseconds

  // Context awareness
  static const int contextUpdateInterval = 5; // seconds
  static const int suggestionCooldown = 30; // seconds

  // Feature flags
  static const bool enableVoiceInput = true;
  static const bool enableGestureControl = true;
  static const bool enableHapticFeedback = true;
  static const bool enableProactiveSuggestions = true;

  // Wake word
  static const String wakeWord = 'Nova';
}