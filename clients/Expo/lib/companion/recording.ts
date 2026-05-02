import { Audio } from "expo-av";
import {
	InterruptionModeAndroid,
	InterruptionModeIOS,
} from "expo-av/build/Audio.types";
import {
	AndroidAudioEncoder,
	AndroidOutputFormat,
	IOSAudioQuality,
	IOSOutputFormat,
} from "expo-av/build/Audio/RecordingConstants";
import type { RecordingOptions } from "expo-av/build/Audio/Recording.types";
import { Platform } from "react-native";

function uint8ArrayToBase64(bytes: Uint8Array): string {
	let binary = "";
	const chunk = 0x8000;
	for (let i = 0; i < bytes.length; i += chunk) {
		binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
	}
	return globalThis.btoa(binary);
}

async function uriToBase64(uri: string): Promise<string> {
	const response = await fetch(uri);
	const buf = await response.arrayBuffer();
	return uint8ArrayToBase64(new Uint8Array(buf));
}

/** iOS: linear PCM WAV @16kHz mono (works with gateway STT). Android: AAC m4a (needs pydub/ffmpeg on server). */
export function getCompanionRecordingOptions(): RecordingOptions {
	return {
		isMeteringEnabled: true,
		android: {
			extension: ".m4a",
			outputFormat: AndroidOutputFormat.MPEG_4,
			audioEncoder: AndroidAudioEncoder.AAC,
			sampleRate: 44100,
			numberOfChannels: 1,
			bitRate: 128000,
		},
		ios: {
			extension: ".wav",
			sampleRate: 16000,
			numberOfChannels: 1,
			outputFormat: IOSOutputFormat.LINEARPCM,
			audioQuality: IOSAudioQuality.HIGH,
			bitRate: 256000,
			linearPCMBitDepth: 16,
			linearPCMIsBigEndian: false,
			linearPCMIsFloat: false,
		},
		web: {
			mimeType: "audio/webm",
			bitsPerSecond: 128000,
		},
	};
}

let prepared: InstanceType<typeof Audio.Recording> | null = null;

export async function ensureRecordingPermissions(): Promise<boolean> {
	const { status } = await Audio.requestPermissionsAsync();
	return status === "granted";
}

export async function startCompanionRecording(): Promise<void> {
	await Audio.setAudioModeAsync({
		allowsRecordingIOS: true,
		playsInSilentModeIOS: true,
		interruptionModeIOS: InterruptionModeIOS.DoNotMix,
		staysActiveInBackground: false,
		interruptionModeAndroid: InterruptionModeAndroid.DuckOthers,
		shouldDuckAndroid: true,
		playThroughEarpieceAndroid: false,
	});

	if (prepared) {
		try {
			await prepared.stopAndUnloadAsync();
		} catch {
			// ignore
		}
		prepared = null;
	}

	const recording = new Audio.Recording();
	await recording.prepareToRecordAsync(getCompanionRecordingOptions());
	await recording.startAsync();
	prepared = recording;
}

export async function stopCompanionRecording(): Promise<string | null> {
	if (!prepared) {
		return null;
	}
	const rec = prepared;
	prepared = null;

	try {
		await rec.stopAndUnloadAsync();
	} catch {
		return null;
	}

	const uri = rec.getURI();
	if (!uri) {
		return null;
	}

	try {
		return await uriToBase64(uri);
	} catch {
		return null;
	}
}

/** Short clip for foreground wake-word polling (same format rules as hold-to-talk). */
export async function recordShortChunk(durationSeconds: number): Promise<string | null> {
	if (Platform.OS === "web") {
		return null;
	}
	const ok = await ensureRecordingPermissions();
	if (!ok) {
		return null;
	}

	await Audio.setAudioModeAsync({
		allowsRecordingIOS: true,
		playsInSilentModeIOS: true,
		interruptionModeIOS: InterruptionModeIOS.DoNotMix,
		staysActiveInBackground: false,
		interruptionModeAndroid: InterruptionModeAndroid.DuckOthers,
		shouldDuckAndroid: true,
		playThroughEarpieceAndroid: false,
	});

	const recording = new Audio.Recording();
	await recording.prepareToRecordAsync(getCompanionRecordingOptions());
	await recording.startAsync();

	await new Promise((r) => setTimeout(r, Math.max(0.8, durationSeconds) * 1000));

	try {
		await recording.stopAndUnloadAsync();
	} catch {
		return null;
	}

	const uri = recording.getURI();
	if (!uri) {
		return null;
	}
	try {
		return await uriToBase64(uri);
	} catch {
		return null;
	}
}
