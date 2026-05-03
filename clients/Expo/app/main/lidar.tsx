import "@/global.css";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { GlbViewer } from "@/lib/building-viewers";
import UNI_MODEL from "@/assets/lidar/Uni_textured.glb";

export default function LidarTabScreen() {
	const insets = useSafeAreaInsets();

	return (
		<View style={[styles.screen, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 12 }]}>
			<ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
				<Text style={styles.title}>LiDAR scan test</Text>
				<Text style={styles.sub}>
					Experimental textured mesh for New Mansoura University (Egypt). This tab is for LiDAR / scan QA only — indoor
					navigation still uses its own 2D map data.
				</Text>
				<View style={styles.viewer}>
					<GlbViewer assetModule={UNI_MODEL} autoRotateYPerFrame={0.006} />
				</View>
				<Text style={styles.note}>
					Tip: GLView + large GLBs are best verified on a physical phone. Simulators and web builds may be slow or fail to
					render.
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
});
