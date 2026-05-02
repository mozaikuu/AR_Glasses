export type AudioRecorderConfig = {
	sampleRate: number;
	channels: number;
	bitsPerSample: number;
};

export class AudioRecorderStub {
	async startRecording(_config: AudioRecorderConfig): Promise<string> {
		throw new Error("AudioRecorderModule is not available on this platform.");
	}

	async stopRecording(): Promise<string> {
		throw new Error("AudioRecorderModule is not available on this platform.");
	}
}

export type CameraCaptureOptions = {
	quality?: number;
};

export class CameraStub {
	async capturePhoto(_options: CameraCaptureOptions): Promise<string> {
		throw new Error("CameraModule is not available on this platform.");
	}

	async startPreview(): Promise<void> {
		throw new Error("CameraModule is not available on this platform.");
	}

	async stopPreview(): Promise<void> {
		throw new Error("CameraModule is not available on this platform.");
	}
}

export class AudioPlayerStub {
	async playAudio(_filePath: string): Promise<void> {
		throw new Error("AudioPlayerModule is not available on this platform.");
	}

	async stopAudio(): Promise<void> {
		throw new Error("AudioPlayerModule is not available on this platform.");
	}

	async isPlaying(): Promise<boolean> {
		return false;
	}

	async getDuration(): Promise<number> {
		return 0;
	}
}
