import axios, { AxiosInstance } from "axios";
import {
	AudioDevicesResponse,
	DestinationsResponse,
	NavigationNextResponse,
	NavigationStartRequest,
	NavigationStartResponse,
	NavigationStatus,
	NavigationStopResponse,
	ProcessRequest,
	ProcessResponse,
} from "@/types/api";

export type APIClientOptions = {
	baseURL: string;
	apiKey?: string | null;
	timeoutMs?: number;
};

export class CEREBROAPIClient {
	private client: AxiosInstance;
	private apiKey?: string | null;

	constructor(options: APIClientOptions) {
		this.apiKey = options.apiKey ?? null;
		this.client = axios.create({
			baseURL: options.baseURL,
			timeout: options.timeoutMs ?? 15000,
		});
	}

	setAPIKey(apiKey: string | null): void {
		this.apiKey = apiKey;
	}

	setBaseURL(baseURL: string): void {
		this.client.defaults.baseURL = baseURL;
	}

	private buildHeaders(): Record<string, string> {
		if (!this.apiKey) {
			return {};
		}

		return {
			"X-API-Key": this.apiKey,
		};
	}

	async healthCheck(): Promise<void> {
		await this.client.get("/", { headers: this.buildHeaders() });
	}

	async process(payload: ProcessRequest): Promise<ProcessResponse> {
		const response = await this.client.post<ProcessResponse>(
			"/process",
			payload,
			{
				headers: this.buildHeaders(),
			},
		);
		return response.data;
	}

	async getAudioDevices(): Promise<AudioDevicesResponse> {
		const response = await this.client.get<AudioDevicesResponse>(
			"/audio/devices",
			{
				headers: this.buildHeaders(),
			},
		);
		return response.data;
	}

	async getDestinations(): Promise<DestinationsResponse> {
		const response = await this.client.get<DestinationsResponse>(
			"/navigation/destinations",
			{
				headers: this.buildHeaders(),
			},
		);
		return response.data;
	}

	async startNavigation(
		request: NavigationStartRequest,
	): Promise<NavigationStartResponse> {
		const response = await this.client.post<NavigationStartResponse>(
			"/navigation/start",
			request,
			{
				headers: this.buildHeaders(),
			},
		);
		return response.data;
	}

	async getNavigationStatus(sessionId: string): Promise<NavigationStatus> {
		const response = await this.client.get<NavigationStatus>(
			"/navigation/status",
			{
				headers: this.buildHeaders(),
				params: { session_id: sessionId },
			},
		);
		return response.data;
	}

	async nextNavigationStep(
		sessionId: string,
	): Promise<NavigationNextResponse> {
		const response = await this.client.post<NavigationNextResponse>(
			"/navigation/next",
			{ session_id: sessionId },
			{ headers: this.buildHeaders() },
		);
		return response.data;
	}

	async stopNavigation(sessionId: string): Promise<NavigationStopResponse> {
		const response = await this.client.post<NavigationStopResponse>(
			"/navigation/stop",
			{ session_id: sessionId },
			{ headers: this.buildHeaders() },
		);
		return response.data;
	}
}
