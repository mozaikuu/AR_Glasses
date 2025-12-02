import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSelector } from 'react-redux';

// Screens
import DashboardScreen from '../screens/DashboardScreen';
import DeviceListScreen from '../screens/DeviceListScreen';
import DeviceDetailScreen from '../screens/DeviceDetailScreen';
import AddDeviceScreen from '../screens/AddDeviceScreen';
import ControllerListScreen from '../screens/ControllerListScreen';
import AddControllerScreen from '../screens/AddControllerScreen';
import StatisticsScreen from '../screens/StatisticsScreen';
import ARScreen from '../screens/ARScreen';
import VRScreen from '../screens/VRScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const DeviceStack = () => (
  <Stack.Navigator>
    <Stack.Screen 
      name="DeviceList" 
      component={DeviceListScreen}
      options={{ title: 'Devices' }}
    />
    <Stack.Screen 
      name="DeviceDetail" 
      component={DeviceDetailScreen}
      options={{ title: 'Device Details' }}
    />
    <Stack.Screen 
      name="AddDevice" 
      component={AddDeviceScreen}
      options={{ title: 'Add Device' }}
    />
  </Stack.Navigator>
);

const ControllerStack = () => (
  <Stack.Navigator>
    <Stack.Screen 
      name="ControllerList" 
      component={ControllerListScreen}
      options={{ title: 'Controllers' }}
    />
    <Stack.Screen 
      name="AddController" 
      component={AddControllerScreen}
      options={{ title: 'Add Controller' }}
    />
  </Stack.Navigator>
);

const MainTabs = () => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  
  const theme = {
    dark: isDarkMode,
    colors: {
      primary: '#22c55e',
      background: isDarkMode ? '#000000' : '#FFFFFF',
      card: isDarkMode ? '#1C1C1E' : '#F2F2F7',
      text: isDarkMode ? '#FFFFFF' : '#000000',
      border: isDarkMode ? '#38383A' : '#C6C6C8',
      notification: '#FF3B30',
    },
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Devices') {
            iconName = focused ? 'hardware-chip' : 'hardware-chip-outline';
          } else if (route.name === 'Controllers') {
            iconName = focused ? 'bluetooth' : 'bluetooth-outline';
          } else if (route.name === 'Statistics') {
            iconName = focused ? 'stats-chart' : 'stats-chart-outline';
          } else if (route.name === 'AR') {
            iconName = focused ? 'cube' : 'cube-outline';
          } else if (route.name === 'VR') {
            iconName = focused ? 'glasses' : 'glasses-outline';
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.border,
        tabBarStyle: {
          backgroundColor: theme.colors.card,
          borderTopColor: theme.colors.border,
        },
        headerStyle: {
          backgroundColor: theme.colors.card,
        },
        headerTintColor: theme.colors.text,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Devices" component={DeviceStack} />
      <Tab.Screen name="Controllers" component={ControllerStack} />
      <Tab.Screen name="Statistics" component={StatisticsScreen} />
      <Tab.Screen name="AR" component={ARScreen} />
      <Tab.Screen name="VR" component={VRScreen} />
    </Tab.Navigator>
  );
};

const AppNavigator = () => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  
  const theme = {
    dark: isDarkMode,
    colors: {
      primary: '#22c55e',
      background: isDarkMode ? '#000000' : '#FFFFFF',
      card: isDarkMode ? '#1C1C1E' : '#F2F2F7',
      text: isDarkMode ? '#FFFFFF' : '#000000',
      border: isDarkMode ? '#38383A' : '#C6C6C8',
      notification: '#FF3B30',
    },
  };

  return (
    <NavigationContainer theme={theme}>
      <MainTabs />
    </NavigationContainer>
  );
};

export default AppNavigator;

