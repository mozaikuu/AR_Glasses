import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { addController } from '../store/slices/devicesSlice';
import { storage } from '../utils/storage';
import { lightTheme, darkTheme } from '../constants/theme';

const AddControllerScreen = ({ navigation }) => {
  const dispatch = useDispatch();
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const controllers = useSelector((state) => state.devices.controllers);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [name, setName] = useState('');
  const [type, setType] = useState('bluetooth');
  const [macAddress, setMacAddress] = useState('');
  const [description, setDescription] = useState('');

  const controllerTypes = [
    { label: 'Bluetooth', value: 'bluetooth', icon: 'bluetooth' },
    { label: 'Wi-Fi', value: 'wifi', icon: 'wifi' },
    { label: 'Zigbee', value: 'zigbee', icon: 'radio' },
    { label: 'Z-Wave', value: 'zwave', icon: 'radio' },
    { label: 'Other', value: 'other', icon: 'hardware-chip' },
  ];

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a controller name');
      return;
    }

    if (type === 'bluetooth' && !macAddress.trim()) {
      Alert.alert('Error', 'Please enter a MAC address for Bluetooth controller');
      return;
    }

    const newController = {
      name: name.trim(),
      type,
      macAddress: macAddress.trim() || undefined,
      description: description.trim() || undefined,
      connected: false,
    };

    dispatch(addController(newController));

    // Save to storage
    const updatedControllers = [
      ...controllers,
      {
        id: Date.now().toString(),
        ...newController,
        createdAt: new Date().toISOString(),
      },
    ];
    await storage.saveControllers(updatedControllers);

    Alert.alert('Success', 'Controller added successfully', [
      { text: 'OK', onPress: () => navigation.goBack() },
    ]);
  };

  const handleScanBluetooth = () => {
    Alert.alert(
      'Bluetooth Scan',
      'Bluetooth scanning functionality would be implemented here. This would use expo-bluetooth to discover nearby devices.',
      [{ text: 'OK' }]
    );
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.content}>
        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>
            Controller Name *
          </Text>
          <TextInput
            style={[
              styles.input,
              {
                backgroundColor: theme.surface,
                color: theme.text,
                borderColor: theme.border,
              },
            ]}
            value={name}
            onChangeText={setName}
            placeholder="Enter controller name"
            placeholderTextColor={theme.textSecondary}
          />
        </View>

        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>
            Controller Type
          </Text>
          <View
            style={[
              styles.typeContainer,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
          >
            {controllerTypes.map((item) => (
              <TouchableOpacity
                key={item.value}
                style={[
                  styles.typeOption,
                  {
                    backgroundColor:
                      type === item.value ? theme.primary : 'transparent',
                    borderColor: theme.border,
                  },
                ]}
                onPress={() => setType(item.value)}
              >
                <Ionicons
                  name={item.icon}
                  size={20}
                  color={type === item.value ? '#FFFFFF' : theme.text}
                />
                <Text
                  style={[
                    styles.typeOptionText,
                    {
                      color: type === item.value ? '#FFFFFF' : theme.text,
                    },
                  ]}
                >
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {type === 'bluetooth' && (
          <View style={[styles.section, { backgroundColor: theme.card }]}>
            <View style={styles.labelRow}>
              <Text style={[styles.label, { color: theme.text }]}>
                MAC Address *
              </Text>
              <TouchableOpacity
                style={[styles.scanButton, { backgroundColor: theme.primary }]}
                onPress={handleScanBluetooth}
              >
                <Ionicons name="search" size={16} color="#FFFFFF" />
                <Text style={styles.scanButtonText}>Scan</Text>
              </TouchableOpacity>
            </View>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: theme.surface,
                  color: theme.text,
                  borderColor: theme.border,
                  fontFamily: 'monospace',
                },
              ]}
              value={macAddress}
              onChangeText={setMacAddress}
              placeholder="XX:XX:XX:XX:XX:XX"
              placeholderTextColor={theme.textSecondary}
              autoCapitalize="characters"
            />
            <Text style={[styles.hint, { color: theme.textSecondary }]}>
              Format: XX:XX:XX:XX:XX:XX
            </Text>
          </View>
        )}

        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>
            Description
          </Text>
          <TextInput
            style={[
              styles.textArea,
              {
                backgroundColor: theme.surface,
                color: theme.text,
                borderColor: theme.border,
              },
            ]}
            value={description}
            onChangeText={setDescription}
            placeholder="Enter controller description (optional)"
            placeholderTextColor={theme.textSecondary}
            multiline
            numberOfLines={4}
          />
        </View>

        <TouchableOpacity
          style={[styles.saveButton, { backgroundColor: theme.primary }]}
          onPress={handleSave}
        >
          <Text style={styles.saveButtonText}>Add Controller</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  section: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  textArea: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
  },
  typeContainer: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 4,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 6,
    margin: 4,
    borderWidth: 1,
    gap: 8,
    minWidth: 100,
    justifyContent: 'center',
  },
  typeOptionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  scanButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    gap: 4,
  },
  scanButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  hint: {
    fontSize: 12,
    marginTop: 4,
  },
  saveButton: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default AddControllerScreen;

