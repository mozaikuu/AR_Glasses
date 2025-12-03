import React, { createContext, useContext, useMemo, useState } from "react";

const DeviceContext = createContext(null);

const initialDevices = [
  { id: "1", name: "Living Room Lamp", type: "Light", state: "ON", room: "Living Room" },
  { id: "2", name: "Bedroom AC", type: "Climate", state: "RUNNING", room: "Bedroom" },
  { id: "3", name: "Front Door Lock", type: "Security", state: "OFF", room: "Entrance" },
  { id: "4", name: "Garage Sensor", type: "Sensor", state: "MALFUNCTION", room: "Garage" }
];

export function DeviceProvider({ children }) {
  const [devices, setDevices] = useState(initialDevices);
  const [logs, setLogs] = useState([]);

  // Toggle device state manually
  const toggleDevice = (id, targetState) => {
    setDevices((prev) =>
      prev.map((d) => (d.id === id ? { ...d, state: targetState } : d))
    );
    const device = devices.find((d) => d.id === id);
    if (device) {
      setLogs((prev) => [
        {
          id: `${Date.now()}`,
          deviceId: device.id,
          deviceName: device.name,
          type: "Action",
          message: `Manually set to ${targetState}`,
          timestamp: new Date().toISOString()
        },
        ...prev
      ]);
    }
  };

  // Add a new device
  const addDevice = (device) => {
    setDevices((prev) => [...prev, device]);
    setLogs((prev) => [
      {
        id: `${Date.now()}`,
        deviceId: device.id,
        deviceName: device.name,
        type: "Action",
        message: "Device added",
        timestamp: new Date().toISOString()
      },
      ...prev
    ]);
  };

  // Remove an existing device
  const removeDevice = (id) => {
    const device = devices.find((d) => d.id === id);
    setDevices((prev) => prev.filter((d) => d.id !== id));
    if (device) {
      setLogs((prev) => [
        {
          id: `${Date.now()}`,
          deviceId: device.id,
          deviceName: device.name,
          type: "Action",
          message: "Device removed",
          timestamp: new Date().toISOString()
        },
        ...prev
      ]);
    }
  };

  const value = useMemo(
    () => ({
      devices,
      logs,
      toggleDevice,
      addDevice,
      removeDevice
    }),
    [devices, logs]
  );

  return <DeviceContext.Provider value={value}>{children}</DeviceContext.Provider>;
}

export function useDevices() {
  const ctx = useContext(DeviceContext);
  if (!ctx) throw new Error("useDevices must be used within DeviceProvider");
  return ctx;
}
