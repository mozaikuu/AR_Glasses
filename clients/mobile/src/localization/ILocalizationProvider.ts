import { Pose } from "@/types/api";

export type LocalizationStatus = {
	isReady: boolean;
	accuracy?: number;
	lastUpdated?: number;
	errorMessage?: string;
};

export type PoseListener = (pose: Pose | null) => void;

export interface ILocalizationProvider {
	startListening(listener: PoseListener): void;
	stopListening(): void;
	getCurrentPose(): Pose | null;
	getCurrentLocationName(): string | null;
	calibrate(pose: Pose): Promise<void>;
	getStatus(): LocalizationStatus;
}
