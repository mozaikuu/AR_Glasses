import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDevices } from "../context/DeviceContext.jsx";

export default function AddDevice() {
  const { addDevice } = useDevices();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    type: "Light",
    room: "",
    state: "OFF"
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.room.trim()) return;

    addDevice({
      id: `${Date.now()}`,
      ...form
    });
    navigate("/devices");
  };

  return (
    <div className="max-w-xl rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <h2 className="text-xl font-semibold text-white">Add a Device</h2>
      <p className="text-sm text-slate-400">
        Connect a new device to your smart home controller.
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label className="text-sm text-slate-300">Device Name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-sm text-slate-300">Type</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
          >
            <option>Light</option>
            <option>Climate</option>
            <option>Security</option>
            <option>Sensor</option>
            <option>Appliance</option>
          </select>
        </div>
        <div>
          <label className="text-sm text-slate-300">Location / Room</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
            value={form.room}
            onChange={(e) => setForm({ ...form, room: e.target.value })}
            required
          />
        </div>
        <div>
          <label className="text-sm text-slate-300">Initial State</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white focus:border-brand-500 focus:outline-none"
            value={form.state}
            onChange={(e) => setForm({ ...form, state: e.target.value })}
          >
            <option>OFF</option>
            <option>ON</option>
            <option>RUNNING</option>
            <option>MALFUNCTION</option>
          </select>
        </div>
        <button
          type="submit"
          className="w-full rounded-md bg-brand-600 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Add Device
        </button>
      </form>
    </div>
  );
}


