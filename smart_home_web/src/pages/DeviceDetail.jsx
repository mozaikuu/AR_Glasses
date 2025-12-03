import { useParams } from "react-router-dom";
import { useDevices } from "../context/DeviceContext.jsx";

const buttonClass =
  "px-3 py-1.5 rounded-md text-sm font-medium border border-slate-700 hover:border-brand-600/70 hover:bg-slate-800";

export default function DeviceDetail() {
  const { id } = useParams();
  const { devices, toggleDevice } = useDevices();

  const device = devices.find((d) => d.id === id);

  if (!device) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="text-lg font-semibold text-white">Device not found</h2>
        <p className="text-sm text-slate-400">
          Please go back to the devices list.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6">
        <h2 className="text-2xl font-semibold text-white">{device.name}</h2>
        <p className="text-sm text-slate-400">
          {device.type} · {device.room}
        </p>

        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            className={`${buttonClass} ${
              device.state === "ON" ? "bg-brand-600 text-white" : ""
            }`}
            onClick={() => toggleDevice(device.id, "ON")}
          >
            Turn ON
          </button>
          <button
            type="button"
            className={`${buttonClass} ${
              device.state === "OFF" ? "bg-slate-800 text-white" : ""
            }`}
            onClick={() => toggleDevice(device.id, "OFF")}
          >
            Turn OFF
          </button>
          <button
            type="button"
            className={`${buttonClass} ${
              device.state === "RUNNING" ? "bg-sky-500/20 text-sky-300" : ""
            }`}
            onClick={() => toggleDevice(device.id, "RUNNING")}
          >
            Set RUNNING
          </button>
          <button
            type="button"
            className={`${buttonClass} ${
              device.state === "MALFUNCTION"
                ? "bg-rose-500/20 text-rose-300"
                : ""
            }`}
            onClick={() => toggleDevice(device.id, "MALFUNCTION")}
          >
            Set MALFUNCTION
          </button>
        </div>
      </div>
    </div>
  );
}


