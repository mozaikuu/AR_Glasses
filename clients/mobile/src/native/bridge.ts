import { NativeModules } from "react-native";
import {
	AudioPlayerStub,
	AudioRecorderStub,
	CameraStub,
	AudioRecorderConfig,
	CameraCaptureOptions,
} from "@/native/NativeModuleStubs";

export type NativeAudioRecorder = {
	startRecording: (config: AudioRecorderConfig) => Promise<string>;
	stopRecording: () => Promise<string>;
};

export type NativeCamera = {
	capturePhoto: (options: CameraCaptureOptions) => Promise<string>;
	startPreview?: () => Promise<void>;
	stopPreview?: () => Promise<void>;
};

export type NativeAudioPlayer = {
	playAudio: (filePath: string) => Promise<void>;
	stopAudio: () => Promise<void>;
	isPlaying: () => Promise<boolean>;
	getDuration: () => Promise<number>;
};

const audioRecorderModule = NativeModules.AudioRecorderModule as
	| NativeAudioRecorder
	| undefined;
const cameraModule = NativeModules.CameraModule as NativeCamera | undefined;
const audioPlayerModule = NativeModules.AudioPlayerModule as
	| NativeAudioPlayer
	| undefined;

const audioRecorderFallback = new AudioRecorderStub();
const cameraFallback = new CameraStub();
const audioPlayerFallback = new AudioPlayerStub();

export const NativeAudioRecorder: NativeAudioRecorder = audioRecorderModule ?? {
	startRecording: (config) => audioRecorderFallback.startRecording(config),
	stopRecording: () => audioRecorderFallback.stopRecording(),
};

export const NativeCamera: NativeCamera = cameraModule ?? {
	capturePhoto: (options) => cameraFallback.capturePhoto(options),
	startPreview: () => cameraFallback.startPreview(),
	stopPreview: () => cameraFallback.stopPreview(),
};

export const NativeAudioPlayer: NativeAudioPlayer = audioPlayerModule ?? {
	playAudio: (filePath) => audioPlayerFallback.playAudio(filePath),
	stopAudio: () => audioPlayerFallback.stopAudio(),
	isPlaying: () => audioPlayerFallback.isPlaying(),
	getDuration: () => audioPlayerFallback.getDuration(),
};
