import { configureStore } from '@reduxjs/toolkit';
import devicesReducer from './slices/devicesSlice';
import statisticsReducer from './slices/statisticsSlice';
import themeReducer from './slices/themeSlice';
import { persistenceMiddleware } from './middleware/persistenceMiddleware';

export const store = configureStore({
  reducer: {
    devices: devicesReducer,
    statistics: statisticsReducer,
    theme: themeReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(persistenceMiddleware),
});

