/**
 * Archived LiDAR scan tab (not wired to Expo Router).
 * Restore: copy to `app/main/lidar.tsx` and register in `app/main/_layout.tsx`.
 */
import "@/global.css";
import { StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { GlbViewer } from "@/lib/building-viewers";
import UNI_MODEL from "@/assets/lidar/Uni_textured.glb";

export default function LidarTabScreen() {
	const insets = useSafeAreaInsets();

	return (
		<View style={[styles.screen, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 8 }]}>
			<View style={styles.header}>
				<Text style={styles.title}>LiDAR scan test</Text>
				<Text style={styles.sub}>
					Walk inside the textured mesh (first-person). The camera auto-places in the scan bounds; use Recenter if you
					drift. Indoor navigation still uses its own 2D map data.
				</Text>
			</View>
			<View style={styles.viewer}>
				<GlbViewer assetModule={UNI_MODEL} interactionMode="walk" autoRotateYPerFrame={0} />
			</View>
			<Text style={styles.note}>
				Drag the upper area to look; D-pad moves on the ground plane. Full SLAM localization is not wired here — this is a
				standalone scan viewer. Best on a physical device.
			</Text>
		</View>
	);
}

const styles = StyleSheet.create({
	screen: { flex: 1, backgroundColor: "#f8fafc" },
	header: { paddingHorizontal: 16, gap: 8, paddingBottom: 8 },
	title: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
	sub: { fontSize: 14, lineHeight: 20, color: "#334155" },
	viewer: { flex: 1, minHeight: 320, marginHorizontal: 12, borderRadius: 12, overflow: "hidden" },
	note: { fontSize: 12, lineHeight: 17, color: "#64748b", paddingHorizontal: 16, paddingTop: 8 },
});
