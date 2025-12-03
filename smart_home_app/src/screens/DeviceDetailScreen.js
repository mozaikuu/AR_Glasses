import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Switch,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { updateDeviceState, removeDevice } from '../store/slices/devicesSlice';
import { addCommand } from '../store/slices/statisticsSlice';
import { deviceStateColors, lightTheme, darkTheme } from '../constants/theme';
import { storage } from '../utils/storage';

const DeviceDetailScreen = ({ route, navigation }) => {
  const { deviceId } = route.params;
  const dispatch = useDispatch();
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const device = devices.find((d) => d.id === deviceId);

  if (!device) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <Text style={[styles.errorText, { color: theme.text }]}>
          Device not found
        </Text>
      </View>
    );
  }

  const handleStateChange = (newState) => {
    dispatch(updateDeviceState({ id: device.id, state: newState }));
    dispatch(
      addCommand({
        deviceId: device.id,
        deviceName: device.name,
        action: newState,
      })
    );
    // Save to storage
    const updatedDevices = devices.map((d) =>
      d.id === device.id ? { ...d, state: newState } : d
    );
    storage.saveDevices(updatedDevices);
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Device',
      `Are you sure you want to delete ${device.name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            dispatch(removeDevice(device.id));
            const updatedDevices = devices.filter((d) => d.id !== device.id);
            storage.saveDevices(updatedDevices);
            navigation.goBack();
          },
        },
      ]
    );
  };

  const getStateColor = (state) => {
    return deviceStateColors[state] || theme.textSecondary;
  };

  const isOn = device.state === 'ON' || device.state === 'RUNNING';

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={[styles.header, { backgroundColor: theme.card }]}>
        <View style={styles.headerContent}>
          <View style={styles.iconContainer}>
            <Ionicons name="hardware-chip" size={48} color={theme.primary} />
          </View>
          <View style={styles.headerInfo}>
            <Text style={[styles.deviceName, { color: theme.text }]}>
              {device.name}
            </Text>
            <Text style={[styles.deviceType, { color: theme.textSecondary }]}>
              {device.type || 'Device'}
            </Text>
          </View>
        </View>
        <View
          style={[
            styles.stateBadge,
            { backgroundColor: getStateColor(device.state) + '20' },
          ]}
        >
          <View
            style={[
              styles.stateDot,
              { backgroundColor: getStateColor(device.state) },
            ]}
          />
          <Text
            style={[styles.stateText, { color: getStateColor(device.state) }]}
          >
            {device.state}
          </Text>
        </View>
      </View>

      <View style={styles.content}>
        {/* Control Section */}
        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Control
          </Text>
          <View style={styles.controlRow}>
            <Text style={[styles.controlLabel, { color: theme.text }]}>
              Power
            </Text>
            <Switch
              value={isOn}
              onValueChange={(value) =>
                handleStateChange(value ? 'ON' : 'OFF')
              }
              trackColor={{ false: theme.border, true: theme.primary }}
              thumbColor="#FFFFFF"
            />
          </View>

          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[
                styles.controlButton,
                {
                  backgroundColor:
                    device.state === 'ON' ? theme.primary : theme.surface,
                },
              ]}
              onPress={() => handleStateChange('ON')}
            >
              <Ionicons
                name="power"
                size={20}
                color={device.state === 'ON' ? '#FFFFFF' : theme.text}
              />
              <Text
                style={[
                  styles.controlButtonText,
                  {
                    color: device.state === 'ON' ? '#FFFFFF' : theme.text,
                  },
                ]}
              >
                ON
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.controlButton,
                {
                  backgroundColor:
                    device.state === 'OFF' ? theme.primary : theme.surface,
                },
              ]}
              onPress={() => handleStateChange('OFF')}
            >
              <Ionicons
                name="power-outline"
                size={20}
                color={device.state === 'OFF' ? '#FFFFFF' : theme.text}
              />
              <Text
                style={[
                  styles.controlButtonText,
                  {
                    color: device.state === 'OFF' ? '#FFFFFF' : theme.text,
                  },
                ]}
              >
                OFF
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[
                styles.controlButton,
                {
                  backgroundColor:
                    device.state === 'RUNNING' ? theme.primary : theme.surface,
                },
              ]}
              onPress={() => handleStateChange('RUNNING')}
            >
              <Ionicons
                name="play"
                size={20}
                color={device.state === 'RUNNING' ? '#FFFFFF' : theme.text}
              />
              <Text
                style={[
                  styles.controlButtonText,
                  {
                    color: device.state === 'RUNNING' ? '#FFFFFF' : theme.text,
                  },
                ]}
              >
                RUN
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Information Section */}
        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Information
          </Text>
          {device.location && (
            <View style={styles.infoRow}>
              <Ionicons name="location" size={20} color={theme.textSecondary} />
              <Text style={[styles.infoText, { color: theme.text }]}>
                {device.location}
              </Text>
            </View>
          )}
          {device.description && (
            <View style={styles.infoRow}>
              <Ionicons name="document-text" size={20} color={theme.textSecondary} />
              <Text style={[styles.infoText, { color: theme.text }]}>
                {device.description}
              </Text>
            </View>
          )}
          <View style={styles.infoRow}>
            <Ionicons name="stats-chart" size={20} color={theme.textSecondary} />
            <Text style={[styles.infoText, { color: theme.text }]}>
              Usage Count: {device.usageCount || 0}
            </Text>
          </View>
          {device.createdAt && (
            <View style={styles.infoRow}>
              <Ionicons name="calendar" size={20} color={theme.textSecondary} />
              <Text style={[styles.infoText, { color: theme.text }]}>
                Added: {new Date(device.createdAt).toLocaleDateString()}
              </Text>
            </View>
          )}
        </View>

        {/* Delete Button */}
        <TouchableOpacity
          style={[styles.deleteButton, { backgroundColor: theme.error }]}
          onPress={handleDelete}
        >
          <Ionicons name="trash" size={20} color="#FFFFFF" />
          <Text style={styles.deleteButtonText}>Delete Device</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconContainer: {
    marginRight: 16,
  },
  headerInfo: {
    flex: 1,
  },
  deviceName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  deviceType: {
    fontSize: 16,
  },
  stateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
  },
  stateDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  stateText: {
    fontSize: 14,
    fontWeight: '600',
  },
  content: {
    padding: 20,
  },
  section: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  controlRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  controlLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  controlButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  controlButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  infoText: {
    fontSize: 14,
    flex: 1,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    gap: 8,
    marginTop: 8,
  },
  deleteButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 100,
  },
});

export default DeviceDetailScreen;

