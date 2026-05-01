import { Pose } from "@/types/api";
import {
	ILocalizationProvider,
	LocalizationStatus,
	PoseListener,
} from "@/localization/ILocalizationProvider";

const DEFAULT_POLL_MS = 500;

export class MultiSetLocalizationProvider implements ILocalizationProvider {
	private listener: PoseListener | null = null;
	private pollTimer: ReturnType<typeof setInterval> | null = null;
	private currentPose: Pose | null = null;
	private currentLocation: string | null = null;
	private status: LocalizationStatus = { isReady: false };

	startListening(listener: PoseListener): void {
		this.listener = listener;
		if (this.pollTimer) {
			return;
		}

		this.pollTimer = setInterval(() => {
			if (this.listener) {
				this.listener(this.currentPose);
			}
		}, DEFAULT_POLL_MS);
	}

	stopListening(): void {
		if (this.pollTimer) {
			clearInterval(this.pollTimer);
			this.pollTimer = null;
		}
	}

	getCurrentPose(): Pose | null {
		return this.currentPose;
	}

	getCurrentLocationName(): string | null {
		return this.currentLocation;
	}

	async calibrate(pose: Pose): Promise<void> {
		this.setMockPose(pose);
	}

	getStatus(): LocalizationStatus {
		return this.status;
	}

	setMockPose(pose: Pose): void {
		this.currentPose = pose;
		this.status = {
			isReady: true,
			accuracy: pose.accuracy,
			lastUpdated: Date.now(),
		};

		if (this.listener) {
			this.listener(pose);
		}
	}

	setLocationName(name: string | null): void {
		this.currentLocation = name;
	}
}

export const multiSetProvider = new MultiSetLocalizationProvider();
