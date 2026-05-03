import "@/global.css";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { GlbViewer } from "@/lib/building-viewers";
import UNI_MODEL from "@/assets/lidar/Uni_textured.glb";

export default function ThreeDTabScreen() {
	const insets = useSafeAreaInsets();

	return (
		<View style={[styles.screen, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 12 }]}>
			<ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
				<Text style={styles.title}>3D building test</Text>
				<Text style={styles.sub}>
					Same campus GLB as the LiDAR tab, with a slower turntable and copy aimed at general 3D building preview (still
					temporary / non-production).
				</Text>
				<View style={styles.viewer}>
					<GlbViewer assetModule={UNI_MODEL} autoRotateYPerFrame={0.002} />
				</View>
				<Text style={styles.note}>
					Source asset: bundled <Text style={styles.mono}>assets/lidar/Uni_textured.glb</Text> (copied from repo{" "}
					<Text style={styles.mono}>Lidar/Uni_textured.glb</Text>).
				</Text>
			</ScrollView>
		</View>
	);
}

const styles = StyleSheet.create({
	screen: { flex: 1, backgroundColor: "#f8fafc" },
	scroll: { paddingHorizontal: 16, paddingBottom: 24, gap: 12 },
	title: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
	sub: { fontSize: 14, lineHeight: 20, color: "#334155" },
	viewer: { height: 360 },
	note: { fontSize: 13, lineHeight: 18, color: "#64748b" },
	mono: { fontFamily: "monospace", color: "#475569" },
});
