import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
 CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { useDevices } from "../context/DeviceContext.jsx";

const COLORS = ["#22c55e", "#0ea5e9", "#f97316", "#f43f5e", "#a855f7"];

export default function UsageStatsDashboard() {
  const { devices, logs } = useDevices();

  const perDeviceData = useMemo(() => {
    const usage = {};
    logs.forEach((log) => {
      if (log.type !== "Action") return;
      usage[log.deviceName] = (usage[log.deviceName] || 0) + 1;
    });
    return Object.entries(usage).map(([name, count]) => ({
      name,
      count
    }));
  }, [logs]);

  const timeSeries = useMemo(() => {
    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    return days.map((day) => ({
      day,
      commands: Math.floor(Math.random() * 30) + 5,
      errors: Math.floor(Math.random() * 5)
    }));
  }, []);

  const stateBreakdown = useMemo(() => {
    const counts = {
      ON: 0,
      OFF: 0,
      RUNNING: 0,
      MALFUNCTION: 0
    };
    devices.forEach((device) => {
      counts[device.state] = (counts[device.state] || 0) + 1;
    });
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [devices]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl	font-semibold text-white">
          Usage Statistics Dashboard
        </h2>
        <p className="text-sm text-slate-400">
          Track most used commands, per-device usage, and temporal trends.
        </p>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">
          Daily/Weekly Command Volume
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#1e293b",
                  fontSize: "0.75rem"
                }}
              />
              <Line
                type="monotone"
                dataKey="commands"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="errors"
                stroke="#f43f5e"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">
            Per-device Usage
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={perDeviceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e293b",
                    fontSize: "0.75rem"
                  }}
                />
                <Bar dataKey="count" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">
            Live State Breakdown
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stateBreakdown}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                >
                  {stateBreakdown.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#1e293b",
                    fontSize: "0.75rem"
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </div>
  );
}


