import { CEREBROAPIClient } from "@/api/client";
import { NavigationStatus } from "@/types/api";
import { useAppStore } from "@/store";
import { configManager } from "@/config";

export class NavigationService {
	private apiClient: CEREBROAPIClient;
	private pollTimer: ReturnType<typeof setInterval> | null = null;

	constructor(apiClient: CEREBROAPIClient) {
		this.apiClient = apiClient;
	}

	async getDestinations(): Promise<void> {
		const store = useAppStore.getState();
		try {
			const response = await this.apiClient.getDestinations();
			store.setDestinations(response.destinations);
			store.setNavigationError(null);
		} catch (error) {
			store.setNavigationError("Failed to load destinations.");
			throw error;
		}
	}

	async startNavigation(destination: string): Promise<void> {
		const store = useAppStore.getState();
		try {
			const response = await this.apiClient.startNavigation({ destination });
			const session: NavigationStatus = {
				session_id: response.session_id,
				destination: response.destination,
				current_step: 1,
				total_steps: response.total_steps,
				next_instruction: response.next_instruction,
				is_complete: false,
			};
			store.setNavigationSession(session);
			store.setNavigating(true);
			store.setNavigationError(null);
			this.startPolling(response.session_id);
		} catch (error) {
			store.setNavigationError("Failed to start navigation.");
			throw error;
		}
	}

	async stopNavigation(): Promise<void> {
		const store = useAppStore.getState();
		const session = store.navigationSession;
		if (!session) {
			store.setNavigating(false);
			return;
		}

		try {
			await this.apiClient.stopNavigation(session.session_id);
			store.setNavigationError(null);
		} catch {
			store.setNavigationError("Failed to stop navigation.");
		} finally {
			this.stopPolling();
			store.setNavigating(false);
			store.setNavigationSession(null);
		}
	}

	async nextStep(): Promise<void> {
		const store = useAppStore.getState();
		const session = store.navigationSession;
		if (!session) {
			return;
		}

		try {
			const response = await this.apiClient.nextNavigationStep(
				session.session_id,
			);
			const updated: NavigationStatus = {
				...session,
				current_step: response.current_step,
				next_instruction: response.next_instruction,
				is_complete: response.is_complete,
			};
			store.setNavigationSession(updated);
			store.setNavigationError(null);
			if (response.is_complete) {
				this.stopPolling();
			}
		} catch {
			store.setNavigationError("Failed to advance navigation step.");
		}
	}

	private startPolling(sessionId: string): void {
		this.stopPolling();
		const pollInterval = configManager.getNavigationPollIntervalMs();

		this.pollTimer = setInterval(async () => {
			const store = useAppStore.getState();
			try {
				const status = await this.apiClient.getNavigationStatus(sessionId);
				store.setNavigationSession(status);
				store.setNavigationError(null);
				if (status.is_complete) {
					this.stopPolling();
				}
			} catch {
				store.setNavigationError("Navigation status update failed.");
			}
		}, pollInterval);
	}

	private stopPolling(): void {
		if (this.pollTimer) {
			clearInterval(this.pollTimer);
			this.pollTimer = null;
		}
	}
}
