/**
 * Permission utilities for Smart Glasses React Native app
 * Handles camera, microphone, and location permissions
 */
import { PermissionsAndroid, Platform } from 'react-native';

/**
 * Request camera permission
 * @returns {Promise<boolean>} - True if granted, false otherwise
 */
export async function requestCameraPermission() {
  if (Platform.OS === 'ios') {
    // iOS requires Info.plist entries, permission is automatic on first use
    return true;
  }

  try {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.CAMERA,
      {
        title: 'Camera Permission',
        message: 'Smart Glasses needs camera access for object detection and navigation',
        buttonNeutral: 'Ask Me Later',
        buttonNegative: 'Cancel',
        buttonPositive: 'OK',
      }
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  } catch (err) {
    console.warn('Camera permission error:', err);
    return false;
  }
}

/**
 * Request microphone permission
 * @returns {Promise<boolean>} - True if granted, false otherwise
 */
export async function requestMicrophonePermission() {
  if (Platform.OS === 'ios') {
    // iOS requires Info.plist entries, permission is automatic on first use
    return true;
  }

  try {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      {
        title: 'Microphone Permission',
        message: 'Smart Glasses needs microphone access for voice commands',
        buttonNeutral: 'Ask Me Later',
        buttonNegative: 'Cancel',
        buttonPositive: 'OK',
      }
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  } catch (err) {
    console.warn('Microphone permission error:', err);
    return false;
  }
}

/**
 * Request location permission (for indoor navigation)
 * @returns {Promise<boolean>} - True if granted, false otherwise
 */
export async function requestLocationPermission() {
  if (Platform.OS === 'ios') {
    // iOS location permission is separate
    return true;
  }

  try {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      {
        title: 'Location Permission',
        message: 'Smart Glasses needs location for indoor navigation',
        buttonNeutral: 'Ask Me Later',
        buttonNegative: 'Cancel',
        buttonPositive: 'OK',
      }
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  } catch (err) {
    console.warn('Location permission error:', err);
    return false;
  }
}

/**
 * Request all required permissions at once
 * @returns {Promise<Object>} - Object with permission results
 */
export async function requestAllPermissions() {
  const results = {
    camera: false,
    microphone: false,
    location: false,
  };

  // For Android, request all at once
  if (Platform.OS === 'android') {
    try {
      const permissions = await PermissionsAndroid.requestMultiple([
        PermissionsAndroid.PERMISSIONS.CAMERA,
        PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
        PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      ]);

      results.camera = permissions[PermissionsAndroid.PERMISSIONS.CAMERA] === PermissionsAndroid.RESULTS.GRANTED;
      results.microphone = permissions[PermissionsAndroid.PERMISSIONS.RECORD_AUDIO] === PermissionsAndroid.RESULTS.GRANTED;
      results.location = permissions[PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION] === PermissionsAndroid.RESULTS.GRANTED;
    } catch (err) {
      console.warn('Multiple permissions error:', err);
    }
  } else {
    // For iOS, permissions are handled separately
    results.camera = true;
    results.microphone = true;
    results.location = true;
  }

  return results;
}

/**
 * Check if all required permissions are granted
 * @returns {Promise<boolean>}
 */
export async function checkAllPermissions() {
  const results = await requestAllPermissions();
  return results.camera && results.microphone;
}

/**
 * Get permission status for display
 * @returns {Promise<Object>}
 */
export async function getPermissionStatus() {
  if (Platform.OS === 'ios') {
    return {
      camera: 'granted',
      microphone: 'granted',
      location: 'granted',
    };
  }

  const checkPermission = async (permission) => {
    const status = await PermissionsAndroid.check(permission);
    return status ? 'granted' : 'denied';
  };

  return {
    camera: await checkPermission(PermissionsAndroid.PERMISSIONS.CAMERA),
    microphone: await checkPermission(PermissionsAndroid.PERMISSIONS.RECORD_AUDIO),
    location: await checkPermission(PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION),
  };
}

export default {
  requestCameraPermission,
  requestMicrophonePermission,
  requestLocationPermission,
  requestAllPermissions,
  checkAllPermissions,
  getPermissionStatus,
};