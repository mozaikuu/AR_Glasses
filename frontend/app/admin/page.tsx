"use client";

import { FormEvent, useEffect, useState } from "react";

import { getActiveReports, postIncident } from "@/lib/api";

const incidentOptions = [
	"traffic_jam",
	"bus_full",
	"breakdown",
	"early_arrival",
	"delay",
] as const;

export default function AdminPage() {
	const [incidentType, setIncidentType] =
		useState<(typeof incidentOptions)[number]>("delay");
	const [description, setDescription] = useState(
		"Heavy traffic near highway gate",
	);
	const [etaImpact, setEtaImpact] = useState(8);
	const [reports, setReports] = useState<Array<Record<string, unknown>>>([]);
	const [feedback, setFeedback] = useState<string>("");

	async function loadReports() {
		const result = await getActiveReports("en");
		setReports(result.data.incidents);
	}

	useEffect(() => {
		void loadReports();
		const timer = window.setInterval(() => {
			void loadReports();
		}, 6000);

		return () => window.clearInterval(timer);
	}, []);

	async function submitIncident(event: FormEvent) {
		event.preventDefault();

		const response = await postIncident(
			{
				reporter_role: "driver",
				reporter_name: "Admin Dashboard",
				incident_type: incidentType,
				description,
				eta_impact_minutes: etaImpact,
			},
			"en",
		);

		setFeedback(response.message);
		await loadReports();
	}

	return (
		<div className="space-y-5">
			<section className="panel rounded-3xl p-6 md:p-8">
				<p className="text-xs uppercase tracking-[0.22em] text-amber-300">
					Admin Operations
				</p>
				<h2 className="mt-2 text-2xl font-semibold">
					Incident Reporting + Live Monitoring
				</h2>
				<p className="mt-3 text-sm text-slate-300">
					Reports submitted here immediately affect ETA calculations across
					the system and agent tools.
				</p>
			</section>

			<section className="grid gap-5 mobile-stack md:grid-cols-[1fr_1.4fr]">
				<form className="panel rounded-3xl p-5" onSubmit={submitIncident}>
					<h3 className="text-lg font-medium">Report New Incident</h3>

					<label className="mt-4 block text-xs uppercase tracking-[0.16em] text-slate-400">
						Incident type
					</label>
					<select
						className="mt-2 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
						value={incidentType}
						onChange={(event) =>
							setIncidentType(
								event.target.value as (typeof incidentOptions)[number],
							)
						}
					>
						{incidentOptions.map((item) => (
							<option key={item} value={item}>
								{item}
							</option>
						))}
					</select>

					<label className="mt-4 block text-xs uppercase tracking-[0.16em] text-slate-400">
						Description
					</label>
					<textarea
						className="mt-2 min-h-24 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
						value={description}
						onChange={(event) => setDescription(event.target.value)}
					/>

					<label className="mt-4 block text-xs uppercase tracking-[0.16em] text-slate-400">
						ETA impact (minutes)
					</label>
					<input
						type="number"
						min={-10}
						max={60}
						className="mt-2 w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm"
						value={etaImpact}
						onChange={(event) => setEtaImpact(Number(event.target.value))}
					/>

					<button
						type="submit"
						className="mt-4 rounded-xl bg-amber-500/80 px-4 py-2 text-sm font-semibold text-black transition hover:bg-amber-300"
					>
						Submit Report
					</button>

					{feedback ? (
						<p className="mt-3 rounded-xl border border-mint-300/40 bg-mint-400/10 px-3 py-2 text-sm text-mint-100">
							{feedback}
						</p>
					) : null}
				</form>

				<div className="panel rounded-3xl p-5">
					<h3 className="text-lg font-medium">Active Reports</h3>
					<div className="mt-4 space-y-3">
						{reports.length === 0 ? (
							<p className="text-sm text-slate-300">
								No active incidents right now.
							</p>
						) : (
							reports.slice(0, 12).map((report, index) => (
								<article
									key={`${String(report.id ?? "sim")}-${index}`}
									className="rounded-2xl border border-white/10 bg-white/5 p-4"
								>
									<div className="flex items-center justify-between gap-3">
										<h4 className="text-sm font-semibold capitalize text-amber-200">
											{String(report.incident_type ?? "incident")}
										</h4>
										<span className="rounded-full bg-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.12em] text-slate-300">
											{String(report.source ?? "reported")}
										</span>
									</div>
									<p className="mt-2 text-sm text-slate-200">
										{String(report.description ?? "No details")}
									</p>
									<p className="mt-2 text-xs text-slate-400">
										ETA impact:{" "}
										{String(report.eta_impact_minutes ?? 0)} minutes
									</p>
								</article>
							))
						)}
					</div>
				</div>
			</section>
		</div>
	);
}
