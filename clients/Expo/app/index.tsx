import "@/global.css";
import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function WelcomeScreen() {
	const insets = useSafeAreaInsets();

	return (
		<View style={[styles.root, { paddingTop: insets.top + 24, paddingBottom: insets.bottom + 24 }]}>
			<View style={styles.content}>
				<Text style={styles.title}>Welcome to Cerebro</Text>
			</View>
			<View style={styles.actions}>
				<Pressable
					style={({ pressed }) => [styles.primaryBtn, pressed && styles.pressed]}
					onPress={() => router.push("/onboarding")}
				>
					<Text style={styles.primaryBtnText}>Onboard</Text>
				</Pressable>
				<Pressable
					style={({ pressed }) => [styles.secondaryBtn, pressed && styles.pressed]}
					onPress={() => router.push("/login")}
				>
					<Text style={styles.secondaryBtnText}>Log in</Text>
				</Pressable>
			</View>
		</View>
	);
}

const styles = StyleSheet.create({
	root: {
		flex: 1,
		backgroundColor: "#fff",
		paddingHorizontal: 28,
		justifyContent: "space-between",
	},
	content: {
		flex: 1,
		justifyContent: "center",
	},
	title: {
		fontSize: 28,
		fontWeight: "800",
		color: "#0f172a",
		textAlign: "center",
	},
	actions: {
		gap: 12,
	},
	primaryBtn: {
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
	secondaryBtn: {
		paddingVertical: 16,
		borderRadius: 12,
		alignItems: "center",
		borderWidth: 1,
		borderColor: "#007AFF",
	},
	secondaryBtnText: {
		color: "#007AFF",
		fontSize: 17,
		fontWeight: "700",
	},
	pressed: {
		opacity: 0.85,
	},
});
