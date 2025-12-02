import { Link } from "react-router-dom";
import { useDevices } from "../context/DeviceContext.jsx";

function stateBadgeColor(state) {
  switch (state) {
    case "ON":
      return "bg-emerald-500/20 text-emerald-300 border-emerald-500/50";
    case "OFF":
      return "bg-slate-700/40 text-slate-200 border-slate-500/60";
    case "RUNNING":
      return "bg-sky-500/20 text-sky-300 border-sky-500/50";
    case "MALFUNCTION":
      return "bg-rose-500/20 text-rose-300 border-rose-500/60";
    default:
      return "bg-slate-700/40 text-slate-200 border-slate-500/60";
  }
}

export default function Dashboard() {
  const { devices, logs } = useDevices();
  const total = devices.length;
  const counts = devices.reduce(
    (acc, d) => {
      acc[d.state] = (acc[d.state] || 0) + 1;
      return acc;
    },
    { ON: 0, OFF: 0, RUNNING: 0, MALFUNCTION: 0 }
  );

  const latestLogs = logs.slice(0, 6);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-white">
            Home Overview
          </h2>
          <p className="text-sm text-slate-400">
            Live status of all connected devices, recent activity, and quick
            navigation.
          </p>
        </div>
        <Link
          to="/devices"
          className="inline-flex items-center rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          View all devices
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Devices" value={total} />
        <StatCard label="On" value={counts.ON} tone="on" />
        <StatCard label="Running" value={counts.RUNNING} tone="running" />
        <StatCard label="Malfunction" value={counts.MALFUNCTION} tone="error" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-100">
              Live Device States
            </h3>
            <span className="text-xs text-slate-500">
              Updates automatically
            </span>
          </div>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1 custom-scroll">
            {devices.map((d) => (
              <Link
                key={d.id}
                to={`/devices/${d.id}`}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/40 px-3 py-2 text-sm hover:border-brand-600/70 hover:bg-slate-900/80"
              >
                <div>
                  <div className="font-medium text-slate-100">{d.name}</div>
                  <div className="text-xs text-slate-500">
                    {d.type} · {d.room}
                  </div>
                </div>
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${stateBadgeColor(
                    d.state
                  )}`}
                >
                  {d.state}
                </span>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-100">
              Recent Activity
            </h3>
            <Link
              to="/device-info"
              className="text-xs text-brand-400 hover:text-brand-300"
            >
              View logs
            </Link>
          </div>

          <div className="space-y-3 max-h-72 overflow-y-auto pr-1 custom-scroll">
            {latestLogs.length === 0 && (
              <div className="text-xs text-slate-500">
                No activity yet. Try toggling a device.
              </div>
            )}
            {latestLogs.map((log) => (
              <div
                key={log.id}
                className="border-l-2 border-slate-700 pl-3 text-xs"
              >
                <div className="flex justify-between">
                  <span className="font-medium text-slate-200">
                    {log.deviceName}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-slate-400">{log.message}</div>
                <div className="mt-0.5 text-[10px] text-slate-500">
                  {log.type}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, tone }) {
  const color =
    tone === "on"
      ? "text-emerald-400"
      : tone === "running"
      ? "text-sky-400"
      : tone === "error"
      ? "text-rose-400"
      : "text-slate-100";
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="text-xs text-slate-400">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}


