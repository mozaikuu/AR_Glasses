import { useState } from "react";

const states = ["PAIRING", "SCANNING", "CONNECTED", "FAILED"];

export default function ConnectController() {
  const [status, setStatus] = useState("IDLE");
  const [log, setLog] = useState([]);

  const handlePair = () => {
    setStatus("SCANNING");
    setLog((prev) => [
      { id: Date.now(), message: "Scanning for Bluetooth controllers..." },
      ...prev
    ]);

    setTimeout(() => {
      setStatus("PAIRING");
      setLog((prev) => [
        { id: Date.now(), message: "Pairing with SmartHub-01..." },
        ...prev
      ]);
    }, 1500);

    setTimeout(() => {
      const next = Math.random() > 0.2 ? "CONNECTED" : "FAILED";
      setStatus(next);
      setLog((prev) => [
        {
          id: Date.now(),
          message:
            next === "CONNECTED"
              ? "Controller connected successfully."
              : "Pairing failed. Please retry."
        },
        ...prev
      ]);
    }, 4000);
  };

  return (
    <div className="max-w-2xl space-y-6 rounded-xl border border-slate-800 bg-slate-900/60 p-6">
      <div>
        <h2 className="text-2xl font-semibold text-white">Connect Controller</h2>
        <p className="text-sm text-slate-400">
          Pair a Bluetooth module to manage devices locally.
        </p>
      </div>

      <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-4 text-sm">
        <div className="text-slate-400">Current Status</div>
        <div className="text-xl font-semibold text-white">{status}</div>
      </div>

      <button
        type="button"
        onClick={handlePair}
        className="w-full rounded-md bg-brand-600 py-2 text-sm font-medium text-white hover:bg-brand-700"
      >
        {status === "CONNECTED" ? "Re-scan controllers" : "Start pairing"}
      </button>

      <div>
        <h3 className="text-sm font-semibold text-slate-200">
          Pairing Activity
        </h3>
        <div className="mt-2 max-h-64 overflow-y-auto space-y-2 text-xs text-slate-400">
          {log.map((entry) => (
            <div
              key={entry.id}
              className="rounded-md border border-slate-800 bg-slate-900/50 px-3 py-2"
            >
              {entry.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


