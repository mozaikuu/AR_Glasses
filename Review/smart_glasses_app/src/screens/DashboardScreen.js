import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import DeviceCard from '../components/DeviceCard';
import { updateDeviceState } from '../store/slices/devicesSlice';
import { addCommand } from '../store/slices/statisticsSlice';
import { toggleTheme } from '../store/slices/themeSlice';
import { deviceStateColors, lightTheme, darkTheme } from '../constants/theme';

const DashboardScreen = ({ navigation }) => {
  const dispatch = useDispatch();
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    // Simulate data refresh
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  }, []);

  const handleDeviceControl = (device) => {
    navigation.navigate('Devices', {
      screen: 'DeviceDetail',
      params: { deviceId: device.id },
    });
  };

  const handleQuickControl = (device, newState) => {
    dispatch(updateDeviceState({ id: device.id, state: newState }));
    dispatch(
      addCommand({
        deviceId: device.id,
        deviceName: device.name,
        action: newState,
      })
    );
  };

  const getDeviceCountByState = (state) => {
    return devices.filter((d) => d.state === state).length;
  };

  const stats = {
    total: devices.length,
    on: getDeviceCountByState('ON'),
    off: getDeviceCountByState('OFF'),
    running: getDeviceCountByState('RUNNING'),
    malfunction: getDeviceCountByState('MALFUNCTION'),
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, { color: theme.text }]}>Smart Glasses</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Dashboard
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.themeButton, { backgroundColor: theme.surface }]}
          onPress={() => dispatch(toggleTheme())}
        >
          <Ionicons
            name={isDarkMode ? 'sunny' : 'moon'}
            size={24}
            color={theme.primary}
          />
        </TouchableOpacity>
      </View>

      {/* Statistics Cards */}
      <View style={styles.statsContainer}>
        <View style={[styles.statCard, { backgroundColor: theme.card }]}>
          <Text style={[styles.statValue, { color: theme.text }]}>
            {stats.total}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            Total Devices
          </Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.card }]}>
          <Text
            style={[styles.statValue, { color: deviceStateColors.ON }]}
          >
            {stats.on}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            ON
          </Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.card }]}>
          <Text
            style={[styles.statValue, { color: deviceStateColors.RUNNING }]}
          >
            {stats.running}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            Running
          </Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: theme.card }]}>
          <Text
            style={[
              styles.statValue,
              { color: deviceStateColors.MALFUNCTION },
            ]}
          >
            {stats.malfunction}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textSecondary }]}>
            Issues
          </Text>
        </View>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>
          Quick Actions
        </Text>
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: theme.primary }]}
            onPress={() => navigation.navigate('Devices')}
          >
            <Ionicons name="add-circle" size={24} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Add Device</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: theme.secondary }]}
            onPress={() => navigation.navigate('Controllers')}
          >
            <Ionicons name="bluetooth" size={24} color="#FFFFFF" />
            <Text style={styles.actionButtonText}>Controllers</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Devices List */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Your Devices
          </Text>
          <TouchableOpacity onPress={() => navigation.navigate('Devices')}>
            <Text style={[styles.seeAll, { color: theme.primary }]}>
              See All
            </Text>
          </TouchableOpacity>
        </View>

        {devices.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Ionicons
              name="hardware-chip-outline"
              size={64}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No devices added yet
            </Text>
            <TouchableOpacity
              style={[styles.addButton, { backgroundColor: theme.primary }]}
              onPress={() => navigation.navigate('Devices')}
            >
              <Text style={styles.addButtonText}>Add Your First Device</Text>
            </TouchableOpacity>
          </View>
        ) : (
          devices.slice(0, 5).map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              onPress={() => handleDeviceControl(device)}
              onControl={handleDeviceControl}
            />
          ))
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  subtitle: {
    fontSize: 16,
    marginTop: 4,
  },
  themeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 24,
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  seeAll: {
    fontSize: 14,
    fontWeight: '600',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    marginTop: 16,
    marginBottom: 24,
  },
  addButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default DashboardScreen;

