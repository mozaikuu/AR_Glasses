import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  commandHistory: [],
  deviceUsage: {},
  mostUsedCommands: [],
  applianceInfo: {},
};

const statisticsSlice = createSlice({
  name: 'statistics',
  initialState,
  reducers: {
    addCommand: (state, action) => {
      const command = {
        id: Date.now().toString(),
        ...action.payload,
        timestamp: new Date().toISOString(),
      };
      state.commandHistory.push(command);
      
      // Update command count
      const commandKey = `${action.payload.deviceId}_${action.payload.action}`;
      if (!state.deviceUsage[commandKey]) {
        state.deviceUsage[commandKey] = 0;
      }
      state.deviceUsage[commandKey] += 1;
      
      // Update most used commands
      state.mostUsedCommands = Object.entries(state.deviceUsage)
        .map(([key, count]) => {
          const [deviceId, action] = key.split('_');
          return { deviceId, action, count };
        })
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);
    },
    updateApplianceInfo: (state, action) => {
      const { deviceId, info } = action.payload;
      state.applianceInfo[deviceId] = {
        ...state.applianceInfo[deviceId],
        ...info,
        lastUpdated: new Date().toISOString(),
      };
    },
    setStatistics: (state, action) => {
      return { ...state, ...action.payload };
    },
  },
});

export const {
  addCommand,
  updateApplianceInfo,
  setStatistics,
} = statisticsSlice.actions;

export default statisticsSlice.reducer;

