import { useEffect, useMemo } from "react";
import { configManager } from "@/config";
import { CEREBROAPIClient } from "@/api/client";
import { AudioService } from "@/services/AudioService";
import { CameraService } from "@/services/CameraService";
import { NavigationService } from "@/services/NavigationService";
import { VoiceService } from "@/services/VoiceService";

export type ServiceBundle = {
	apiClient: CEREBROAPIClient;
	audioService: AudioService;
	cameraService: CameraService;
	navigationService: NavigationService;
	voiceService: VoiceService;
};

let cachedServices: ServiceBundle | null = null;

export const initializeServices = (): ServiceBundle => {
	if (cachedServices) {
		return cachedServices;
	}

	const apiClient = new CEREBROAPIClient({
		baseURL: configManager.getBackendURL(),
		apiKey: configManager.getAPIKey(),
	});

	cachedServices = {
		apiClient,
		audioService: new AudioService(),
		cameraService: new CameraService(apiClient),
		navigationService: new NavigationService(apiClient),
		voiceService: new VoiceService(apiClient),
	};

	return cachedServices;
};

export const useServices = (): ServiceBundle => {
	const services = useMemo(() => initializeServices(), []);

	useEffect(() => {
		services.voiceService.requestPermissions().catch(() => undefined);
		services.cameraService.requestPermissions().catch(() => undefined);
	}, [services]);

	return services;
};
