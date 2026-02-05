/**
 * Smart Glasses Mobile Gateway
 * Home screen with connection status, quick actions, and navigation.
 */

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:async';
import 'dart:convert';

import '../main.dart';
import '../config.dart';
import 'settings_screen.dart';
import '../services/bluetooth_service.dart';
import '../services/gateway_service.dart';
import '../services/notification_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final List<Widget> _screens = [
    const ConnectionScreen(),
    const NavigationScreen(),
    const VoiceScreen(),
    const ContextScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Glasses'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.bluetooth),
            label: 'Connect',
          ),
          NavigationDestination(
            icon: Icon(Icons.navigation),
            label: 'Navigate',
          ),
          NavigationDestination(
            icon: Icon(Icons.mic),
            label: 'Voice',
          ),
          NavigationDestination(
            icon: Icon(Icons.lightbulb),
            label: 'Context',
          ),
        ],
      ),
    );
  }
}

// ==================== CONNECTION SCREEN ====================

class ConnectionScreen extends StatelessWidget {
  const ConnectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    var bluetoothService = Provider.of<BluetoothService>(context);
    var gatewayService = Provider.of<GatewayService>(context);

    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // Connection Status Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  Row(
                    children: [
                      Icon(
                        bluetoothService.isConnected
                            ? Icons.bluetooth_connected
                            : Icons.bluetooth_disabled,
                        size: 32,
                        color: bluetoothService.isConnected
                            ? Colors.green
                            : Colors.red,
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              bluetoothService.isConnected
                                  ? 'Glasses Connected'
                                  : 'Disconnected',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            if (bluetoothService.connectedDevice != null)
                              Text(
                                bluetoothService.connectedDevice!.name,
                                style: Theme.of(context).textTheme.bodyMedium,
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: bluetoothService.isConnected
                              ? () => bluetoothService.disconnect()
                              : () => bluetoothService.scanAndConnect(context),
                          icon: Icon(bluetoothService.isConnected
                              ? Icons.link_off
                              : Icons.link),
                          label: Text(bluetoothService.isConnected
                              ? 'Disconnect'
                              : 'Connect'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Quick Actions
          Text(
            'Quick Actions',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _QuickActionButton(
                icon: Icons.camera_alt,
                label: 'Capture',
                onTap: () async {
                  // Send capture command to glasses
                  if (bluetoothService.isConnected) {
                    await bluetoothService.sendCommand('CAPTURE');
                  }
                },
              ),
              _QuickActionButton(
                icon: Icons.mic,
                label: 'Listen',
                onTap: () async {
                  if (bluetoothService.isConnected) {
                    await bluetoothService.sendCommand('LISTEN');
                  }
                },
              ),
              _QuickActionButton(
                icon: Icons.vibration,
                label: 'Haptic',
                onTap: () async {
                  if (bluetoothService.isConnected) {
                    await bluetoothService.sendCommand('HAPTIC_SHORT');
                  }
                },
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Server Status
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  Icon(
                    Icons.cloud,
                    color: gatewayService.isConnected ? Colors.green : Colors.red,
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Server: ${gatewayService.isConnected ? 'Online' : 'Offline'}',
                        ),
                        Text(
                          Config.serverUrl,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () => gatewayService.testConnection(),
                    child: const Text('Test'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onTap,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: Column(
        children: [
          Icon(icon, size: 28),
          const SizedBox(height: 8),
          Text(label),
        ],
      ),
    );
  }
}

// ==================== NAVIGATION SCREEN ====================

class NavigationScreen extends StatefulWidget {
  const NavigationScreen({super.key});

  @override
  State<NavigationScreen> createState() => _NavigationScreenState();
}

class _NavigationScreenState extends State<NavigationScreen> {
  String? _startLocation;
  String? _destination;
  List<String> _locations = [];
  bool _isNavigating = false;
  Map<String, dynamic>? _navigationResult;

  @override
  void initState() {
    super.initState();
    _loadLocations();
  }

  Future<void> _loadLocations() async {
    try {
      final response = await ApiClient().get('/v2/navigation/locations');
      setState(() {
        _locations = List<String>.from(response['locations'] ?? []);
      });
    } catch (e) {
      print('Failed to load locations: $e');
    }
  }

  Future<void> _startNavigation() async {
    if (_startLocation == null || _destination == null) return;

    try {
      final response = await ApiClient().post('/v2/navigation/start', {
        'current_location': _startLocation,
        'destination': _destination,
      });

      setState(() {
        _navigationResult = response;
        _isNavigating = true;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Navigation failed: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // Location Selectors
          DropdownButtonFormField<String>(
            value: _startLocation,
            decoration: const InputDecoration(
              labelText: 'From',
              prefixIcon: Icon(Icons.location_on),
            ),
            items: _locations.map((loc) {
              return DropdownMenuItem(value: loc, child: Text(loc));
            }).toList(),
            onChanged: (val) => setState(() => _startLocation = val),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _destination,
            decoration: const InputDecoration(
              labelText: 'To',
              prefixIcon: Icon(Icons.flag),
            ),
            items: _locations.map((loc) {
              return DropdownMenuItem(value: loc, child: Text(loc));
            }).toList(),
            onChanged: (val) => setState(() => _destination = val),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _startLocation != null && _destination != null
                ? _startNavigation
                : null,
            icon: const Icon(Icons.navigation),
            label: const Text('Start Navigation'),
          ),
          const SizedBox(height: 16),
          // Navigation Steps
          if (_navigationResult != null)
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: ListView(
                    children: [
                      Text(
                        'Route to $_destination',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _navigationResult!['distance'] ?? '',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      const Divider(),
                      if (_navigationResult!['steps'] != null)
                        ...(_navigationResult!['steps'] as List).map((step) {
                          return ListTile(
                            leading: CircleAvatar(
                              child: Text('${step['step_number']}'),
                            ),
                            title: Text(step['instruction']),
                            subtitle: Text(step['distance'] ?? ''),
                          );
                        }).toList(),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ==================== VOICE SCREEN ====================

class VoiceScreen extends StatefulWidget {
  const VoiceScreen({super.key});

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends State<VoiceScreen> {
  bool _isListening = false;
  String _transcribed = '';
  String _response = '';
  String _error = '';
  bool _speechAvailable = false;

  @override
  void initState() {
    super.initState();
    _initSpeech();
  }

  Future<void> _initSpeech() async {
    try {
      // Check if speech recognition is available
      // Note: This is a simplified implementation
      // For production, use the speech_to_text package
      setState(() {
        _speechAvailable = true; // Assume available, actual check would use package
      });
    } catch (e) {
      setState(() {
        _speechAvailable = false;
        _error = 'Speech recognition not available';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          // Error message
          if (_error.isNotEmpty)
            Card(
              color: Colors.red[100],
              child: Padding(
                padding: const EdgeInsets.all(8.0),
                child: Row(
                  children: [
                    Icon(Icons.error, color: Colors.red[700]),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_error)),
                  ],
                ),
              ),
            ),
          // Voice Input
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                children: [
                  Icon(
                    _isListening ? Icons.mic : Icons.mic_none,
                    size: 64,
                    color: _isListening ? Colors.red : Colors.blue,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _isListening ? 'Listening...' : 'Tap to speak',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _isListening ? null : (_speechAvailable ? _startListening : null),
                    icon: Icon(_isListening ? Icons.stop : Icons.mic),
                    label: Text(_isListening ? 'Stop' : 'Speak'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: _isListening ? Colors.red : Colors.blue,
                    ),
                  ),
                  const SizedBox(height: 8),
                  // Fallback to manual input
                  TextButton.icon(
                    onPressed: _isListening ? null : _showManualInput,
                    icon: const Icon(Icons.keyboard),
                    label: const Text('Type instead'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Transcribed Text
          if (_transcribed.isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'You said:',
                      style: Theme.of(context).textTheme.labelMedium,
                    ),
                    Text(_transcribed),
                  ],
                ),
              ),
            ),
          // Response
          if (_response.isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Nova says:',
                      style: Theme.of(context).textTheme.labelMedium,
                    ),
                    Text(_response),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  void _startListening() async {
    setState(() {
      _isListening = true;
      _error = '';
    });

    // For now, show manual input as a fallback
    // In production, implement actual speech-to-text using speech_to_text package
    // Example implementation:
    //
    // import 'package:speech_to_text/speech_to_text.dart';
    // SpeechToText speech = SpeechToText();
    // await speech.initialize();
    // await speech.listen(onResult: (result) {
    //   setState(() {
    //     _transcribed = result.recognizedWords;
    //     _isListening = false;
    //   });
    //   if (_transcribed.isNotEmpty) {
    //     _processCommand(_transcribed);
    //   }
    // });

    // Simulate listening delay then show manual input
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) {
      _showManualInput();
    }
  }

  void _showManualInput() {
    setState(() => _isListening = false);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Enter Command'),
        content: TextField(
          onSubmitted: (text) {
            setState(() {
              _transcribed = text;
              _isListening = false;
            });
            _processCommand(text);
            Navigator.pop(context);
          },
          decoration: const InputDecoration(
            hintText: 'What do you want to ask?',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() => _isListening = false);
              Navigator.pop(context);
            },
            child: const Text('Cancel'),
          ),
        ],
      ),
    );
  }

  Future<void> _processCommand(String command) async {
    try {
      final response = await ApiClient().post('/v2/voice/process', {
        'command': command,
        'wake_word': Config.wakeWord,
      });

      setState(() {
        _response = response['text'] ?? 'I didn\'t understand that.';
      });
    } catch (e) {
      setState(() {
        _response = 'Error: Could not connect to server. Make sure the server is running on ${Config.serverUrl}';
      });
    }
  }
}

// ==================== CONTEXT SCREEN ====================

class ContextScreen extends StatefulWidget {
  const ContextScreen({super.key});

  @override
  State<ContextScreen> createState() => _ContextScreenState();
}

class _ContextScreenState extends State<ContextScreen> {
  List<ContextSuggestion> _suggestions = [];

  @override
  void initState() {
    super.initState();
    _loadSuggestions();
  }

  Future<void> _loadSuggestions() async {
    try {
      final response = await ApiClient().get('/v2/context/suggest');
      setState(() {
        _suggestions = (response['suggestions'] as List)
            .map((s) => ContextSuggestion.fromJson(s))
            .toList();
      });
    } catch (e) {
      print('Failed to load suggestions: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Smart Suggestions',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: _loadSuggestions,
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (_suggestions.isEmpty)
            const Center(
              child: Padding(
                padding: EdgeInsets.all(32.0),
                child: Text('No suggestions yet'),
              ),
            )
          else
            ..._suggestions.map((suggestion) {
              Color urgencyColor;
              switch (suggestion.urgency) {
                case 'high':
                  urgencyColor = Colors.orange;
                  break;
                case 'critical':
                  urgencyColor = Colors.red;
                  break;
                default:
                  urgencyColor = Colors.blue;
              }

              return Card(
                child: ListTile(
                  leading: Icon(
                    Icons.lightbulb,
                    color: urgencyColor,
                  ),
                  title: Text(suggestion.message),
                  subtitle: Text(suggestion.type),
                  trailing: IconButton(
                    icon: const Icon(Icons.dismiss),
                    onPressed: () {
                      setState(() {
                        _suggestions.remove(suggestion);
                      });
                    },
                  ),
                ),
              );
            }).toList(),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Context Awareness Features',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  _ContextFeatureTile(
                    icon: Icons.access_time,
                    title: 'Time-based Suggestions',
                    subtitle: 'Get reminders based on time of day',
                    enabled: true,
                  ),
                  _ContextFeatureTile(
                    icon: Icons.location_on,
                    title: 'Location Awareness',
                    subtitle: 'Suggestions based on where you are',
                    enabled: true,
                  ),
                  _ContextFeatureTile(
                    icon: Icons.directions_walk,
                    title: 'Activity Detection',
                    subtitle: 'Detect when you might need help',
                    enabled: false,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ContextFeatureTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final bool enabled;

  const _ContextFeatureTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.enabled,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle),
      trailing: Switch(
        value: enabled,
        onChanged: (val) {},
      ),
    );
  }
}