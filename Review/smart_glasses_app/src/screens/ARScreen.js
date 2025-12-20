import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { lightTheme, darkTheme } from '../constants/theme';

const { width, height } = Dimensions.get('window');

const ARScreen = () => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [arActive, setArActive] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);

  const handleStartAR = () => {
    Alert.alert(
      'AR Experience',
      'AR functionality would be implemented here using libraries like:\n\n- react-native-arkit (iOS)\n- react-native-arcore (Android)\n- expo-gl and expo-three\n\nThis would allow users to visualize and control devices in augmented reality.',
      [{ text: 'OK' }]
    );
    setArActive(true);
  };

  const handleStopAR = () => {
    setArActive(false);
    setSelectedDevice(null);
  };

  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
    Alert.alert(
      'Device Selected',
      `You selected ${device.name}. In a full AR implementation, this device would be placed in the AR space.`,
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {!arActive ? (
        <View style={styles.setupContainer}>
          <View style={styles.header}>
            <Ionicons name="cube" size={64} color={theme.primary} />
            <Text style={[styles.title, { color: theme.text }]}>
              Augmented Reality
            </Text>
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
              Visualize and control your smart glasses devices in AR
            </Text>
          </View>

          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Ionicons name="information-circle" size={24} color={theme.info} />
              <View style={styles.infoContent}>
                <Text style={[styles.infoTitle, { color: theme.text }]}>
                  AR Features
                </Text>
                <Text style={[styles.infoText, { color: theme.textSecondary }]}>
                  • Place devices in your real-world space{'\n'}
                  • Control devices with AR gestures{'\n'}
                  • Visualize device states in 3D{'\n'}
                  • Interactive device placement
                </Text>
              </View>
            </View>
          </View>

          {devices.length > 0 && (
            <View style={styles.devicesSection}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>
                Available Devices
              </Text>
              <View style={styles.devicesList}>
                {devices.slice(0, 3).map((device) => (
                  <TouchableOpacity
                    key={device.id}
                    style={[
                      styles.deviceButton,
                      {
                        backgroundColor: theme.card,
                        borderColor: theme.border,
                      },
                    ]}
                    onPress={() => handleDeviceSelect(device)}
                  >
                    <Ionicons
                      name="hardware-chip"
                      size={24}
                      color={theme.primary}
                    />
                    <Text style={[styles.deviceName, { color: theme.text }]}>
                      {device.name}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          <TouchableOpacity
            style={[styles.startButton, { backgroundColor: theme.primary }]}
            onPress={handleStartAR}
          >
            <Ionicons name="camera" size={24} color="#FFFFFF" />
            <Text style={styles.startButtonText}>Start AR Experience</Text>
          </TouchableOpacity>

          <View style={styles.noteCard}>
            <Ionicons name="warning" size={20} color={theme.warning} />
            <Text style={[styles.noteText, { color: theme.textSecondary }]}>
              AR functionality requires device camera and motion sensors. This
              is a placeholder implementation.
            </Text>
          </View>
        </View>
      ) : (
        <View style={styles.arViewContainer}>
          <View style={styles.arView}>
            <View style={styles.arPlaceholder}>
              <Ionicons name="cube-outline" size={80} color={theme.textSecondary} />
              <Text style={[styles.arPlaceholderText, { color: theme.textSecondary }]}>
                AR View
              </Text>
              <Text style={[styles.arPlaceholderSubtext, { color: theme.textSecondary }]}>
                Camera feed and AR overlay would appear here
              </Text>
            </View>

            {selectedDevice && (
              <View
                style={[
                  styles.arDeviceOverlay,
                  { backgroundColor: theme.card + 'E6' },
                ]}
              >
                <Text style={[styles.arDeviceName, { color: theme.text }]}>
                  {selectedDevice.name}
                </Text>
                <Text style={[styles.arDeviceState, { color: theme.primary }]}>
                  {selectedDevice.state}
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={[styles.stopButton, { backgroundColor: theme.error }]}
              onPress={handleStopAR}
            >
              <Ionicons name="close" size={24} color="#FFFFFF" />
              <Text style={styles.stopButtonText}>Stop AR</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  setupContainer: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  infoCard: {
    backgroundColor: 'rgba(90, 200, 250, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  infoRow: {
    flexDirection: 'row',
    gap: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
  },
  devicesSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  devicesList: {
    gap: 12,
  },
  deviceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
  },
  deviceName: {
    fontSize: 16,
    fontWeight: '500',
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    borderRadius: 12,
    gap: 12,
    marginBottom: 16,
  },
  startButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  },
  noteCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    padding: 12,
    borderRadius: 8,
  },
  noteText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 16,
  },
  arViewContainer: {
    flex: 1,
  },
  arView: {
    flex: 1,
    position: 'relative',
  },
  arPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#000000',
  },
  arPlaceholderText: {
    fontSize: 24,
    fontWeight: '600',
    marginTop: 16,
  },
  arPlaceholderSubtext: {
    fontSize: 14,
    marginTop: 8,
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  arDeviceOverlay: {
    position: 'absolute',
    top: 60,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  arDeviceName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  arDeviceState: {
    fontSize: 14,
    fontWeight: '500',
  },
  stopButton: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  stopButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default ARScreen;

