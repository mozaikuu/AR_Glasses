import { Link } from "react-router-dom";
import { useDevices } from "../context/DeviceContext.jsx";

export default function Devices() {
  const { devices } = useDevices();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-white">All Devices</h2>
          <p className="text-sm text-slate-400">
            Overview of every connected smart home device.
          </p>
        </div>
        <Link
          to="/devices/add"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Add Device
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {devices.map((device) => (
          <Link
            key={device.id}
            to={`/devices/${device.id}`}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 hover:border-brand-600/60"
          >
            <div className="text-lg font-medium text-slate-100">
              {device.name}
            </div>
            <div className="text-sm text-slate-400">
              {device.type} · {device.room}
            </div>
            <div className="mt-2 text-xs text-slate-500">
              State: <span className="text-slate-200">{device.state}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}


