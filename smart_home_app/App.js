import React, { useEffect } from 'react';
import { Provider, useDispatch } from 'react-redux';
import { StatusBar } from 'expo-status-bar';
import { store } from './src/store';
import AppNavigator from './src/navigation/AppNavigator';
import { storage } from './src/utils/storage';
import { setDevices, setControllers } from './src/store/slices/devicesSlice';
import { setStatistics } from './src/store/slices/statisticsSlice';
import { setTheme } from './src/store/slices/themeSlice';

// Component to load persisted data
const AppInitializer = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    const loadPersistedData = async () => {
      try {
        // Load devices
        const savedDevices = await storage.loadDevices();
        if (savedDevices && savedDevices.length > 0) {
          dispatch(setDevices(savedDevices));
        }

        // Load controllers
        const savedControllers = await storage.loadControllers();
        if (savedControllers && savedControllers.length > 0) {
          dispatch(setControllers(savedControllers));
        }

        // Load statistics
        const savedStatistics = await storage.loadStatistics();
        if (savedStatistics) {
          dispatch(setStatistics(savedStatistics));
        }

        // Load theme preference
        const savedTheme = await storage.loadTheme();
        dispatch(setTheme(savedTheme));
      } catch (error) {
        console.error('Error loading persisted data:', error);
      }
    };

    loadPersistedData();
  }, [dispatch]);

  return <AppNavigator />;
};

export default function App() {
  return (
    <Provider store={store}>
      <StatusBar style="auto" />
      <AppInitializer />
    </Provider>
  );
}
