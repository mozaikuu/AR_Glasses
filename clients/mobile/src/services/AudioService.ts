import RNFS from "@/utils/RNFS";
import { useAppStore } from "@/store";
import { NativeAudioPlayer } from "@/native/bridge";

type CacheInfo = {
	path: string;
	exists: boolean;
};

export class AudioService {
	private cacheDir: string;
	private playbackTimer: ReturnType<typeof setTimeout> | null = null;

	constructor() {
		this.cacheDir = `${RNFS.DocumentDirectoryPath}/cerebro_audio_cache`;
	}

	private async ensureCacheDir(): Promise<void> {
		const exists = await RNFS.exists(this.cacheDir);
		if (!exists) {
			await RNFS.mkdir(this.cacheDir);
		}
	}

	private hashString(value: string): string {
		let hash = 0;
		for (let i = 0; i < value.length; i += 1) {
			hash = (hash << 5) - hash + value.charCodeAt(i);
			hash |= 0;
		}
		return Math.abs(hash).toString();
	}

	private getExtensionFromUrl(url: string): string {
		const match = url.split("?")[0].match(/\.([a-zA-Z0-9]+)$/);
		return match ? match[1] : "wav";
	}

	private async resolveCacheInfo(url: string): Promise<CacheInfo> {
		await this.ensureCacheDir();
		const ext = this.getExtensionFromUrl(url);
		const filename = `${this.hashString(url)}.${ext}`;
		const path = `${this.cacheDir}/${filename}`;
		const exists = await RNFS.exists(path);
		return { path, exists };
	}

	private async schedulePlaybackEnd(): Promise<void> {
		if (this.playbackTimer) {
			clearTimeout(this.playbackTimer);
			this.playbackTimer = null;
		}

		try {
			const durationMs = await NativeAudioPlayer.getDuration();
			if (durationMs > 0) {
				this.playbackTimer = setTimeout(() => {
					useAppStore.getState().setPlayingAudio(false);
					this.playbackTimer = null;
				}, durationMs + 100);
			}
		} catch {
			// Ignore duration errors for now.
		}
	}

	async playTTS(url: string): Promise<string> {
		const cacheInfo = await this.resolveCacheInfo(url);
		if (!cacheInfo.exists) {
			await RNFS.downloadFile({ fromUrl: url, toFile: cacheInfo.path })
				.promise;
		}

		await NativeAudioPlayer.playAudio(cacheInfo.path);
		useAppStore.getState().setPlayingAudio(true);
		await this.schedulePlaybackEnd();

		return cacheInfo.path;
	}

	async stopAudio(): Promise<void> {
		await NativeAudioPlayer.stopAudio();
		useAppStore.getState().setPlayingAudio(false);
		if (this.playbackTimer) {
			clearTimeout(this.playbackTimer);
			this.playbackTimer = null;
		}
	}

	async getCacheSizeMb(): Promise<number> {
		const exists = await RNFS.exists(this.cacheDir);
		if (!exists) {
			return 0;
		}

		const files = await RNFS.readDir(this.cacheDir);
		const totalBytes = files.reduce((sum, file) => sum + (file.size ?? 0), 0);
		return totalBytes / (1024 * 1024);
	}

	async clearCache(): Promise<void> {
		const exists = await RNFS.exists(this.cacheDir);
		if (!exists) {
			return;
		}

		const files = await RNFS.readDir(this.cacheDir);
		await Promise.all(files.map((file) => RNFS.unlink(file.path)));
	}
}
