import { Audio } from "expo-av";
import {
	InterruptionModeAndroid,
	InterruptionModeIOS,
} from "expo-av/build/Audio.types";
import { resolveAbsoluteUrl } from "@/lib/companion/api";
import type { ProcessMetadata } from "@/lib/companion/types";

export async function playTtsFromMetadata(
	baseUrl: string,
	metadata: ProcessMetadata | undefined,
): Promise<void> {
	const raw = metadata?.tts_url;
	if (!raw || typeof raw !== "string") {
		return;
	}
	const uri = resolveAbsoluteUrl(baseUrl, raw);

	await Audio.setAudioModeAsync({
		allowsRecordingIOS: false,
		playsInSilentModeIOS: true,
		interruptionModeIOS: InterruptionModeIOS.MixWithOthers,
		staysActiveInBackground: false,
		interruptionModeAndroid: InterruptionModeAndroid.DuckOthers,
		shouldDuckAndroid: true,
		playThroughEarpieceAndroid: false,
	});

	const { sound } = await Audio.Sound.createAsync({ uri });
	try {
		await sound.playAsync();
		const status = await sound.getStatusAsync();
		const durationMs =
			status.isLoaded && "durationMillis" in status && status.durationMillis
				? status.durationMillis
				: 5000;
		await new Promise((r) => setTimeout(r, durationMs + 400));
	} finally {
		await sound.unloadAsync().catch(() => undefined);
	}
}
