import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDevices } from "../context/DeviceContext.jsx";

export default function RemoveDevice() {
  const { devices, removeDevice } = useDevices();
  const navigate = useNavigate();
  const [selected, setSelected] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selected) return;
    removeDevice(selected);
    navigate("/devices");
  };

  return (
    <div className="max-w-xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <h2 className="text-xl font-semibold text-white">Remove a Device</h2>
      <p className="text-sm text-slate-400">
        Disconnect a device from your network and revoke manual control.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label className="text-sm text-slate-300">Select Device</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-rose-500 focus:outline-none"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">-- choose device --</option>
            {devices.map((device) => (
              <option key={device.id} value={device.id}>
                {device.name} · {device.room}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          className="w-full rounded-md bg-rose-600 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:bg-slate-700"
          disabled={!selected}
        >
          Remove Device
        </button>
      </form>
    </div>
  );
}


