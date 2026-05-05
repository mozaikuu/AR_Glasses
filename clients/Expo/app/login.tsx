import "@/global.css";
import { router } from "expo-router";
import { useState } from "react";
import {
	KeyboardAvoidingView,
	Platform,
	Pressable,
	StyleSheet,
	Text,
	TextInput,
	View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function LoginScreen() {
	const insets = useSafeAreaInsets();
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");

	const continueToApp = () => {
		// No persistence: credentials are discarded when leaving this screen.
		router.replace("/main");
	};

	return (
		<KeyboardAvoidingView
			style={[styles.root, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 16 }]}
			behavior={Platform.OS === "ios" ? "padding" : undefined}
		>
			<Pressable onPress={() => router.back()} hitSlop={12} style={styles.backWrap}>
				<Text style={styles.back}>Back</Text>
			</Pressable>
			<View style={styles.header}>
				<Text style={styles.title}>Log in</Text>
				<Text style={styles.sub}>
					This is a placeholder flow. Nothing is saved yet.
				</Text>
			</View>
			<View style={styles.form}>
				<Text style={styles.label}>Email</Text>
				<TextInput
					value={email}
					onChangeText={setEmail}
					placeholder="you@example.com"
					autoCapitalize="none"
					keyboardType="email-address"
					style={styles.input}
				/>
				<Text style={styles.label}>Password</Text>
				<TextInput
					value={password}
					onChangeText={setPassword}
					placeholder="••••••••"
					secureTextEntry
					style={styles.input}
				/>
				<Pressable
					style={({ pressed }) => [styles.primaryBtn, pressed && styles.pressed]}
					onPress={continueToApp}
				>
					<Text style={styles.primaryBtnText}>Continue</Text>
				</Pressable>
			</View>
		</KeyboardAvoidingView>
	);
}

const styles = StyleSheet.create({
	root: {
		flex: 1,
		backgroundColor: "#fff",
		paddingHorizontal: 24,
	},
	backWrap: {
		alignSelf: "flex-start",
		paddingVertical: 10,
		marginBottom: 8,
	},
	back: {
		fontSize: 16,
		color: "#007AFF",
		fontWeight: "600",
	},
	header: {
		marginBottom: 28,
	},
	title: {
		fontSize: 28,
		fontWeight: "800",
		color: "#0f172a",
	},
	sub: {
		marginTop: 10,
		fontSize: 15,
		lineHeight: 22,
		color: "#64748b",
	},
	form: {
		flex: 1,
	},
	label: {
		fontSize: 14,
		fontWeight: "600",
		color: "#334155",
		marginBottom: 8,
	},
	input: {
		borderWidth: 1,
		borderColor: "#e2e8f0",
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 14,
		fontSize: 16,
		color: "#0f172a",
		marginBottom: 18,
	},
	primaryBtn: {
		marginTop: 8,
		backgroundColor: "#007AFF",
		paddingVertical: 16,
		borderRadius: 12,
		alignItems: "center",
	},
	primaryBtnText: {
		color: "#fff",
		fontSize: 17,
		fontWeight: "700",
	},
	pressed: {
		opacity: 0.88,
	},
});
