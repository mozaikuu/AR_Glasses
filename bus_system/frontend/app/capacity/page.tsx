"use client";

import { useEffect, useState } from "react";

import {
	getBusCapacity,
	getBusCapacityPrediction,
	getPredictedEta,
} from "@/lib/api";

export default function CapacityPage() {
	const [capacity, setCapacity] = useState<{
		total_seats: number;
		current_passengers: number;
		available_seats: number;
		occupancy_rate: number;
	} | null>(null);
	const [prediction, setPrediction] = useState<{
		total_seats: number;
		predicted_passengers: number;
		predicted_available_seats: number;
		probability_bus_full: number;
	} | null>(null);
	const [eta, setEta] = useState<{
		predicted_eta_minutes: number;
		traffic_level: number;
	} | null>(null);

	async function load() {
		const [cap, pred, etaPred] = await Promise.all([
			getBusCapacity("en"),
			getBusCapacityPrediction("en"),
			getPredictedEta("en"),
		]);
		setCapacity(cap.data);
		setPrediction(pred.data);
		setEta({
			predicted_eta_minutes: etaPred.data.predicted_eta_minutes,
			traffic_level: etaPred.data.traffic_level,
		});
	}

	useEffect(() => {
		void load();
		const timer = window.setInterval(() => {
			void load();
		}, 5000);

		return () => window.clearInterval(timer);
	}, []);

	const occupancy = capacity ? Math.round(capacity.occupancy_rate * 100) : 0;
	const fullProbability = prediction
		? Math.round(prediction.probability_bus_full * 100)
		: 0;

	return (
		<div className="space-y-5">
			<section className="panel rounded-3xl p-6 md:p-8">
				<p className="text-xs uppercase tracking-[0.22em] text-mint-300">
					Capacity Intelligence
				</p>
				<h2 className="mt-2 text-2xl font-semibold">
					Live + Predicted Occupancy Dashboard
				</h2>
				<p className="mt-3 text-sm text-slate-300">
					AI model predicts demand and bus-full probability using synthetic
					historical patterns.
				</p>
			</section>

			<section className="grid gap-5 mobile-stack md:grid-cols-3">
				<article className="panel rounded-3xl p-5">
					<p className="text-xs uppercase tracking-[0.2em] text-slate-400">
						Current Occupancy
					</p>
					<p className="mt-2 text-3xl font-semibold">{occupancy}%</p>
					<div className="mt-4 h-3 rounded-full bg-white/10">
						<div
							className="h-3 rounded-full bg-mint-400 transition-all"
							style={{ width: `${Math.min(100, occupancy)}%` }}
						/>
					</div>
					<p className="mt-3 text-sm text-slate-300">
						{capacity?.current_passengers ?? "--"} /{" "}
						{capacity?.total_seats ?? "--"} passengers
					</p>
				</article>

				<article className="panel rounded-3xl p-5">
					<p className="text-xs uppercase tracking-[0.2em] text-slate-400">
						Predicted Demand
					</p>
					<p className="mt-2 text-3xl font-semibold">
						{prediction?.predicted_passengers ?? "--"}
					</p>
					<p className="mt-3 text-sm text-slate-300">
						Estimated available seats:{" "}
						{prediction?.predicted_available_seats ?? "--"}
					</p>
				</article>

				<article className="panel rounded-3xl p-5">
					<p className="text-xs uppercase tracking-[0.2em] text-slate-400">
						Probability Bus Becomes Full
					</p>
					<p className="mt-2 text-3xl font-semibold">{fullProbability}%</p>
					<div className="mt-4 h-3 rounded-full bg-white/10">
						<div
							className="h-3 rounded-full bg-amber-400 transition-all"
							style={{ width: `${Math.min(100, fullProbability)}%` }}
						/>
					</div>
				</article>
			</section>

			<section className="panel rounded-3xl p-5">
				<h3 className="text-lg font-medium">Prediction Context</h3>
				<dl className="mt-4 grid gap-4 text-sm md:grid-cols-2">
					<div className="rounded-2xl border border-white/10 bg-white/5 p-4">
						<dt className="text-slate-400">Predicted ETA</dt>
						<dd className="mt-1 text-2xl font-semibold">
							{eta?.predicted_eta_minutes ?? "--"} min
						</dd>
					</div>
					<div className="rounded-2xl border border-white/10 bg-white/5 p-4">
						<dt className="text-slate-400">Traffic Level</dt>
						<dd className="mt-1 text-2xl font-semibold">
							{eta?.traffic_level ?? "--"} / 10
						</dd>
					</div>
				</dl>
			</section>
		</div>
	);
}
