"use client";

import "leaflet/dist/leaflet.css";

import { useEffect, useMemo, useState } from "react";
import {
	CircleMarker,
	MapContainer,
	Polyline,
	Popup,
	TileLayer,
} from "react-leaflet";

import { backendBaseUrl, BusLocationData, getBusLocation } from "@/lib/api";

const fallbackRoute: Array<[number, number]> = [
	[31.0409, 31.3785],
	[31.1183, 31.2615],
	[31.2301, 31.112],
	[31.3368, 30.9964],
	[31.4314, 30.895],
	[31.4849, 30.8404],
];

export function LiveMap() {
	const [data, setData] = useState<BusLocationData | null>(null);
	const [lastError, setLastError] = useState<string | null>(null);

	const routePoints = useMemo(() => {
		if (!data?.route_points?.length) {
			return fallbackRoute;
		}
		return data.route_points.map(
			(point) => [point.lat, point.lng] as [number, number],
		);
	}, [data]);

	async function loadFromApi() {
		try {
			const result = await getBusLocation("en");
			setData(result.data);
			setLastError(null);
		} catch (error) {
			setLastError(
				error instanceof Error
					? error.message
					: "Unable to fetch bus location",
			);
		}
	}

	useEffect(() => {
		void loadFromApi();
		const timer = window.setInterval(() => {
			void loadFromApi();
		}, 5000);

		return () => window.clearInterval(timer);
	}, []);

	useEffect(() => {
		const httpBase = backendBaseUrl();
		const wsBase = httpBase.startsWith("https")
			? httpBase.replace("https", "wss")
			: httpBase.replace("http", "ws");

		const ws = new WebSocket(`${wsBase}/ws/bus`);

		ws.onmessage = (event) => {
			try {
				const payload = JSON.parse(event.data) as {
					event?: string;
					payload?: BusLocationData;
				};

				if (payload.payload) {
					setData(payload.payload);
				}
			} catch {
				// Keep polling fallback active.
			}
		};

		return () => ws.close();
	}, []);

	const center =
		data?.location?.lat && data?.location?.lng
			? ([data.location.lat, data.location.lng] as [number, number])
			: routePoints[0];

	return (
		<section className="grid gap-5 mobile-stack md:grid-cols-[2.2fr_1fr]">
			<div className="panel overflow-hidden rounded-3xl p-3 md:p-4">
				<MapContainer
					center={center}
					zoom={9}
					scrollWheelZoom
					style={{ height: 500, width: "100%", borderRadius: 20 }}
				>
					<TileLayer
						attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
						url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					/>

					<Polyline
						positions={routePoints}
						pathOptions={{ color: "#2dd4bf", weight: 6 }}
					/>

					{data?.stops?.map((stop) => {
						const point = routePoints[stop.index];
						if (!point) {
							return null;
						}

						return (
							<CircleMarker
								key={stop.name}
								center={point}
								radius={6}
								pathOptions={{
									color: "#fcd48a",
									fillColor: "#f59e0b",
									fillOpacity: 0.95,
								}}
							>
								<Popup>{stop.name}</Popup>
							</CircleMarker>
						);
					})}

					{data?.location ? (
						<CircleMarker
							center={[data.location.lat, data.location.lng]}
							radius={12}
							pathOptions={{
								color: "#fff",
								fillColor: "#f97316",
								fillOpacity: 1,
							}}
						>
							<Popup>
								<div className="text-sm">
									<p className="font-semibold">NMU Bus Route #1</p>
									<p>Status: {data.status}</p>
									<p>Speed: {data.speed_kmh} km/h</p>
								</div>
							</Popup>
						</CircleMarker>
					) : null}
				</MapContainer>
			</div>

			<aside className="space-y-4">
				<div className="panel rounded-3xl p-5">
					<p className="text-xs uppercase tracking-[0.2em] text-mint-300">
						Live Telemetry
					</p>
					<h2 className="mt-2 text-xl font-semibold">NMU Bus Route #1</h2>
					<p className="mt-2 text-sm text-slate-300">
						{data?.status ?? "Loading bus status..."}
					</p>

					<dl className="mt-5 space-y-3 text-sm">
						<div className="flex items-center justify-between">
							<dt className="text-slate-400">Speed</dt>
							<dd>{data?.speed_kmh ?? "--"} km/h</dd>
						</div>
						<div className="flex items-center justify-between">
							<dt className="text-slate-400">Estimated ETA</dt>
							<dd>{data?.estimated_eta_minutes ?? "--"} min</dd>
						</div>
						<div className="flex items-center justify-between">
							<dt className="text-slate-400">Current Passengers</dt>
							<dd>{data?.current_passengers ?? "--"}</dd>
						</div>
						<div className="flex items-center justify-between">
							<dt className="text-slate-400">Occupancy</dt>
							<dd>
								{data ? Math.round(data.occupancy_rate * 100) : "--"}%
							</dd>
						</div>
						<div className="flex items-center justify-between">
							<dt className="text-slate-400">Next Stop</dt>
							<dd className="max-w-[11rem] text-right">
								{data?.next_stop ?? "--"}
							</dd>
						</div>
					</dl>
				</div>

				<div className="panel rounded-3xl p-5">
					<p className="text-xs uppercase tracking-[0.2em] text-amber-300">
						AI Readiness
					</p>
					<p className="mt-2 text-sm text-slate-300">
						Backend exposes bilingual EN/AR responses and real-time
						websocket feed for Cerebro tools.
					</p>
					{lastError ? (
						<p className="mt-3 rounded-lg border border-rose-300/35 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
							{lastError}
						</p>
					) : null}
				</div>
			</aside>
		</section>
	);
}
