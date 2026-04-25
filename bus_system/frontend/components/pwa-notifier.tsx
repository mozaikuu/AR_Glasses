"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, Smartphone } from "lucide-react";

import { getPredictedEta } from "@/lib/api";

export function PwaNotifier() {
	const [permission, setPermission] =
		useState<NotificationPermission>("default");
	const [canInstall, setCanInstall] = useState(false);
	const installPromptRef = useRef<Event | null>(null);
	const lastNotifiedAtRef = useRef<number>(0);

	useEffect(() => {
		if ("serviceWorker" in navigator) {
			void navigator.serviceWorker.register("/sw.js");
		}

		if ("Notification" in window) {
			setPermission(Notification.permission);
		}

		const beforeInstallPromptHandler = (event: Event) => {
			event.preventDefault();
			installPromptRef.current = event;
			setCanInstall(true);
		};

		window.addEventListener(
			"beforeinstallprompt",
			beforeInstallPromptHandler,
		);
		return () =>
			window.removeEventListener(
				"beforeinstallprompt",
				beforeInstallPromptHandler,
			);
	}, []);

	useEffect(() => {
		if (permission !== "granted") {
			return;
		}

		const timer = window.setInterval(async () => {
			try {
				const eta = await getPredictedEta("en");
				const minutes = eta.data.predicted_eta_minutes;
				const now = Date.now();

				if (
					minutes <= 15 &&
					now - lastNotifiedAtRef.current > 12 * 60 * 1000
				) {
					const title = "Bus arriving soon";
					const body = `Predicted arrival in ${Math.round(minutes)} minutes.`;

					if (navigator.serviceWorker?.controller) {
						const registration = await navigator.serviceWorker.ready;
						await registration.showNotification(title, {
							body,
							icon: "/icons/icon-192.svg",
						});
					} else {
						new Notification(title, {
							body,
							icon: "/icons/icon-192.svg",
						});
					}
					lastNotifiedAtRef.current = now;
				}
			} catch {
				// Ignore polling failures in prototype mode.
			}
		}, 60_000);

		return () => window.clearInterval(timer);
	}, [permission]);

	async function enableNotifications() {
		if (!("Notification" in window)) {
			return;
		}
		const status = await Notification.requestPermission();
		setPermission(status);
	}

	async function installApp() {
		const promptEvent = installPromptRef.current as
			| (Event & {
					prompt?: () => Promise<void>;
					userChoice?: Promise<{ outcome: "accepted" | "dismissed" }>;
			  })
			| null;

		if (!promptEvent?.prompt) {
			return;
		}

		await promptEvent.prompt();
		if (promptEvent.userChoice) {
			await promptEvent.userChoice;
		}

		installPromptRef.current = null;
		setCanInstall(false);
	}

	return (
		<div className="fixed bottom-4 right-4 z-50 space-y-2">
			<button
				type="button"
				onClick={enableNotifications}
				className="panel flex items-center gap-2 rounded-full px-4 py-2 text-xs text-slate-100 transition hover:bg-white/10"
			>
				<Bell size={15} />
				{permission === "granted"
					? "Alerts Enabled"
					: "Enable Arrival Alerts"}
			</button>

			{canInstall ? (
				<button
					type="button"
					onClick={installApp}
					className="panel flex items-center gap-2 rounded-full px-4 py-2 text-xs text-slate-100 transition hover:bg-white/10"
				>
					<Smartphone size={15} />
					Install Mobile App
				</button>
			) : null}
		</div>
	);
}
