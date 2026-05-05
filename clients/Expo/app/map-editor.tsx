import "@/global.css";
import { Platform, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import buildingBundleJson from "@/assets/navigation/uni/uni-bundle.json";
import { MapEditorWeb } from "@/lib/navigation-mvp/editor/MapEditorWeb";
import { parseBuildingBundle } from "@/lib/navigation-mvp/validate";
import { useState } from "react";

const bundleParsed = parseBuildingBundle(buildingBundleJson);

export default function MapEditorRoute() {
	const [floorIndex, setFloorIndex] = useState(0);

	if (Platform.OS !== "web") {
		return (
			<View style={styles.blocked}>
				<Text style={styles.title}>Map editor</Text>
				<Text style={styles.body}>The floor plan editor runs on web only. Open this route in Expo web.</Text>
			</View>
		);
	}

	if (!bundleParsed.ok) {
		return (
			<View style={styles.blocked}>
				<Text style={styles.title}>Invalid building bundle</Text>
				<Text style={styles.body}>{bundleParsed.error}</Text>
			</View>
		);
	}

	const bundle = bundleParsed.data;
	const floor = bundle.floors.find((f) => f.index === floorIndex) ?? bundle.floors[0];

	return (
		<View style={styles.root}>
			{bundle.floors.length > 1 ? (
				<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabs}>
					{bundle.floors.map((fl) => (
						<Pressable
							key={fl.index}
							onPress={() => setFloorIndex(fl.index)}
							style={[styles.pill, floorIndex === fl.index && styles.pillOn]}
						>
							<Text style={[styles.pillTxt, floorIndex === fl.index && styles.pillTxtOn]}>{fl.level}</Text>
						</Pressable>
					))}
				</ScrollView>
			) : null}
			<MapEditorWeb key={`editor-${floor?.index ?? 0}`} initialMap={floor.map} />
		</View>
	);
}

const styles = StyleSheet.create({
	root: { flex: 1, backgroundColor: "#fff" },
	blocked: { flex: 1, padding: 24, justifyContent: "center", gap: 12, backgroundColor: "#f8fafc" },
	title: { fontSize: 20, fontWeight: "800", color: "#0f172a" },
	body: { fontSize: 15, lineHeight: 22, color: "#475569" },
	tabs: { maxHeight: 48, paddingHorizontal: 8, paddingTop: 8 },
	pill: {
		paddingHorizontal: 14,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#f1f5f9",
		marginRight: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	pillOn: { backgroundColor: "#eff6ff", borderColor: "#2563eb" },
	pillTxt: { fontWeight: "700", color: "#475569", fontSize: 14 },
	pillTxtOn: { color: "#1d4ed8" },
});
