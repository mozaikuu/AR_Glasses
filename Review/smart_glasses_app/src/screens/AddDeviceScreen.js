import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  Picker,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { Ionicons } from '@expo/vector-icons';
import { addDevice } from '../store/slices/devicesSlice';
import { storage } from '../utils/storage';
import { lightTheme, darkTheme } from '../constants/theme';

const AddDeviceScreen = ({ navigation }) => {
  const dispatch = useDispatch();
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const devices = useSelector((state) => state.devices.devices);
  const theme = isDarkMode ? darkTheme : lightTheme;

  const [name, setName] = useState('');
  const [type, setType] = useState('light');
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [controllerId, setControllerId] = useState('');

  const deviceTypes = [
    { label: 'Light', value: 'light' },
    { label: 'Thermostat', value: 'thermostat' },
    { label: 'Camera', value: 'camera' },
    { label: 'Door Lock', value: 'door' },
    { label: 'Window', value: 'window' },
    { label: 'Fan', value: 'fan' },
    { label: 'TV', value: 'tv' },
    { label: 'Speaker', value: 'speaker' },
    { label: 'Other', value: 'other' },
  ];

  const handleSave = () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a device name');
      return;
    }

    const newDevice = {
      name: name.trim(),
      type,
      location: location.trim() || undefined,
      description: description.trim() || undefined,
      controllerId: controllerId || undefined,
      state: 'OFF',
    };

    dispatch(addDevice(newDevice));
    
    // Save to storage
    const updatedDevices = [...devices, {
      id: Date.now().toString(),
      ...newDevice,
      createdAt: new Date().toISOString(),
      usageCount: 0,
    }];
    storage.saveDevices(updatedDevices);

    Alert.alert('Success', 'Device added successfully', [
      { text: 'OK', onPress: () => navigation.goBack() },
    ]);
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.content}>
        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>
            Device Name *
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
            placeholder="Enter device name"
            placeholderTextColor={theme.textSecondary}
          />
        </View>

        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>Device Type</Text>
          <View
            style={[
              styles.pickerContainer,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
          >
            {deviceTypes.map((item) => (
              <TouchableOpacity
                key={item.value}
                style={[
                  styles.pickerOption,
                  {
                    backgroundColor:
                      type === item.value ? theme.primary : 'transparent',
                  },
                ]}
                onPress={() => setType(item.value)}
              >
                <Text
                  style={[
                    styles.pickerOptionText,
                    {
                      color:
                        type === item.value ? '#FFFFFF' : theme.text,
                    },
                  ]}
                >
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={[styles.section, { backgroundColor: theme.card }]}>
          <Text style={[styles.label, { color: theme.text }]}>Location</Text>
          <TextInput
            style={[
              styles.input,
              {
                backgroundColor: theme.surface,
                color: theme.text,
                borderColor: theme.border,
              },
            ]}
            value={location}
            onChangeText={setLocation}
            placeholder="e.g., Living Room, Bedroom"
            placeholderTextColor={theme.textSecondary}
          />
        </View>

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
            placeholder="Enter device description (optional)"
            placeholderTextColor={theme.textSecondary}
            multiline
            numberOfLines={4}
          />
        </View>

        <TouchableOpacity
          style={[styles.saveButton, { backgroundColor: theme.primary }]}
          onPress={handleSave}
        >
          <Text style={styles.saveButtonText}>Add Device</Text>
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
  pickerContainer: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 4,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pickerOption: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    margin: 4,
  },
  pickerOptionText: {
    fontSize: 14,
    fontWeight: '500',
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

export default AddDeviceScreen;

