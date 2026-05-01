import { create } from "zustand";
import { Destination, NavigationStatus, Pose } from "@/types/api";

export type AppState = {
	isListening: boolean;
	isProcessing: boolean;
	isPlayingAudio: boolean;
	recordingDuration: number;
	lastResponse: string;
	lastImageUri: string | null;
	errorMessage: string | null;

	isNavigating: boolean;
	navigationSession: NavigationStatus | null;
	destinations: Destination[];
	navigationError: string | null;
	currentPose: Pose | null;
	currentLocation: string | null;

	setListening: (value: boolean) => void;
	setProcessing: (value: boolean) => void;
	setPlayingAudio: (value: boolean) => void;
	setRecordingDuration: (value: number) => void;
	setLastResponse: (value: string) => void;
	setLastImageUri: (value: string | null) => void;
	setErrorMessage: (value: string | null) => void;

	setNavigating: (value: boolean) => void;
	setNavigationSession: (session: NavigationStatus | null) => void;
	setDestinations: (destinations: Destination[]) => void;
	setNavigationError: (value: string | null) => void;
	setCurrentPose: (pose: Pose | null) => void;
	setCurrentLocation: (value: string | null) => void;
};

export const useAppStore = create<AppState>((set) => ({
	isListening: false,
	isProcessing: false,
	isPlayingAudio: false,
	recordingDuration: 0,
	lastResponse: "",
	lastImageUri: null,
	errorMessage: null,

	isNavigating: false,
	navigationSession: null,
	destinations: [],
	navigationError: null,
	currentPose: null,
	currentLocation: null,

	setListening: (value) => set({ isListening: value }),
	setProcessing: (value) => set({ isProcessing: value }),
	setPlayingAudio: (value) => set({ isPlayingAudio: value }),
	setRecordingDuration: (value) => set({ recordingDuration: value }),
	setLastResponse: (value) => set({ lastResponse: value }),
	setLastImageUri: (value) => set({ lastImageUri: value }),
	setErrorMessage: (value) => set({ errorMessage: value }),

	setNavigating: (value) => set({ isNavigating: value }),
	setNavigationSession: (session) => set({ navigationSession: session }),
	setDestinations: (destinations) => set({ destinations }),
	setNavigationError: (value) => set({ navigationError: value }),
	setCurrentPose: (pose) => set({ currentPose: pose }),
	setCurrentLocation: (value) => set({ currentLocation: value }),
}));
