/**
 * Smart Glasses Mobile Gateway
 * Main entry point for the Flutter mobile app.
 *
 * License: MIT
 */

import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';

// Config
import 'config.dart';

// Screens
import 'screens/home_screen.dart';
import 'screens/settings_screen.dart';

// Services
import 'services/bluetooth_service.dart';
import 'services/gateway_service.dart';
import 'services/notification_service.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => BluetoothService()),
        ChangeNotifierProvider(create: (_) => GatewayService()),
        ChangeNotifierProvider(create: (_) => NotificationService()),
      ],
      child: const SmartGlassesApp(),
    ),
  );
}

class SmartGlassesApp extends StatelessWidget {
  const SmartGlassesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Glasses',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        darkTheme: ThemeData.dark(),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      routes: {
        '/settings': (_) => const SettingsScreen(),
      },
      debugShowCheckedModeBanner: false,
    );
  }
}

// ==================== DATA MODELS ====================

class Device {
  final String id;
  final String name;
  final BluetoothDevice device;
  bool connected;

  Device({
    required this.id,
    required this.name,
    required this.device,
    this.connected = false,
  });
}

class NavigationStep {
  final String instruction;
  final String? landmark;
  final int distance;
  final int duration;

  NavigationStep({
    required this.instruction,
    this.landmark,
    required this.distance,
    required this.duration,
  });

  factory NavigationStep.fromJson(Map<String, dynamic> json) {
    return NavigationStep(
      instruction: json['instruction'] ?? '',
      landmark: json['landmark'],
      distance: json['distance'] ?? 0,
      duration: json['duration'] ?? 0,
    );
  }
}

class ContextSuggestion {
  final String message;
  final String type;
  final String urgency;

  ContextSuggestion({
    required this.message,
    required this.type,
    required this.urgency,
  });

  factory ContextSuggestion.fromJson(Map<String, dynamic> json) {
    return ContextSuggestion(
      message: json['message'] ?? '',
      type: json['type'] ?? 'general',
      urgency: json['urgency'] ?? 'normal',
    );
  }
}

// ==================== API CLIENT ====================

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  ApiClient._internal();

  final String baseUrl = Config.serverUrl;
  Duration timeout = const Duration(seconds: 10);

  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl$endpoint'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    ).timeout(timeout);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('API error: ${response.statusCode}');
    }
  }

  Future<Map<String, dynamic>> get(String endpoint) async {
    final response = await http.get(
      Uri.parse('$baseUrl$endpoint'),
    ).timeout(timeout);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('API error: ${response.statusCode}');
    }
  }
}

// ==================== UTILITY FUNCTIONS ====================

String formatDistance(int meters) {
  if (meters < 1000) {
    return '${meters}m';
  }
  return '${(meters / 1000).toStringAsFixed(1)}km';
}

String formatDuration(int seconds) {
  if (seconds < 60) {
    return '${seconds}s';
  }
  int minutes = seconds ~/ 60;
  int remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return '${minutes}m ${remainingSeconds}s';
  }
  int hours = minutes ~/ 60;
  remainingMinutes = minutes % 60;
  return '${hours}h ${remainingMinutes}m';
}

// ==================== EXAMPLE USAGE ====================

/*
// Send voice command
final response = await ApiClient().post('/v2/voice/process', {
  'command': 'navigate to cafeteria',
  'wake_word': 'Nova',
});

// Process image
final imageResponse = await ApiClient().post('/v2/vision/detect', {
  'image': base64Image,
  'width': 320,
  'height': 240,
});

// Get navigation
final navResponse = await ApiClient().post('/v2/navigation/start', {
  'current_location': 'lobby',
  'destination': 'cafeteria',
});

// Get context suggestions
final suggestions = await ApiClient().get('/v2/context/suggest');
*/