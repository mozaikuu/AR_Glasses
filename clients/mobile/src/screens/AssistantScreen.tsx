import React, { useCallback, useEffect, useRef, useState } from "react";
import {
	ActivityIndicator,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	View,
} from "react-native";
import { useAppStore } from "@/store";
import { useServices } from "@/services";

const AssistantScreen = () => {
	const {
		isListening,
		isProcessing,
		isPlayingAudio,
		recordingDuration,
		lastResponse,
		errorMessage,
		setListening,
		setProcessing,
		setRecordingDuration,
		setLastResponse,
		setErrorMessage,
		setLastImageUri,
	} = useAppStore();

	const { voiceService, cameraService, audioService } = useServices();
	const [cameraQuery, setCameraQuery] = useState("");
	const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
	const recordingStartRef = useRef<number | null>(null);

	const stopTimer = useCallback(() => {
		if (timerRef.current) {
			clearInterval(timerRef.current);
			timerRef.current = null;
		}
	}, []);

	const startTimer = useCallback(() => {
		stopTimer();
		recordingStartRef.current = Date.now();
		timerRef.current = setInterval(() => {
			if (recordingStartRef.current) {
				const elapsed = (Date.now() - recordingStartRef.current) / 1000;
				setRecordingDuration(Number(elapsed.toFixed(1)));
			}
		}, 100);
	}, [setRecordingDuration, stopTimer]);

	useEffect(() => () => stopTimer(), [stopTimer]);

	const handlePressIn = async () => {
		try {
			setErrorMessage(null);
			setRecordingDuration(0);
			await voiceService.startRecording();
			setListening(true);
			startTimer();
		} catch (error) {
			setErrorMessage("Failed to start recording.");
			setListening(false);
			stopTimer();
		}
	};

	const handlePressOut = async () => {
		if (!isListening) {
			return;
		}

		stopTimer();
		setListening(false);
		setProcessing(true);
		setErrorMessage(null);

		try {
			const base64Audio = await voiceService.stopRecording();
			const response = await voiceService.processAudio(base64Audio);
			setLastResponse(response.text ?? "");
			if (response.metadata?.tts_url) {
				await audioService.playTTS(response.metadata.tts_url);
			}
		} catch (error) {
			setErrorMessage("Failed to process audio.");
		} finally {
			setProcessing(false);
		}
	};

	const handleCamera = async () => {
		setProcessing(true);
		setErrorMessage(null);
		try {
			const photoPath = await cameraService.capturePhoto();
			setLastImageUri(photoPath);
			const response = await cameraService.analyzeScene(photoPath, cameraQuery.trim() || undefined);
			setLastResponse(response.text ?? "");
			if (response.metadata?.tts_url) {
				await audioService.playTTS(response.metadata.tts_url);
			}
		} catch (error) {
			setErrorMessage("Failed to analyze camera input.");
		} finally {
			setProcessing(false);
		}
	};

	return (
		<View style={styles.container}>
			<Text style={styles.title}>CEREBRO Assistant</Text>

			<View style={styles.controls}>
				<Pressable
					onPressIn={handlePressIn}
					onPressOut={handlePressOut}
					style={({ pressed }) => [styles.listenButton, pressed && styles.listenButtonActive]}
				>
					<Text style={styles.listenText}>{isListening ? "Listening..." : "Hold to Speak"}</Text>
				</Pressable>

				<View style={styles.recordingRow}>
					<Text style={styles.recordingLabel}>Recording:</Text>
					<Text style={styles.recordingValue}>{recordingDuration.toFixed(1)}s</Text>
				</View>

				<TextInput
					value={cameraQuery}
					onChangeText={setCameraQuery}
					placeholder="Optional camera prompt"
					placeholderTextColor="#6d7a8b"
					style={styles.input}
				/>

				<Pressable style={styles.cameraButton} onPress={handleCamera}>
					<Text style={styles.cameraText}>Analyze Scene</Text>
				</Pressable>
			</View>

			{isProcessing && (
				<View style={styles.processing}
					<ActivityIndicator size="large" color="#2e7dff" />
					<Text style={styles.processingText}>Processing...</Text>
				</View>
			)}

			{isPlayingAudio && (
				<Text style={styles.playingText}>Playing audio response...</Text>
			)}

			{errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

			<ScrollView style={styles.responseContainer} contentContainerStyle={styles.responseContent}>
				<Text style={styles.responseText}>{lastResponse || "Your response will appear here."}</Text>
			</ScrollView>
		</View>
	);
};

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: "#0d1117",
		padding: 20,
	},
	title: {
		fontSize: 24,
		fontWeight: "700",
		color: "#f5f7fb",
		marginBottom: 12,
	},
	controls: {
		backgroundColor: "#141b26",
		borderRadius: 16,
		padding: 16,
		gap: 12,
	},
	listenButton: {
		paddingVertical: 16,
		borderRadius: 12,
		backgroundColor: "#2e7dff",
		alignItems: "center",
	},
	listenButtonActive: {
		backgroundColor: "#1e5bd9",
	},
	listenText: {
		color: "#ffffff",
		fontSize: 16,
		fontWeight: "600",
	},
	recordingRow: {
		flexDirection: "row",
		justifyContent: "space-between",
	},
	recordingLabel: {
		color: "#9aa7b2",
		fontSize: 14,
	},
	recordingValue: {
		color: "#f5f7fb",
		fontSize: 14,
		fontWeight: "600",
	},
	input: {
		borderWidth: 1,
		borderColor: "#2b3647",
		borderRadius: 10,
		padding: 10,
		color: "#f5f7fb",
		backgroundColor: "#0b111a",
	},
	cameraButton: {
		paddingVertical: 14,
		borderRadius: 12,
		backgroundColor: "#22c55e",
		alignItems: "center",
	},
	cameraText: {
		color: "#0b111a",
		fontWeight: "700",
		fontSize: 15,
	},
	processing: {
		marginTop: 16,
		alignItems: "center",
		gap: 8,
	},
	processingText: {
		color: "#9aa7b2",
	},
	playingText: {
		marginTop: 12,
		color: "#fbbf24",
		fontWeight: "600",
	},
	errorText: {
		marginTop: 12,
		color: "#f87171",
		fontWeight: "600",
	},
	responseContainer: {
		flex: 1,
		marginTop: 16,
		backgroundColor: "#101827",
		borderRadius: 16,
	},
	responseContent: {
		padding: 16,
	},
	responseText: {
		color: "#cbd5f5",
		fontSize: 15,
		lineHeight: 21,
	},
});

export default AssistantScreen;
