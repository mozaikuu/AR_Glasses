/**
 * Smart Glasses Mobile Gateway
 * Server API communication service.
 */

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';

class GatewayService with ChangeNotifier {
  bool _isConnected = false;
  String _serverUrl = Config.serverUrl;

  bool get isConnected => _isConnected;
  String get serverUrl => _serverUrl;

  Future<void> testConnection() async {
    try {
      final response = await http.get(Uri.parse('$_serverUrl/'));
      if (response.statusCode == 200) {
        _isConnected = true;
        notifyListeners();
        print('Server connection successful');
      } else {
        _isConnected = false;
        notifyListeners();
        print('Server returned status: ${response.statusCode}');
      }
    } catch (e) {
      _isConnected = false;
      notifyListeners();
      print('Server connection failed: $e');
    }
  }

  Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$_serverUrl$endpoint'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('API error: ${response.statusCode}');
    }
  }

  Future<Map<String, dynamic>> get(String endpoint) async {
    final response = await http.get(Uri.parse('$_serverUrl$endpoint'));

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('API error: ${response.statusCode}');
    }
  }

  void setServerUrl(String url) {
    _serverUrl = url;
    notifyListeners();
  }
}