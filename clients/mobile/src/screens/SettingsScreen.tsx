import React, { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { configManager } from "@/config";
import { initializeServices } from "@/services";

const SettingsScreen = () => {
	const [backendURL, setBackendURL] = useState(configManager.getBackendURL());
	const [apiKey, setApiKey] = useState(configManager.getAPIKey() ?? "");
	const [status, setStatus] = useState<string | null>(null);

	const handleSave = () => {
		configManager.setBackendURL(backendURL);
		configManager.setAPIKey(apiKey);
		const { apiClient } = initializeServices();
		apiClient.setBaseURL(configManager.getBackendURL());
		apiClient.setAPIKey(configManager.getAPIKey());
		setStatus("Settings saved.");
		setTimeout(() => setStatus(null), 2000);
	};

	return (
		<View style={styles.container}>
			<Text style={styles.title}>Settings</Text>
			<Text style={styles.label}>Backend URL</Text>
			<TextInput
				style={styles.input}
				value={backendURL}
				onChangeText={setBackendURL}
				autoCapitalize="none"
				autoCorrect={false}
				placeholder="http://127.0.0.1:8000"
				placeholderTextColor="#6d7a8b"
			/>
			<Text style={styles.label}>API Key (optional)</Text>
			<TextInput
				style={styles.input}
				value={apiKey}
				onChangeText={setApiKey}
				autoCapitalize="none"
				autoCorrect={false}
				placeholder="X-API-Key"
				placeholderTextColor="#6d7a8b"
			/>

			<Pressable style={styles.saveButton} onPress={handleSave}>
				<Text style={styles.saveText}>Save</Text>
			</Pressable>

			{status && <Text style={styles.statusText}>{status}</Text>}
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
	label: {
		color: "#9aa7b2",
		marginTop: 12,
		marginBottom: 6,
	},
	input: {
		borderWidth: 1,
		borderColor: "#2b3647",
		borderRadius: 10,
		padding: 10,
		color: "#f5f7fb",
		backgroundColor: "#0b111a",
	},
	saveButton: {
		backgroundColor: "#22c55e",
		borderRadius: 12,
		paddingVertical: 12,
		alignItems: "center",
		marginTop: 20,
	},
	saveText: {
		color: "#0b111a",
		fontWeight: "700",
	},
	statusText: {
		marginTop: 12,
		color: "#38bdf8",
		fontWeight: "600",
	},
});

export default SettingsScreen;
