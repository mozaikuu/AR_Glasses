import type { Metadata, Viewport } from "next";
import { Space_Grotesk, Tajawal } from "next/font/google";

import { MainNav } from "@/components/main-nav";
import { PwaNotifier } from "@/components/pwa-notifier";

import "./globals.css";

const displayFont = Space_Grotesk({
	subsets: ["latin"],
	variable: "--font-display",
});

const arabicFont = Tajawal({
	subsets: ["arabic", "latin"],
	weight: ["400", "500", "700"],
	variable: "--font-arabic",
});

export const metadata: Metadata = {
	title: "NMU Smart Bus Tracker",
	description:
		"Smart University Bus Tracking prototype for Cerebro Smart Glasses",
	manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
	themeColor: "#0a1725",
};

export default function RootLayout({
	children,
}: Readonly<{ children: React.ReactNode }>) {
	return (
		<html lang="en">
			<body
				className={`${displayFont.variable} ${arabicFont.variable} min-h-screen`}
			>
				<div className="mx-auto w-full max-w-7xl px-4 pb-8 pt-6 md:px-8">
					<header className="panel rounded-3xl px-5 py-5 md:px-8">
						<div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
							<div>
								<p className="text-xs uppercase tracking-[0.24em] text-mint-300">
									Cerebro x NMU
								</p>
								<h1 className="mt-2 text-2xl font-semibold md:text-3xl">
									<span className="gradient-text">
										Smart University Bus Tracking MVP
									</span>
								</h1>
								<p className="mt-2 max-w-2xl text-sm text-slate-300">
									Real-time simulation, AI prediction, wallet flows,
									and bilingual assistant-ready endpoints.
								</p>
							</div>
							<MainNav />
						</div>
					</header>

					<main className="mt-6">{children}</main>
				</div>
				<PwaNotifier />
			</body>
		</html>
	);
}
