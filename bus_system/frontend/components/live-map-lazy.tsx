"use client";

import dynamic from "next/dynamic";

const LiveMapInner = dynamic(
	() => import("@/components/live-map").then((module) => module.LiveMap),
	{
		ssr: false,
		loading: () => (
			<div className="panel rounded-3xl p-6 text-sm text-slate-300">
				Loading live map...
			</div>
		),
	},
);

export function LiveMapLazy() {
	return <LiveMapInner />;
}
