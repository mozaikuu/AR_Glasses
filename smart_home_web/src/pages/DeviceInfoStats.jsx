import { useDevices } from "../context/DeviceContext.jsx";

export default function DeviceInfoStats() {
  const { devices, logs } = useDevices();
  const history = logs.filter((log) => log.type === "Action").slice(0, 10);
  const errors = logs.filter((log) => log.type === "Error").slice(0, 10);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">
          Device Info &amp; Statistics
        </h2>
        <p className="text-sm text-slate-400">
          Live overview, action history, and error monitoring.
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">
          Device Snapshot
        </h3>
        <div className="grid gap-3 md:grid-cols-2">
          {devices.map((device) => (
            <div
              key={device.id}
              className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 text-sm"
            >
              <div className="font-medium text-slate-100">{device.name}</div>
              <div className="text-slate-400">
                {device.type} · {device.room}
              </div>
              <div className="text-xs text-slate-500">
                Current state: {device.state}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <LogPanel title="Usage History" entries={history} empty="No actions yet." />
        <LogPanel title="Error Logs" entries={errors} empty="No errors. All good!" />
      </section>
    </div>
  );
}

function LogPanel({ title, entries, empty }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="text-sm font-semibold text-slate-200 mb-3">{title}</h3>
      <div className="space-y-2 text-xs text-slate-400 max-h-72 overflow-y-auto">
        {entries.length === 0 && (
          <div className="text-slate-500">{empty}</div>
        )}
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="rounded-lg border border-slate-800 bg-slate-950/40 p-3"
          >
            <div className="font-medium text-slate-200">
              {entry.deviceName}
            </div>
            <div>{entry.message}</div>
            <div className="text-[10px] text-slate-500">
              {new Date(entry.timestamp).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


