import React from "react";
import { FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import { useNavigation } from "@/hooks/useNavigation";

const NavigationScreen = () => {
	const {
		isNavigating,
		currentSession,
		destinations,
		isLoading,
		errorMessage,
		startNavigation,
		stopNavigation,
		nextStep,
		refreshDestinations,
	} = useNavigation();

	return (
		<View style={styles.container}>
			<Text style={styles.title}>Navigation</Text>

			{errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

			{!isNavigating && (
				<>
					<Pressable
						style={styles.refreshButton}
						onPress={refreshDestinations}
					>
						<Text style={styles.refreshText}>
							{isLoading ? "Loading..." : "Refresh Destinations"}
						</Text>
					</Pressable>
					<FlatList
						data={destinations}
						keyExtractor={(item) => item.id}
						renderItem={({ item }) => (
							<Pressable
								style={styles.destinationCard}
								onPress={() => startNavigation(item.name)}
							>
								<Text style={styles.destinationName}>{item.name}</Text>
								{item.description && (
									<Text style={styles.destinationDescription}>
										{item.description}
									</Text>
								)}
							</Pressable>
						)}
						ListEmptyComponent={
							<Text style={styles.emptyText}>
								No destinations available.
							</Text>
						}
					/>
				</>
			)}

			{isNavigating && currentSession && (
				<View style={styles.navigationPanel}>
					<Text style={styles.destinationTitle}>
						{currentSession.destination}
					</Text>
					<Text style={styles.stepText}>
						Step {currentSession.current_step} /{" "}
						{currentSession.total_steps}
					</Text>
					<Text style={styles.instructionText}>
						{currentSession.next_instruction}
					</Text>
					{currentSession.is_complete && (
						<Text style={styles.completeText}>Navigation complete.</Text>
					)}

					<Pressable style={styles.nextButton} onPress={nextStep}>
						<Text style={styles.nextText}>Next Step</Text>
					</Pressable>

					<Pressable style={styles.stopButton} onPress={stopNavigation}>
						<Text style={styles.stopText}>Stop Navigation</Text>
					</Pressable>
				</View>
			)}
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
	errorText: {
		color: "#f87171",
		marginBottom: 12,
		fontWeight: "600",
	},
	refreshButton: {
		backgroundColor: "#1f2937",
		paddingVertical: 12,
		borderRadius: 10,
		alignItems: "center",
		marginBottom: 12,
	},
	refreshText: {
		color: "#e5e7eb",
		fontWeight: "600",
	},
	destinationCard: {
		backgroundColor: "#141b26",
		borderRadius: 14,
		padding: 14,
		marginBottom: 12,
	},
	destinationName: {
		color: "#f5f7fb",
		fontWeight: "700",
		fontSize: 16,
	},
	destinationDescription: {
		color: "#9aa7b2",
		marginTop: 6,
	},
	emptyText: {
		color: "#9aa7b2",
		marginTop: 20,
		textAlign: "center",
	},
	navigationPanel: {
		backgroundColor: "#141b26",
		borderRadius: 16,
		padding: 20,
		gap: 12,
	},
	destinationTitle: {
		color: "#f5f7fb",
		fontSize: 20,
		fontWeight: "700",
	},
	stepText: {
		color: "#9aa7b2",
	},
	instructionText: {
		color: "#e2e8f0",
		fontSize: 16,
		lineHeight: 22,
	},
	completeText: {
		color: "#22c55e",
		fontWeight: "700",
	},
	nextButton: {
		backgroundColor: "#38bdf8",
		borderRadius: 12,
		paddingVertical: 12,
		alignItems: "center",
	},
	nextText: {
		color: "#0b111a",
		fontWeight: "700",
	},
	stopButton: {
		backgroundColor: "#ef4444",
		borderRadius: 12,
		paddingVertical: 12,
		alignItems: "center",
	},
	stopText: {
		color: "#ffffff",
		fontWeight: "700",
	},
});

export default NavigationScreen;
