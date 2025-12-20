import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEYS = {
  DEVICES: '@smart_glasses:devices',
  CONTROLLERS: '@smart_glasses:controllers',
  STATISTICS: '@smart_glasses:statistics',
  THEME: '@smart_glasses:theme',
};

export const storage = {
  // Devices
  async saveDevices(devices) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.DEVICES, JSON.stringify(devices));
    } catch (error) {
      console.error('Error saving devices:', error);
    }
  },

  async loadDevices() {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.DEVICES);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading devices:', error);
      return [];
    }
  },

  // Controllers
  async saveControllers(controllers) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.CONTROLLERS, JSON.stringify(controllers));
    } catch (error) {
      console.error('Error saving controllers:', error);
    }
  },

  async loadControllers() {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.CONTROLLERS);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Error loading controllers:', error);
      return [];
    }
  },

  // Statistics
  async saveStatistics(statistics) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.STATISTICS, JSON.stringify(statistics));
    } catch (error) {
      console.error('Error saving statistics:', error);
    }
  },

  async loadStatistics() {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.STATISTICS);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error loading statistics:', error);
      return null;
    }
  },

  // Theme
  async saveTheme(isDarkMode) {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.THEME, JSON.stringify(isDarkMode));
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  },

  async loadTheme() {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.THEME);
      return data ? JSON.parse(data) : true;
    } catch (error) {
      console.error('Error loading theme:', error);
      return true;
    }
  },

  // Clear all data
  async clearAll() {
    try {
      await AsyncStorage.multiRemove(Object.values(STORAGE_KEYS));
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },
};

