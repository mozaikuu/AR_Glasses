import "@/global.css";
import { useCallback, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import * as DocumentPicker from "expo-document-picker";

import { EquirectangularPanorama } from "@/lib/building-viewers";

/**
 * Panorama experiments use equirectangular images. Add files under the repo `img360/` folder on disk,
 * then copy a supported image into `clients/Expo/assets/panorama/` and `require` it here as the default.
 */
export default function PanoramaTabScreen() {
	const insets = useSafeAreaInsets();
	const [imageUri, setImageUri] = useState<string | null>(null);

	const pickImage = useCallback(async () => {
		const result = await DocumentPicker.getDocumentAsync({
			type: "image/*",
			copyToCacheDirectory: true,
		});
		if (result.canceled) {
			return;
		}
		const asset = result.assets[0];
		if (asset?.uri) {
			setImageUri(asset.uri);
		}
	}, []);

	return (
		<View style={[styles.screen, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 12 }]}>
			<ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
				<Text style={styles.title}>Panorama test</Text>
				<Text style={styles.sub}>
					360° placeholder for New Mansoura University campus imagery. The repo <Text style={styles.mono}>img360/</Text>{" "}
					folder is the intended source on disk; bundle images under{" "}
					<Text style={styles.mono}>assets/panorama/</Text> when you add files so Metro can ship a default preview.
				</Text>

				<Pressable style={styles.btn} onPress={pickImage}>
					<Text style={styles.btnTxt}>Pick equirectangular image</Text>
				</Pressable>

				{imageUri ? (
					<View style={styles.viewer}>
						<EquirectangularPanorama imageUri={imageUri} />
					</View>
				) : (
					<View style={styles.placeholder}>
						<Text style={styles.placeholderTitle}>No panorama loaded</Text>
						<Text style={styles.placeholderBody}>
							Use the button above to choose a local equirectangular JPEG/PNG. For best results use a 2:1 panorama; very
							large files may be slow on device.
						</Text>
					</View>
				)}
			</ScrollView>
		</View>
	);
}

const styles = StyleSheet.create({
	screen: { flex: 1, backgroundColor: "#f8fafc" },
	scroll: { paddingHorizontal: 16, paddingBottom: 24, gap: 12 },
	title: { fontSize: 22, fontWeight: "700", color: "#0f172a" },
	sub: { fontSize: 14, lineHeight: 20, color: "#334155" },
	mono: { fontFamily: "monospace", color: "#0f172a" },
	btn: {
		alignSelf: "flex-start",
		backgroundColor: "#2563eb",
		paddingHorizontal: 16,
		paddingVertical: 12,
		borderRadius: 10,
	},
	btnTxt: { color: "#fff", fontWeight: "600", fontSize: 15 },
	viewer: { height: 360 },
	placeholder: {
		minHeight: 220,
		borderRadius: 12,
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderStyle: "dashed",
		padding: 16,
		justifyContent: "center",
		gap: 8,
		backgroundColor: "#fff",
	},
	placeholderTitle: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
	placeholderBody: { fontSize: 14, lineHeight: 20, color: "#475569" },
});
