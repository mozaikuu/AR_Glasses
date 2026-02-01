/**
 * Smart Glasses Mobile Gateway
 * Settings screen for configuration.
 */

import 'package:flutter/material.dart';
import '../config.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Server Configuration
          const Text(
            'Server',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Card(
            child: Column(
              children: [
                ListTile(
                  title: const Text('Server URL'),
                  subtitle: Text(Config.serverUrl),
                  leading: const Icon(Icons.cloud),
                  onTap: () => _editServerUrl(context),
                ),
                const Divider(),
                ListTile(
                  title: const Text('Local Server URL'),
                  subtitle: Text(Config.localServerUrl),
                  leading: const Icon(Icons.home),
                  onTap: () {},
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // BLE Configuration
          const Text(
            'Bluetooth',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Card(
            child: Column(
              children: [
                ListTile(
                  title: const Text('Device Name'),
                  subtitle: Text(Config.targetDeviceName),
                  leading: const Icon(Icons.devices),
                ),
                const Divider(),
                ListTile(
                  title: const Text('Service UUID'),
                  subtitle: Text(Config.bleServiceUuid),
                  leading: const Icon(Icons.tag),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Feature Flags
          const Text(
            'Features',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: const Text('Voice Input'),
                  subtitle: const Text('Enable voice commands'),
                  value: Config.enableVoiceInput,
                  onChanged: (val) {},
                ),
                const Divider(),
                SwitchListTile(
                  title: const Text('Gesture Control'),
                  subtitle: const Text('Enable hand gestures'),
                  value: Config.enableGestureControl,
                  onChanged: (val) {},
                ),
                const Divider(),
                SwitchListTile(
                  title: const Text('Haptic Feedback'),
                  subtitle: const Text('Vibration feedback'),
                  value: Config.enableHapticFeedback,
                  onChanged: (val) {},
                ),
                const Divider(),
                SwitchListTile(
                  title: const Text('Proactive Suggestions'),
                  subtitle: const Text('Context-aware hints'),
                  value: Config.enableProactiveSuggestions,
                  onChanged: (val) {},
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // About
          const Text(
            'About',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Card(
            child: Column(
              children: [
                ListTile(
                  title: const Text('Version'),
                  subtitle: const Text('2.0.0'),
                  leading: const Icon(Icons.info),
                ),
                const Divider(),
                ListTile(
                  title: const Text('License'),
                  subtitle: const Text('MIT'),
                  onTap: () {},
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _editServerUrl(BuildContext context) {
    // Would show a dialog to edit the server URL
  }
}