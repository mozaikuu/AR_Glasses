# Smart Home React Native App

A comprehensive React Native application for managing and controlling smart home devices with features including device management, usage statistics, AR/VR experiences, and more.

## Features

### 1. Dashboard (Dark Mode)
- Display device states: ON, OFF, MALFUNCTION, RUNNING
- Quick statistics overview
- Manual control with buttons
- Dedicated screens for each device
- Dark mode support with theme toggle

### 2. Device & Controller Management
- Add/connect devices and controllers (including Bluetooth modules)
- Remove devices
- Show device information and usage statistics
- Support for multiple device types (lights, thermostats, cameras, locks, etc.)
- Controller connection management (Bluetooth, Wi-Fi, Zigbee, Z-Wave)

### 3. Usage Statistics
- Track most used commands
- Show info for each home appliance
- Usage charts and graphs
- Command history
- Device usage statistics

### 4. Optional Features
- Basic AR mobile experience (placeholder)
- Basic Meta-Quest VR functionality (placeholder)

### 5. Input/Output Communication
- Two-way communication between phone and dashboard
- Real-time device state updates
- Command tracking and history

### 6. UI & UX
- Clean, responsive, and intuitive interface using React Native components
- Navigation between screens using React Navigation
- Data persistence using AsyncStorage
- Redux for state management

## Tech Stack

- **React Native** - Mobile framework
- **Expo** - Development platform
- **Redux Toolkit** - State management
- **React Navigation** - Navigation
- **AsyncStorage** - Data persistence
- **React Native Chart Kit** - Statistics visualization
- **Expo Vector Icons** - Icons

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Run on iOS:
```bash
npm run ios
```

4. Run on Android:
```bash
npm run android
```

## Project Structure

```
smart_home_app/
├── App.js                 # Main app entry point
├── index.js              # Expo entry point
├── package.json          # Dependencies
├── src/
│   ├── components/       # Reusable components
│   │   └── DeviceCard.js
│   ├── constants/        # Constants and themes
│   │   └── theme.js
│   ├── navigation/       # Navigation setup
│   │   └── AppNavigator.js
│   ├── screens/          # Screen components
│   │   ├── DashboardScreen.js
│   │   ├── DeviceListScreen.js
│   │   ├── DeviceDetailScreen.js
│   │   ├── AddDeviceScreen.js
│   │   ├── ControllerListScreen.js
│   │   ├── AddControllerScreen.js
│   │   ├── StatisticsScreen.js
│   │   ├── ARScreen.js
│   │   └── VRScreen.js
│   ├── store/            # Redux store
│   │   ├── index.js
│   │   ├── middleware/
│   │   │   └── persistenceMiddleware.js
│   │   └── slices/
│   │       ├── devicesSlice.js
│   │       ├── statisticsSlice.js
│   │       └── themeSlice.js
│   └── utils/            # Utility functions
│       └── storage.js
└── assets/               # Images and assets
```

## Usage

### Adding a Device
1. Navigate to the Devices tab
2. Tap the "+" button
3. Fill in device information (name, type, location)
4. Save the device

### Controlling a Device
1. Go to Dashboard or Devices tab
2. Tap on a device card
3. Use the control buttons (ON, OFF, RUN) or toggle switch
4. View device details and statistics

### Adding a Controller
1. Navigate to the Controllers tab
2. Tap the "+" button
3. Select controller type (Bluetooth, Wi-Fi, etc.)
4. Enter MAC address (for Bluetooth)
5. Save the controller

### Viewing Statistics
1. Navigate to the Statistics tab
2. View usage charts, most used commands, and device statistics
3. Check recent command history

### AR/VR Features
- Navigate to AR or VR tabs
- These are placeholder implementations
- Full implementation would require additional libraries and hardware

## Data Persistence

All data is automatically persisted to AsyncStorage:
- Devices and their states
- Controllers and connection status
- Usage statistics and command history
- Theme preferences (dark/light mode)

## State Management

The app uses Redux Toolkit for state management with three main slices:
- **devicesSlice**: Manages devices and controllers
- **statisticsSlice**: Tracks usage statistics and commands
- **themeSlice**: Handles theme preferences

## Navigation

The app uses React Navigation with:
- Bottom tab navigation for main sections
- Stack navigation for device and controller management
- Deep linking support for device details

## Future Enhancements

- Full AR implementation with device placement
- Complete VR experience with Meta Quest SDK
- Real Bluetooth device scanning and connection
- WebSocket support for real-time updates
- Push notifications for device alerts
- User authentication and cloud sync
- Multiple home support
- Automation and scheduling

## License

This project is open source and available under the MIT License.

