import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  devices: [],
  controllers: [],
  loading: false,
  error: null,
};

const devicesSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    addDevice: (state, action) => {
      const newDevice = {
        id: Date.now().toString(),
        ...action.payload,
        state: action.payload.state || 'OFF',
        createdAt: new Date().toISOString(),
        usageCount: 0,
      };
      state.devices.push(newDevice);
    },
    removeDevice: (state, action) => {
      state.devices = state.devices.filter(device => device.id !== action.payload);
    },
    updateDeviceState: (state, action) => {
      const { id, state: newState } = action.payload;
      const device = state.devices.find(d => d.id === id);
      if (device) {
        device.state = newState;
        device.lastUpdated = new Date().toISOString();
        if (newState === 'ON' || newState === 'RUNNING') {
          device.usageCount = (device.usageCount || 0) + 1;
        }
      }
    },
    addController: (state, action) => {
      const newController = {
        id: Date.now().toString(),
        ...action.payload,
        connected: false,
        createdAt: new Date().toISOString(),
      };
      state.controllers.push(newController);
    },
    removeController: (state, action) => {
      state.controllers = state.controllers.filter(controller => controller.id !== action.payload);
    },
    updateControllerConnection: (state, action) => {
      const { id, connected } = action.payload;
      const controller = state.controllers.find(c => c.id === id);
      if (controller) {
        controller.connected = connected;
      }
    },
    setDevices: (state, action) => {
      state.devices = action.payload;
    },
    setControllers: (state, action) => {
      state.controllers = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    addCommand: (state, action) => {
      // This action is handled by statisticsSlice, but kept here for compatibility
      // The actual implementation is in statisticsSlice
    },
  },
});

export const {
  addDevice,
  removeDevice,
  updateDeviceState,
  addController,
  removeController,
  updateControllerConnection,
  setDevices,
  setControllers,
  setLoading,
  setError,
  addCommand,
} = devicesSlice.actions;

export default devicesSlice.reducer;

