import "@/global.css";
import { router } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const STEPS = [
	{
		title: "Your day in one place",
		body: "See today’s classes, assignments, and what you owe for courses and bus — all from Home.",
	},
	{
		title: "Get around",
		body: "Use Bus for routes and Indoor Nav when you’re on campus.",
	},
	{
		title: "Study companion",
		body: "Companion helps you ask questions and stay on track. You can connect it later.",
	},
] as const;

export default function OnboardingScreen() {
	const insets = useSafeAreaInsets();
	const [step, setStep] = useState(0);
	const isLast = step === STEPS.length - 1;

	const goMain = () => {
		router.replace("/main");
	};

	return (
		<View style={[styles.root, { paddingTop: insets.top + 16, paddingBottom: insets.bottom + 16 }]}>
			<Pressable onPress={goMain} hitSlop={12} style={styles.skipWrap}>
				<Text style={styles.skip}>Skip</Text>
			</Pressable>
			<View style={styles.body}>
				<Text style={styles.progress}>
					{step + 1} / {STEPS.length}
				</Text>
				<Text style={styles.title}>{STEPS[step].title}</Text>
				<Text style={styles.copy}>{STEPS[step].body}</Text>
			</View>
			<View style={styles.footer}>
				{step > 0 ? (
					<Pressable
						style={({ pressed }) => [styles.ghostBtn, pressed && styles.pressed]}
						onPress={() => setStep((s) => s - 1)}
					>
						<Text style={styles.ghostBtnText}>Back</Text>
					</Pressable>
				) : (
					<View style={styles.footerSpacer} />
				)}
				<Pressable
					style={({ pressed }) => [styles.primaryBtn, pressed && styles.pressed]}
					onPress={() => {
						if (isLast) {
							goMain();
						} else {
							setStep((s) => s + 1);
						}
					}}
				>
					<Text style={styles.primaryBtnText}>{isLast ? "Get started" : "Next"}</Text>
				</Pressable>
			</View>
		</View>
	);
}

const styles = StyleSheet.create({
	root: {
		flex: 1,
		backgroundColor: "#fff",
		paddingHorizontal: 24,
	},
	skipWrap: {
		alignSelf: "flex-end",
		paddingVertical: 8,
		paddingHorizontal: 4,
	},
	skip: {
		fontSize: 16,
		color: "#64748b",
		fontWeight: "600",
	},
	body: {
		flex: 1,
		justifyContent: "center",
		paddingBottom: 40,
	},
	progress: {
		fontSize: 14,
		fontWeight: "600",
		color: "#007AFF",
		marginBottom: 12,
	},
	title: {
		fontSize: 26,
		fontWeight: "800",
		color: "#0f172a",
		marginBottom: 16,
	},
	copy: {
		fontSize: 17,
		lineHeight: 26,
		color: "#475569",
	},
	footer: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 12,
	},
	footerSpacer: {
		width: 80,
	},
	ghostBtn: {
		paddingVertical: 14,
		paddingHorizontal: 8,
	},
	ghostBtnText: {
		fontSize: 16,
		fontWeight: "600",
		color: "#64748b",
	},
	primaryBtn: {
		flex: 1,
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
