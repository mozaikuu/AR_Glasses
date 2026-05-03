import { Link, Stack } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

export default function NotFoundScreen() {
	return (
		<>
			<Stack.Screen options={{ title: "Not found" }} />
			<View style={styles.container}>
				<Text style={styles.title}>This screen does not exist.</Text>
				<Text style={styles.body}>
					The app opened a URL or path that is not registered. That often
					happens with an old deep link (for example a path without{" "}
					<Text style={styles.mono}>/main</Text>) or a typo in{" "}
					<Text style={styles.mono}>exp://…:8081</Text> links.
				</Text>
				<Link href="/" style={styles.link}>
					<Text style={styles.linkText}>Go to welcome</Text>
				</Link>
				<Link href="/main" style={styles.link}>
					<Text style={styles.linkText}>Go to app home</Text>
				</Link>
			</View>
		</>
	);
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		padding: 24,
		justifyContent: "center",
		backgroundColor: "#fff",
	},
	title: {
		fontSize: 20,
		fontWeight: "700",
		color: "#0f172a",
		marginBottom: 12,
	},
	body: {
		fontSize: 15,
		lineHeight: 22,
		color: "#64748b",
		marginBottom: 24,
	},
	mono: {
		fontFamily: "monospace",
		fontSize: 14,
		color: "#334155",
	},
	link: {
		marginVertical: 8,
	},
	linkText: {
		fontSize: 17,
		fontWeight: "600",
		color: "#007AFF",
	},
});
