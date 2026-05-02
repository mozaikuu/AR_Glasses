import { PermissionsAndroid } from "react-native";
import { CEREBROAPIClient } from "@/api/client";
import { ProcessResponse } from "@/types/api";
import RNFS from "@/utils/RNFS";
import { NativeCamera } from "@/native/bridge";

export class CameraService {
	private apiClient: CEREBROAPIClient;
	private lastCapturePath: string | null = null;

	constructor(apiClient: CEREBROAPIClient) {
		this.apiClient = apiClient;
	}

	async requestPermissions(): Promise<boolean> {
		const result = await PermissionsAndroid.request(
			PermissionsAndroid.PERMISSIONS.CAMERA,
			{
				title: "Camera access",
				message: "CEREBRO needs access to your camera to analyze scenes.",
				buttonPositive: "Allow",
				buttonNegative: "Deny",
			},
		);

		return result === PermissionsAndroid.RESULTS.GRANTED;
	}

	async capturePhoto(quality = 0.85): Promise<string> {
		const filePath = await NativeCamera.capturePhoto({ quality });
		this.lastCapturePath = filePath;
		return filePath;
	}

	async analyzeScene(
		filePath: string,
		query?: string,
	): Promise<ProcessResponse> {
		const base64 = await RNFS.readFile(filePath, "base64");
		return this.apiClient.process({
			image_base64: base64,
			text: query,
		});
	}

	async captureAndAnalyze(query?: string): Promise<ProcessResponse> {
		const filePath = await this.capturePhoto();
		return this.analyzeScene(filePath, query);
	}

	getLastCapturePath(): string | null {
		return this.lastCapturePath;
	}
}
