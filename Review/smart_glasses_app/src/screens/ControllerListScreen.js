import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { removeController, updateControllerConnection } from '../store/slices/devicesSlice';
import { storage } from '../utils/storage';
import { lightTheme, darkTheme } from '../constants/theme';

const ControllerListScreen = ({ navigation }) => {
  const dispatch = useDispatch();
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const controllers = useSelector((state) => state.devices.controllers);
  const theme = isDarkMode ? darkTheme : lightTheme;

  useEffect(() => {
    // Load controllers from storage on mount
    const loadControllers = async () => {
      const savedControllers = await storage.loadControllers();
      if (savedControllers && savedControllers.length > 0) {
        // Controllers are already loaded via Redux persistence
      }
    };
    loadControllers();
  }, []);

  const handleDelete = (controller) => {
    Alert.alert(
      'Remove Controller',
      `Are you sure you want to remove ${controller.name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            dispatch(removeController(controller.id));
            const updatedControllers = controllers.filter((c) => c.id !== controller.id);
            await storage.saveControllers(updatedControllers);
          },
        },
      ]
    );
  };

  const handleToggleConnection = async (controller) => {
    const newConnectionState = !controller.connected;
    dispatch(updateControllerConnection({ id: controller.id, connected: newConnectionState }));
    const updatedControllers = controllers.map((c) =>
      c.id === controller.id ? { ...c, connected: newConnectionState } : c
    );
    await storage.saveControllers(updatedControllers);
  };

  const renderController = ({ item }) => (
    <View style={[styles.controllerCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
      <View style={styles.controllerHeader}>
        <View style={styles.controllerInfo}>
          <View style={styles.iconContainer}>
            <Ionicons name="bluetooth" size={32} color={theme.primary} />
          </View>
          <View style={styles.infoContainer}>
            <Text style={[styles.controllerName, { color: theme.text }]}>
              {item.name}
            </Text>
            <Text style={[styles.controllerType, { color: theme.textSecondary }]}>
              {item.type || 'Bluetooth Controller'}
            </Text>
            {item.macAddress && (
              <Text style={[styles.macAddress, { color: theme.textSecondary }]}>
                {item.macAddress}
              </Text>
            )}
          </View>
        </View>
        <View style={styles.statusContainer}>
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor: item.connected
                  ? theme.success + '20'
                  : theme.textSecondary + '20',
              },
            ]}
          >
            <View
              style={[
                styles.statusDot,
                {
                  backgroundColor: item.connected ? theme.success : theme.textSecondary,
                },
              ]}
            />
            <Text
              style={[
                styles.statusText,
                {
                  color: item.connected ? theme.success : theme.textSecondary,
                },
              ]}
            >
              {item.connected ? 'Connected' : 'Disconnected'}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.actionsContainer}>
        <TouchableOpacity
          style={[
            styles.actionButton,
            {
              backgroundColor: item.connected
                ? theme.error + '20'
                : theme.success + '20',
            },
          ]}
          onPress={() => handleToggleConnection(item)}
        >
          <Ionicons
            name={item.connected ? 'close-circle' : 'checkmark-circle'}
            size={20}
            color={item.connected ? theme.error : theme.success}
          />
          <Text
            style={[
              styles.actionButtonText,
              {
                color: item.connected ? theme.error : theme.success,
              },
            ]}
          >
            {item.connected ? 'Disconnect' : 'Connect'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.error + '20' }]}
          onPress={() => handleDelete(item)}
        >
          <Ionicons name="trash" size={20} color={theme.error} />
          <Text style={[styles.actionButtonText, { color: theme.error }]}>
            Remove
          </Text>
        </TouchableOpacity>
      </View>

      {item.description && (
        <View style={styles.descriptionContainer}>
          <Text style={[styles.description, { color: theme.textSecondary }]}>
            {item.description}
          </Text>
        </View>
      )}
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <FlatList
        data={controllers}
        renderItem={renderController}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons
              name="bluetooth-outline"
              size={64}
              color={theme.textSecondary}
            />
            <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
              No controllers added yet
            </Text>
            <TouchableOpacity
              style={[styles.addButton, { backgroundColor: theme.primary }]}
              onPress={() => navigation.navigate('AddController')}
            >
              <Text style={styles.addButtonText}>Add Your First Controller</Text>
            </TouchableOpacity>
          </View>
        }
      />
      <TouchableOpacity
        style={[styles.fab, { backgroundColor: theme.primary }]}
        onPress={() => navigation.navigate('AddController')}
      >
        <Ionicons name="add" size={28} color="#FFFFFF" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: 20,
    paddingBottom: 100,
  },
  controllerCard: {
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
  controllerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  controllerInfo: {
    flexDirection: 'row',
    flex: 1,
  },
  iconContainer: {
    marginRight: 12,
  },
  infoContainer: {
    flex: 1,
  },
  controllerName: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  controllerType: {
    fontSize: 14,
    marginBottom: 4,
  },
  macAddress: {
    fontSize: 12,
    fontFamily: 'monospace',
  },
  statusContainer: {
    alignItems: 'flex-end',
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  descriptionContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  description: {
    fontSize: 14,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
    marginTop: 100,
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
  fab: {
    position: 'absolute',
    right: 20,
    bottom: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 8,
  },
});

export default ControllerListScreen;

