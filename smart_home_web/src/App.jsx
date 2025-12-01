import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Devices from "./pages/Devices.jsx";
import DeviceDetail from "./pages/DeviceDetail.jsx";
import AddDevice from "./pages/AddDevice.jsx";
import RemoveDevice from "./pages/RemoveDevice.jsx";
import ConnectController from "./pages/ConnectController.jsx";
import DeviceInfoStats from "./pages/DeviceInfoStats.jsx";
import UsageStatsDashboard from "./pages/UsageStatsDashboard.jsx";
import { DeviceProvider } from "./context/DeviceContext.jsx";

const navLinkClasses = ({ isActive }) =>
  [
    "block px-3 py-2 rounded-md text-sm font-medium transition-colors",
    isActive
      ? "bg-brand-600 text-white"
      : "text-slate-300 hover:bg-slate-800 hover:text-white"
  ].join(" ");

export default function App() {
  return (
    <DeviceProvider>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex">
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
          <div className="px-6 py-4 border-b border-slate-800">
            <h1 className="text-lg font-semibold text-white">
              Smart Home Dashboard
            </h1>
          </div>
          <nav className="flex-1 px-3 py-4 space-y-3 text-sm">
            <div className="space-y-1">
              <NavLink to="/" className={navLinkClasses} end>
                Overview
              </NavLink>
              <NavLink to="/devices" className={navLinkClasses}>
                Devices
              </NavLink>
              <NavLink to="/connect-controller" className={navLinkClasses}>
                Connect Controller
              </NavLink>
              <NavLink to="/device-info" className={navLinkClasses}>
                Device Info &amp; Statistics
              </NavLink>
              <NavLink to="/usage-stats" className={navLinkClasses}>
                Usage Statistics
              </NavLink>
            </div>
            <div>
              <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Add / Remove Device
              </p>
              <div className="space-y-1">
                <NavLink to="/devices/add" className={navLinkClasses}>
                  Add Device
                </NavLink>
                <NavLink to="/devices/remove" className={navLinkClasses}>
                  Remove Device
                </NavLink>
              </div>
            </div>
          </nav>
        </aside>
        <main className="flex-1 min-w-0 bg-slate-950">
          <div className="max-w-6xl mx-auto px-6 py-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/devices" element={<Devices />} />
              <Route path="/devices/add" element={<AddDevice />} />
              <Route path="/devices/remove" element={<RemoveDevice />} />
              <Route path="/devices/:id" element={<DeviceDetail />} />
              <Route
                path="/connect-controller"
                element={<ConnectController />}
              />
              <Route path="/device-info" element={<DeviceInfoStats />} />
              <Route path="/usage-stats" element={<UsageStatsDashboard />} />
            </Routes>
          </div>
        </main>
      </div>
    </DeviceProvider>
  );
}


