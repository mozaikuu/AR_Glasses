import { PermissionsAndroid } from "react-native";
import { CEREBROAPIClient } from "@/api/client";
import { ProcessResponse } from "@/types/api";
import RNFS from "@/utils/RNFS";
import { NativeAudioRecorder } from "@/native/bridge";

export class VoiceService {
	private apiClient: CEREBROAPIClient;
	private lastRecordingPath: string | null = null;

	constructor(apiClient: CEREBROAPIClient) {
		this.apiClient = apiClient;
	}

	async requestPermissions(): Promise<boolean> {
		const result = await PermissionsAndroid.request(
			PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
			{
				title: "Microphone access",
				message:
					"CEREBRO needs access to your microphone to capture voice input.",
				buttonPositive: "Allow",
				buttonNegative: "Deny",
			},
		);

		return result === PermissionsAndroid.RESULTS.GRANTED;
	}

	async startRecording(): Promise<void> {
		const filePath = await NativeAudioRecorder.startRecording({
			sampleRate: 16000,
			channels: 1,
			bitsPerSample: 16,
		});
		this.lastRecordingPath = filePath;
	}

	async stopRecording(): Promise<string> {
		const filePath = await NativeAudioRecorder.stopRecording();
		this.lastRecordingPath = filePath;
		const base64 = await RNFS.readFile(filePath, "base64");
		return base64;
	}

	async processAudio(base64Audio: string): Promise<ProcessResponse> {
		return this.apiClient.process({ audio_base64: base64Audio });
	}

	getLastRecordingPath(): string | null {
		return this.lastRecordingPath;
	}
}
