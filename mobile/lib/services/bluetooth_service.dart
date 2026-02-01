/**
 * Smart Glasses Mobile Gateway
 * Bluetooth LE service for ESP32 communication.
 */

import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import '../config.dart';

class BluetoothService with ChangeNotifier {
  bool _isConnected = false;
  Device? _connectedDevice;
  BluetoothCharacteristic? _characteristic;

  bool get isConnected => _isConnected;
  Device? get connectedDevice => _connectedDevice;

  Future<void> scanAndConnect(BuildContext context) async {
    // Start scanning
    print('Starting BLE scan...');

    // Listen for scan results
    FlutterBluePlus.scanResults.listen((results) {
      for (ScanResult result in results) {
        if (result.device.name == Config.targetDeviceName) {
          print('Found ${result.device.name}');
          _connectToDevice(result.device, context);
          FlutterBluePlus.stopScan();
          break;
        }
      }
    });

    // Start scan with timeout
    await FlutterBluePlus.startScan(timeout: const Duration(seconds: 10));
  }

  Future<void> _connectToDevice(BluetoothDevice device, BuildContext context) async {
    print('Connecting to ${device.name}...');

    // Set up connection listener
    device.connectionState.listen((state) {
      if (state == BluetoothConnectionState.connected) {
        _isConnected = true;
        _connectedDevice = Device(
          id: device.remoteId.str,
          name: device.name,
          device: device,
          connected: true,
        );
        notifyListeners();
        print('Connected to ${device.name}');
      } else if (state == BluetoothConnectionState.disconnected) {
        _isConnected = false;
        _connectedDevice = null;
        notifyListeners();
        print('Disconnected from ${device.name}');
      }
    });

    // Connect
    await device.connect();

    // Discover services
    List<BluetoothService> services = await device.discoverServices();

    // Find our service
    for (BluetoothService service in services) {
      if (service.uuid.toString() == Config.bleServiceUuid) {
        // Find characteristic
        for (BluetoothCharacteristic char in service.characteristics) {
          if (char.uuid.toString() == Config.bleCharacteristicUuid) {
            _characteristic = char;
            await char.setNotifyValue(true);
            break;
          }
        }
        break;
      }
    }
  }

  Future<void> disconnect() async {
    if (_connectedDevice != null) {
      await _connectedDevice!.device.disconnect();
      _isConnected = false;
      _connectedDevice = null;
      _characteristic = null;
      notifyListeners();
    }
  }

  Future<void> sendCommand(String command) async {
    if (_characteristic != null) {
      await _characteristic!.write(command.codeUnits);
      print('Sent command: $command');
    } else {
      print('Not connected - cannot send command');
    }
  }

  Stream<List<int>> get notifications {
    if (_characteristic != null) {
      return _characteristic!.onValueReceivedStream;
    }
    return const Stream.empty();
  }
}