/**
 * Smart Glasses Mobile Gateway
 * Configuration settings.
 *
 * Edit this file to configure your server and BLE settings.
 */

class Config {
  // Server configuration
  // Change this to your server's IP address
  static const String serverUrl = 'http://192.168.1.X:8001';

  // For local development
  static const String localServerUrl = 'http://localhost:8001';

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