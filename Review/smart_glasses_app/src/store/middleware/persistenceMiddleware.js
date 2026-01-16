import { storage } from '../../utils/storage';

// Middleware to persist Redux state to AsyncStorage
export const persistenceMiddleware = (store) => (next) => (action) => {
  const result = next(action);
  const state = store.getState();

  // Persist devices
  if (
    action.type.startsWith('devices/') &&
    !action.type.includes('setLoading') &&
    !action.type.includes('setError')
  ) {
    storage.saveDevices(state.devices.devices);
    storage.saveControllers(state.devices.controllers);
  }

  // Persist statistics
  if (action.type.startsWith('statistics/')) {
    storage.saveStatistics({
      commandHistory: state.statistics.commandHistory,
      deviceUsage: state.statistics.deviceUsage,
      mostUsedCommands: state.statistics.mostUsedCommands,
      applianceInfo: state.statistics.applianceInfo,
    });
  }

  // Persist theme
  if (action.type.startsWith('theme/')) {
    storage.saveTheme(state.theme.isDarkMode);
  }

  return result;
};

