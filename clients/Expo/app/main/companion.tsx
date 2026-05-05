import "@/global.css";
import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useRef, useState } from "react";
import {
	ActivityIndicator,
	AppState,
	type AppStateStatus,
	Keyboard,
	KeyboardAvoidingView,
	Modal,
	Platform,
	Pressable,
	ScrollView,
	StyleSheet,
	Switch,
	Text,
	TextInput,
	View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useSegments } from "expo-router";
import { CameraView, useCameraPermissions } from "expo-camera";
import { processCompanion, testCompanionGateway } from "@/lib/companion/api";
import {
	getApiKey,
	getBackendUrl,
	getDefaultBackendUrl,
	normalizeBackendUrl,
	setApiKey,
	setBackendUrl,
} from "@/lib/companion/config";
import { shouldCaptureContext } from "@/lib/companion/contextCapture";
import {
	ensureRecordingPermissions,
	recordShortChunk,
	startCompanionRecording,
	stopCompanionRecording,
} from "@/lib/companion/recording";
import { playTtsFromMetadata } from "@/lib/companion/tts";

const WAKE_POLL_MS = 3200;
const WAKE_CHUNK_SEC = 2.2;

export default function CompanionScreen() {
	const insets = useSafeAreaInsets();
	const segments = useSegments();
	const routeLabel = segments.join("/") || "tabs";

	const [permission, requestCameraPermission] = useCameraPermissions();
	const cameraRef = useRef<InstanceType<typeof CameraView> | null>(null);
	const [cameraReady, setCameraReady] = useState(false);

	const [menuOpen, setMenuOpen] = useState(false);
	const [backendDraft, setBackendDraft] = useState(getDefaultBackendUrl());
	const [apiKeyDraft, setApiKeyDraft] = useState("");
	const [activeBackendUrl, setActiveBackendUrl] = useState(
		getDefaultBackendUrl(),
	);
	const [testBusy, setTestBusy] = useState(false);
	const [testResult, setTestResult] = useState<string | null>(null);

	const [question, setQuestion] = useState("");
	const [reply, setReply] = useState("");
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [lastCaptureInfo, setLastCaptureInfo] = useState<string | null>(null);

	const [wakeEnabled, setWakeEnabled] = useState(false);
	const [appState, setAppState] = useState<AppStateStatus>(AppState.currentState);
	const wakeBusy = useRef(false);
	const holdRecordingActive = useRef(false);

	useEffect(() => {
		const sub = AppState.addEventListener("change", setAppState);
		return () => sub.remove();
	}, []);

	const refreshStoredSettings = useCallback(async () => {
		const url = await getBackendUrl();
		const key = await getApiKey();
		setBackendDraft(url);
		setApiKeyDraft(key ?? "");
		setActiveBackendUrl(url);
	}, []);

	useEffect(() => {
		let cancelled = false;
		void (async () => {
			await refreshStoredSettings();
			if (cancelled) {
				return;
			}
		})();
		return () => {
			cancelled = true;
		};
	}, [refreshStoredSettings]);

	const openMenu = useCallback(async () => {
		setTestResult(null);
		setError(null);
		await refreshStoredSettings();
		setMenuOpen(true);
	}, [refreshStoredSettings]);

	const capturePhotoBase64 = useCallback(async (): Promise<string | null> => {
		if (Platform.OS === "web") {
			return null;
		}
		if (!permission?.granted) {
			return null;
		}
		if (!cameraRef.current || !cameraReady) {
			return null;
		}
		try {
			const pic = await cameraRef.current.takePictureAsync({
				base64: true,
				quality: 0.65,
				skipProcessing: Platform.OS === "android",
			});
			return pic.base64 ?? null;
		} catch {
			return null;
		}
	}, [permission?.granted, cameraReady]);

	const runProcess = useCallback(
		async (payload: Parameters<typeof processCompanion>[0]) => {
			setError(null);
			setBusy(true);
			try {
				const base = await getBackendUrl();
				const res = await processCompanion(payload);
				setReply(res.text ?? "");
				try {
					await playTtsFromMetadata(base, res.metadata);
				} catch {
					// TTS optional for MVP
				}
			} catch (e) {
				setError(e instanceof Error ? e.message : String(e));
			} finally {
				setBusy(false);
			}
		},
		[],
	);

	const onSendText = useCallback(async () => {
		Keyboard.dismiss();
		const text = question.trim();
		if (!text || busy) {
			return;
		}

		let imageBase64: string | null | undefined;
		let captureHint: string | null = null;

		if (shouldCaptureContext(text)) {
			if (!permission?.granted) {
				captureHint =
					"No camera permission — answer sent text-only. Enable camera for visual context.";
			} else {
				imageBase64 = await capturePhotoBase64();
				captureHint = imageBase64
					? "Attached a camera frame (auto)."
					: "Could not capture camera frame — sent text-only.";
			}
		}

		setLastCaptureInfo(captureHint);
		setQuestion("");

		await runProcess({
			text,
			...(imageBase64 ? { image_base64: imageBase64 } : {}),
			metadata: {
				source: "expo_companion_text",
				expo_route: routeLabel,
				auto_capture: Boolean(imageBase64),
			},
		});
	}, [
		question,
		busy,
		permission?.granted,
		capturePhotoBase64,
		runProcess,
		routeLabel,
	]);

	const onAnalyzeCamera = useCallback(async () => {
		Keyboard.dismiss();
		if (busy) {
			return;
		}
		if (!permission?.granted) {
			await requestCameraPermission();
			return;
		}
		const imageBase64 = await capturePhotoBase64();
		if (!imageBase64) {
			setError("Could not capture image. Is the camera ready?");
			return;
		}
		setLastCaptureInfo("Manual camera analyze.");
		await runProcess({
			text: question.trim() || "Describe what you see and answer helpfully.",
			image_base64: imageBase64,
			metadata: {
				source: "expo_companion_manual_camera",
				expo_route: routeLabel,
			},
		});
	}, [
		busy,
		permission?.granted,
		requestCameraPermission,
		capturePhotoBase64,
		question,
		runProcess,
		routeLabel,
	]);

	const onHoldSpeakIn = useCallback(async () => {
		Keyboard.dismiss();
		setError(null);
		const ok = await ensureRecordingPermissions();
		if (!ok) {
			setError("Microphone permission is required for hold-to-talk.");
			return;
		}
		try {
			holdRecordingActive.current = true;
			await startCompanionRecording();
		} catch (e) {
			holdRecordingActive.current = false;
			setError(e instanceof Error ? e.message : "Recording failed to start.");
		}
	}, []);

	const onHoldSpeakOut = useCallback(async () => {
		holdRecordingActive.current = false;
		if (busy) {
			return;
		}
		const audioBase64 = await stopCompanionRecording();
		if (!audioBase64) {
			setError("No audio captured.");
			return;
		}
		setLastCaptureInfo("Hold-to-talk audio.");
		await runProcess({
			audio_base64: audioBase64,
			metadata: {
				source: "expo_companion_hold_talk",
				expo_route: routeLabel,
			},
		});
	}, [busy, runProcess, routeLabel]);

	useEffect(() => {
		if (!wakeEnabled || appState !== "active" || Platform.OS === "web") {
			return;
		}

		const id = setInterval(() => {
			void (async () => {
				if (wakeBusy.current || busy || holdRecordingActive.current) {
					return;
				}
				const ok = await ensureRecordingPermissions();
				if (!ok) {
					return;
				}
				wakeBusy.current = true;
				try {
					const audioBase64 = await recordShortChunk(WAKE_CHUNK_SEC);
					if (!audioBase64) {
						return;
					}
					const res = await processCompanion({
						audio_base64: audioBase64,
						metadata: {
							always_listen: true,
							source: "expo_companion_foreground_wake",
							expo_route: routeLabel,
						},
					});
					const t = (res.text ?? "").trim();
					if (
						t &&
						!t.startsWith("Listening") &&
						!t.includes("say 'Computer'")
					) {
						setReply(t);
						setLastCaptureInfo("Wake-word mode (foreground chunk).");
						const base = await getBackendUrl();
						try {
							await playTtsFromMetadata(base, res.metadata);
						} catch {
							// ignore
						}
					}
				} catch {
					// ignore polling errors
				} finally {
					wakeBusy.current = false;
				}
			})();
		}, WAKE_POLL_MS);

		return () => clearInterval(id);
	}, [wakeEnabled, appState, busy, routeLabel]);

	const saveSettings = useCallback(async () => {
		const normalized = normalizeBackendUrl(backendDraft);
		setBackendDraft(normalized);
		await setBackendUrl(normalized);
		await setApiKey(apiKeyDraft.trim() ? apiKeyDraft : null);
		const stored = await getBackendUrl();
		setActiveBackendUrl(stored);
		setError(null);
		setTestResult(null);
		setReply(
			`Settings saved. Active gateway:\n${stored}\n\nOn a physical phone use your PC LAN IP (not 127.0.0.1).`,
		);
		setMenuOpen(false);
	}, [backendDraft, apiKeyDraft]);

	const runGatewayTest = useCallback(async () => {
		setTestBusy(true);
		setTestResult(null);
		try {
			const base = normalizeBackendUrl(backendDraft);
			const key = apiKeyDraft.trim() || null;
			const result = await testCompanionGateway(base, key);
			setTestResult(result.detail);
			if (!result.ok) {
				setError(result.detail);
			} else {
				setError(null);
			}
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e);
			setTestResult(msg);
			setError(msg);
		} finally {
			setTestBusy(false);
		}
	}, [backendDraft, apiKeyDraft]);

	return (
		<KeyboardAvoidingView
			style={[styles.root, { paddingTop: insets.top + 8 }]}
			behavior={Platform.OS === "ios" ? "padding" : undefined}
		>
			<View style={styles.headerRow}>
				<Text style={styles.title}>Companion</Text>
				<Pressable
					onPress={openMenu}
					style={styles.menuBtn}
					accessibilityLabel="Open settings menu"
					hitSlop={12}
				>
					<Ionicons name="menu" size={28} color="#007AFF" />
				</Pressable>
			</View>

			<Pressable onPress={Keyboard.dismiss}>
				<Text style={styles.sub}>
					Context-aware MVP: typed questions, hold-to-talk, auto camera for vague
					queries, optional foreground wake-word (app open only).
				</Text>
				<Text style={styles.activeUrlLabel} numberOfLines={2}>
					Active gateway: {activeBackendUrl}
				</Text>
			</Pressable>

			<View style={styles.card}>
				<View style={styles.rowBetween}>
					<View style={{ flex: 1, paddingRight: 12 }}>
						<Text style={styles.label}>Wake word (foreground)</Text>
						<Text style={styles.hint}>
							Polls short mic clips while this screen is open and the app is active.
							Say your configured wake word (e.g. Computer) first. Does not run when
							the phone is locked.
						</Text>
					</View>
					<Switch value={wakeEnabled} onValueChange={setWakeEnabled} />
				</View>
			</View>

			{Platform.OS !== "web" && (
				<View style={styles.cameraHost} pointerEvents="none">
					<CameraView
						ref={cameraRef}
						style={styles.camera}
						facing="back"
						mode="picture"
						active={permission?.granted === true}
						onCameraReady={() => setCameraReady(true)}
					/>
				</View>
			)}

			{permission && !permission.granted && Platform.OS !== "web" && (
				<Pressable
					onPress={() => requestCameraPermission()}
					style={styles.warnBanner}
				>
					<Text style={styles.warnText}>
						Tap to allow camera (for context capture)
					</Text>
				</Pressable>
			)}

			<ScrollView
				style={styles.scroll}
				contentContainerStyle={{ paddingBottom: insets.bottom + 120 }}
				keyboardShouldPersistTaps="handled"
				keyboardDismissMode={
					Platform.OS === "ios" ? "interactive" : "on-drag"
				}
			>
				<View style={styles.card}>
					<Text style={styles.label}>Assistant</Text>
					{busy && (
						<View style={styles.loadingRow}>
							<ActivityIndicator color="#007AFF" />
							<Text style={styles.loadingText}>Processing…</Text>
						</View>
					)}
					{error && <Text style={styles.error}>{error}</Text>}
					{lastCaptureInfo && (
						<Text style={styles.meta}>{lastCaptureInfo}</Text>
					)}
					<Text style={styles.reply}>{reply || "—"}</Text>
				</View>

				<View style={styles.card}>
					<TextInput
						value={question}
						onChangeText={setQuestion}
						placeholder='Try: "What is this?" or "Where is room 201?"'
						placeholderTextColor="#888"
						style={[styles.input, styles.multiline]}
						multiline
						blurOnSubmit={false}
					/>
					<View style={styles.keyboardToolbar}>
						<Pressable
							onPress={Keyboard.dismiss}
							style={styles.keyboardToolbarBtn}
							hitSlop={8}
						>
							<Text style={styles.keyboardToolbarText}>Hide keyboard</Text>
						</Pressable>
					</View>
					<Pressable
						onPress={onSendText}
						disabled={busy}
						style={[styles.primaryBtn, busy && styles.disabled]}
					>
						<Text style={styles.primaryBtnText}>Send</Text>
					</Pressable>

					<Pressable
						onPressIn={onHoldSpeakIn}
						onPressOut={onHoldSpeakOut}
						disabled={busy}
						style={[styles.holdBtn, busy && styles.disabled]}
					>
						<Text style={styles.holdBtnText}>Hold to speak</Text>
					</Pressable>

					<Pressable
						onPress={onAnalyzeCamera}
						disabled={busy}
						style={[styles.secondaryBtn, busy && styles.disabled]}
					>
						<Text style={styles.secondaryBtnText}>Analyze with camera</Text>
					</Pressable>
				</View>
			</ScrollView>

			<Modal
				visible={menuOpen}
				animationType="slide"
				transparent
				onRequestClose={() => setMenuOpen(false)}
			>
				<View style={styles.modalRoot}>
					<Pressable
						style={styles.modalBackdrop}
						onPress={() => setMenuOpen(false)}
						accessibilityLabel="Close settings"
					/>
					<View
						style={[
							styles.modalSheet,
							{ paddingBottom: Math.max(insets.bottom, 16) },
						]}
					>
						<View style={styles.modalHeader}>
							<Text style={styles.modalTitle}>Settings</Text>
							<Pressable
								onPress={() => setMenuOpen(false)}
								hitSlop={12}
								accessibilityLabel="Close"
							>
								<Ionicons name="close" size={26} color="#333" />
							</Pressable>
						</View>

						<ScrollView keyboardShouldPersistTaps="handled">
							<Text style={styles.modalHint}>
								Saved gateway (used for requests):
							</Text>
							<Text style={styles.modalActiveUrl}>{activeBackendUrl}</Text>

							<Text style={styles.label}>Gateway base URL</Text>
							<Text style={styles.hint}>
								Use http://YOUR_PC_LAN_IP:PORT on a real device (not 127.0.0.1).
							</Text>
							<TextInput
								value={backendDraft}
								onChangeText={setBackendDraft}
								autoCapitalize="none"
								autoCorrect={false}
								placeholder="http://192.168.x.x:8000"
								placeholderTextColor="#888"
								style={styles.input}
							/>

							<Text style={styles.label}>API key (optional)</Text>
							<Text style={styles.hint}>
								Only if your gateway checks X-API-Key. Wrong key can cause 403.
							</Text>
							<TextInput
								value={apiKeyDraft}
								onChangeText={setApiKeyDraft}
								autoCapitalize="none"
								autoCorrect={false}
								placeholder="X-API-Key header"
								placeholderTextColor="#888"
								style={styles.input}
								secureTextEntry
							/>

							{testBusy ? (
								<View style={styles.loadingRow}>
									<ActivityIndicator color="#007AFF" />
									<Text style={styles.loadingText}>Testing…</Text>
								</View>
							) : (
								<Pressable
									onPress={runGatewayTest}
									style={styles.outlineBtn}
								>
									<Text style={styles.outlineBtnText}>
										Test connection (GET /)
									</Text>
								</Pressable>
							)}

							{testResult && (
								<Text style={styles.testResult}>{testResult}</Text>
							)}

							<Pressable onPress={saveSettings} style={styles.primaryBtn}>
								<Text style={styles.primaryBtnText}>Save settings</Text>
							</Pressable>
						</ScrollView>
					</View>
				</View>
			</Modal>
		</KeyboardAvoidingView>
	);
}

const styles = StyleSheet.create({
	root: {
		flex: 1,
		backgroundColor: "#fff",
		paddingHorizontal: 16,
	},
	headerRow: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
	},
	menuBtn: {
		padding: 4,
	},
	title: {
		fontSize: 22,
		fontWeight: "700",
		color: "#111",
		flex: 1,
	},
	sub: {
		marginTop: 6,
		fontSize: 13,
		color: "#555",
		lineHeight: 18,
	},
	activeUrlLabel: {
		marginTop: 8,
		fontSize: 12,
		color: "#007AFF",
		fontWeight: "600",
	},
	card: {
		backgroundColor: "#f8f9fa",
		borderRadius: 12,
		padding: 12,
		marginBottom: 10,
		borderWidth: 1,
		borderColor: "#e5e5e5",
	},
	label: {
		fontSize: 13,
		fontWeight: "600",
		color: "#333",
		marginBottom: 6,
	},
	hint: {
		fontSize: 12,
		color: "#666",
		lineHeight: 16,
		marginBottom: 6,
	},
	input: {
		borderWidth: 1,
		borderColor: "#ddd",
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 10,
		fontSize: 15,
		color: "#111",
		backgroundColor: "#fff",
		marginBottom: 10,
	},
	multiline: {
		minHeight: 72,
		textAlignVertical: "top",
	},
	keyboardToolbar: {
		alignItems: "flex-end",
		marginBottom: 8,
	},
	keyboardToolbarBtn: {
		paddingVertical: 6,
		paddingHorizontal: 4,
	},
	keyboardToolbarText: {
		color: "#007AFF",
		fontWeight: "600",
		fontSize: 14,
	},
	primaryBtn: {
		backgroundColor: "#007AFF",
		paddingVertical: 14,
		borderRadius: 10,
		alignItems: "center",
		marginBottom: 10,
	},
	primaryBtnText: {
		color: "#fff",
		fontWeight: "700",
		fontSize: 16,
	},
	outlineBtn: {
		borderWidth: 1,
		borderColor: "#007AFF",
		paddingVertical: 12,
		borderRadius: 10,
		alignItems: "center",
		marginBottom: 10,
	},
	outlineBtnText: {
		color: "#007AFF",
		fontWeight: "700",
		fontSize: 15,
	},
	secondaryBtn: {
		backgroundColor: "#34C759",
		paddingVertical: 14,
		borderRadius: 10,
		alignItems: "center",
	},
	secondaryBtnText: {
		color: "#fff",
		fontWeight: "700",
		fontSize: 16,
	},
	holdBtn: {
		backgroundColor: "#5856D6",
		paddingVertical: 14,
		borderRadius: 10,
		alignItems: "center",
		marginBottom: 10,
	},
	holdBtnText: {
		color: "#fff",
		fontWeight: "700",
		fontSize: 16,
	},
	disabled: {
		opacity: 0.45,
	},
	rowBetween: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
	},
	loadingRow: {
		flexDirection: "row",
		alignItems: "center",
		gap: 8,
		marginBottom: 8,
	},
	loadingText: {
		fontSize: 14,
		color: "#555",
	},
	error: {
		color: "#c00",
		fontWeight: "600",
		marginBottom: 8,
	},
	meta: {
		fontSize: 12,
		color: "#666",
		marginBottom: 8,
		fontStyle: "italic",
	},
	reply: {
		fontSize: 15,
		color: "#111",
		lineHeight: 22,
	},
	testResult: {
		fontSize: 12,
		color: "#333",
		marginBottom: 10,
		lineHeight: 17,
	},
	warnBanner: {
		backgroundColor: "#FFF3CD",
		padding: 10,
		borderRadius: 8,
		marginBottom: 8,
	},
	warnText: {
		color: "#856404",
		fontWeight: "600",
		textAlign: "center",
	},
	cameraHost: {
		position: "absolute",
		width: 64,
		height: 64,
		right: 8,
		bottom: 8,
		opacity: 0.04,
		overflow: "hidden",
		zIndex: -1,
	},
	camera: {
		flex: 1,
	},
	scroll: {
		flex: 1,
		marginTop: 4,
	},
	modalRoot: {
		flex: 1,
		justifyContent: "flex-end",
	},
	modalBackdrop: {
		...StyleSheet.absoluteFillObject,
		backgroundColor: "rgba(0,0,0,0.45)",
	},
	modalSheet: {
		backgroundColor: "#fff",
		borderTopLeftRadius: 16,
		borderTopRightRadius: 16,
		paddingHorizontal: 16,
		paddingTop: 16,
		maxHeight: "88%",
	},
	modalHeader: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		marginBottom: 12,
	},
	modalTitle: {
		fontSize: 18,
		fontWeight: "700",
		color: "#111",
	},
	modalHint: {
		fontSize: 12,
		color: "#666",
		marginBottom: 4,
	},
	modalActiveUrl: {
		fontSize: 13,
		color: "#007AFF",
		fontWeight: "600",
		marginBottom: 14,
	},
});
