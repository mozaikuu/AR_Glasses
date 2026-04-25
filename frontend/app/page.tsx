import { LiveMapLazy } from "@/components/live-map-lazy";

export default function HomePage() {
	return (
		<div className="space-y-5">
			<section className="panel rounded-3xl p-6 md:p-8">
				<p className="text-xs uppercase tracking-[0.22em] text-amber-300">
					Live Operations
				</p>
				<h2 className="mt-2 text-2xl font-semibold md:text-3xl">
					Mansoura to NMU Bus Tracking
				</h2>
				<p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-300">
					This dashboard simulates real-time route movement with virtual
					stops, speed variation, passenger flow, incident-based ETA
					impact, and AI-powered predictions using synthetic historical
					data.
				</p>
			</section>

			<LiveMapLazy />
		</div>
	);
}
