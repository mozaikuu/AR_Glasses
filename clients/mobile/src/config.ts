export type ConfigValues = {
	backendURL: string;
	apiKey: string | null;
	navigationPollIntervalMs: number;
};

class ConfigManager {
	private config: ConfigValues = {
		backendURL: "http://127.0.0.1:8000",
		apiKey: null,
		navigationPollIntervalMs: 500,
	};

	getBackendURL(): string {
		return this.config.backendURL;
	}

	setBackendURL(url: string): void {
		this.config.backendURL = url.trim();
	}

	getAPIKey(): string | null {
		return this.config.apiKey;
	}

	setAPIKey(key: string | null): void {
		this.config.apiKey = key && key.trim().length > 0 ? key.trim() : null;
	}

	getNavigationPollIntervalMs(): number {
		return this.config.navigationPollIntervalMs;
	}

	setNavigationPollIntervalMs(ms: number): void {
		this.config.navigationPollIntervalMs = Math.max(250, ms);
	}
}

export const configManager = new ConfigManager();
