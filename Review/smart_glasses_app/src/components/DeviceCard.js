import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSelector } from 'react-redux';
import { deviceStateColors } from '../constants/theme';

const DeviceCard = ({ device, onPress, onControl }) => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const theme = isDarkMode ? require('../constants/theme').darkTheme : require('../constants/theme').lightTheme;

  const getStateColor = (state) => {
    return deviceStateColors[state] || theme.textSecondary;
  };

  const getDeviceIcon = (type) => {
    const icons = {
      light: 'bulb',
      thermostat: 'thermometer',
      camera: 'camera',
      door: 'lock-closed',
      window: 'square',
      fan: 'leaf',
      tv: 'tv',
      speaker: 'musical-notes',
      default: 'hardware-chip',
    };
    return icons[type?.toLowerCase()] || icons.default;
  };

  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: theme.card, borderColor: theme.border }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <View style={styles.iconContainer}>
          <Ionicons
            name={getDeviceIcon(device.type)}
            size={32}
            color={theme.primary}
          />
        </View>
        <View style={styles.infoContainer}>
          <Text style={[styles.name, { color: theme.text }]}>{device.name}</Text>
          <Text style={[styles.type, { color: theme.textSecondary }]}>
            {device.type || 'Device'}
          </Text>
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
            style={[
              styles.stateText,
              { color: getStateColor(device.state) },
            ]}
          >
            {device.state}
          </Text>
        </View>
      </View>

      {device.location && (
        <View style={styles.locationContainer}>
          <Ionicons name="location" size={14} color={theme.textSecondary} />
          <Text style={[styles.location, { color: theme.textSecondary }]}>
            {device.location}
          </Text>
        </View>
      )}

      {onControl && (
        <TouchableOpacity
          style={[styles.controlButton, { backgroundColor: theme.primary }]}
          onPress={() => onControl(device)}
          activeOpacity={0.8}
        >
          <Text style={styles.controlButtonText}>Control</Text>
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  iconContainer: {
    marginRight: 12,
  },
  infoContainer: {
    flex: 1,
  },
  name: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  type: {
    fontSize: 14,
  },
  stateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  stateDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  stateText: {
    fontSize: 12,
    fontWeight: '600',
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  location: {
    fontSize: 12,
    marginLeft: 4,
  },
  controlButton: {
    marginTop: 12,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  controlButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default DeviceCard;

