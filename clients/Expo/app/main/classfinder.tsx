/**
 * Campus class finder tab (SOEN390-style): mini campus map, today’s classes, POI search, glass UI.
 * Inspired by https://github.com/team-exception-handlers/soen390-project
 */
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useMemo, useState } from "react";
import {
	FlatList,
	Linking,
	Modal,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	View,
	useWindowDimensions,
} from "react-native";
import Svg, { G, Rect, Text as SvgText } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
	CAMPUS_BUILDINGS,
	DEMO_LECTURES,
	DEMO_POIS,
	FLOORS_BY_BUILDING,
	type LectureDemo,
	type PoiDemo,
} from "@/lib/classfinder/campusData";
import { scanForRoom } from "@/lib/classfinder/parseRoom";

const REPO = "https://github.com/team-exception-handlers/soen390-project";

const VB = { w: 320, h: 200 };

type TabKey = "map" | "today" | "places";

function mockDirections(roomToken: string): string[] {
	const b = roomToken.split("-")[0] ?? "?";
	return [
		`Leave current area toward building ${b}.`,
		`Enter ${b} lobby — follow corridor signage for ${roomToken}.`,
		`Take stairs or elevator to the floor indicated on your room key.`,
		`Arrive near ${roomToken} (demo steps — hook to live indoor nav when ready).`,
	];
}

export default function ClassFinderTab() {
	const insets = useSafeAreaInsets();
	const { width: winW } = useWindowDimensions();
	const mapW = Math.min(winW - 32, 360);

	const [tab, setTab] = useState<TabKey>("map");
	const [selectedCode, setSelectedCode] = useState<string | null>("H");
	const [floorKey, setFloorKey] = useState<string>("H-1");
	const [search, setSearch] = useState("");
	const [placeFilter, setPlaceFilter] = useState<PoiDemo["category"] | "all">("all");
	const [lectureModal, setLectureModal] = useState<LectureDemo | null>(null);

	const parsedSearch = useMemo(() => scanForRoom(search), [search]);

	const floors = selectedCode ? (FLOORS_BY_BUILDING[selectedCode] ?? []) : [];

	const filteredPois = useMemo(() => {
		const s = search.trim().toLowerCase();
		return DEMO_POIS.filter((p) => {
			if (placeFilter !== "all" && p.category !== placeFilter) {
				return false;
			}
			if (!s) {
				return true;
			}
			return (
				p.name.toLowerCase().includes(s) ||
				p.building.toLowerCase().includes(s) ||
				p.floorKey.toLowerCase().includes(s)
			);
		});
	}, [search, placeFilter]);

	const openMaps = () => {
		void Linking.openURL(
			"https://www.google.com/maps/search/?api=1&query=Concordia+University+Montreal",
		);
	};

	return (
		<View style={[styles.root, { paddingTop: 10 + insets.top }]}>
			<View style={styles.hero}>
				<Text style={styles.title}>Campus finder</Text>
				<Text style={styles.sub}>Map · schedule · services (demo data)</Text>
			</View>

			<View style={styles.segment}>
				{(["map", "today", "places"] as const).map((k) => (
					<Pressable
						key={k}
						onPress={() => setTab(k)}
						style={[styles.segBtn, tab === k && styles.segBtnOn]}
					>
						<Text style={[styles.segTxt, tab === k && styles.segTxtOn]}>
							{k === "map" ? "Map" : k === "today" ? "Today" : "Places"}
						</Text>
					</Pressable>
				))}
			</View>

			{tab === "map" ? (
				<ScrollView contentContainerStyle={styles.scrollPad}>
					<Text style={styles.cardTitle}>Mini campus</Text>
					<Text style={styles.cardHint}>
						Select a building below — the map highlights your choice. Pick a floor, then open indoor navigation.
					</Text>
					<View style={[styles.mapWrap, { width: mapW }]}>
						<Svg width={mapW} height={(mapW * VB.h) / VB.w} viewBox={`0 0 ${VB.w} ${VB.h}`}>
							<Rect x={0} y={0} width={VB.w} height={VB.h} rx={14} fill="#0f172a" />
							{CAMPUS_BUILDINGS.map((b) => {
								const on = selectedCode === b.code;
								const { x, y, w, h } = b.map;
								return (
									<G key={String(b.code)}>
										<Rect
											x={x}
											y={y}
											width={w}
											height={h}
											rx={10}
											fill={b.color}
											opacity={on ? 1 : 0.55}
											stroke="#fff"
											strokeWidth={on ? 3 : 1}
										/>
										<SvgText x={x + 8} y={y + 18} fill="#fff" fontSize={11} fontWeight="800">
											{String(b.code)}
										</SvgText>
									</G>
								);
							})}
						</Svg>
					</View>

					<View style={styles.buildingPick}>
						{CAMPUS_BUILDINGS.map((b) => (
							<Pressable
								key={String(b.code)}
								onPress={() => {
									setSelectedCode(String(b.code));
									const fl = FLOORS_BY_BUILDING[String(b.code)]?.[0];
									if (fl) {
										setFloorKey(fl.key);
									}
								}}
								style={[styles.buildingPill, selectedCode === b.code && styles.buildingPillOn]}
							>
								<Text style={[styles.buildingPillTxt, selectedCode === b.code && styles.buildingPillTxtOn]}>
									{String(b.code)} · {b.name}
								</Text>
							</Pressable>
						))}
					</View>

					<Text style={styles.section}>Floors — {selectedCode ?? "—"}</Text>
					<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.floorRow}>
						{floors.map((f) => (
							<Pressable
								key={f.key}
								onPress={() => setFloorKey(f.key)}
								style={[styles.floorChip, floorKey === f.key && styles.floorChipOn]}
							>
								<Text style={[styles.floorChipTxt, floorKey === f.key && styles.floorChipTxtOn]}>
									{f.label} ({f.key})
								</Text>
							</Pressable>
						))}
					</ScrollView>

					<View style={styles.btnRow}>
						<Pressable onPress={() => router.push("/main/navigation")} style={styles.primary}>
							<Ionicons name="navigate" size={18} color="#fff" />
							<Text style={styles.primaryTxt}>Indoor nav</Text>
						</Pressable>
						<Pressable onPress={openMaps} style={styles.outdoor}>
							<Ionicons name="earth" size={18} color="#0f172a" />
							<Text style={styles.outdoorTxt}>Outdoor maps</Text>
						</Pressable>
					</View>
				</ScrollView>
			) : null}

			{tab === "today" ? (
				<FlatList
					data={DEMO_LECTURES}
					keyExtractor={(i) => i.id}
					contentContainerStyle={styles.listPad}
					renderItem={({ item }) => (
						<Pressable onPress={() => setLectureModal(item)} style={styles.lecCard}>
							<View style={styles.lecTop}>
								<Text style={styles.lecCode}>{item.courseCode}</Text>
								<Text style={styles.lecTime}>
									{item.day} {item.start}–{item.end}
								</Text>
							</View>
							<Text style={styles.lecTitle}>{item.title}</Text>
							<Text style={styles.lecRoom}>Room: {scanForRoom(item.roomRaw) ?? item.roomRaw}</Text>
						</Pressable>
					)}
				/>
			) : null}

			{tab === "places" ? (
				<ScrollView contentContainerStyle={styles.scrollPad}>
					<TextInput
						value={search}
						onChangeText={setSearch}
						placeholder="Search washrooms, food, study…"
						placeholderTextColor="#64748b"
						style={styles.input}
					/>
					{parsedSearch ? (
						<View style={styles.parseBanner}>
							<Text style={styles.parseLbl}>Detected room</Text>
							<Text style={styles.parseVal}>{parsedSearch}</Text>
						</View>
					) : null}
					<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterRow}>
						{(["all", "washroom", "food", "study", "transit"] as const).map((c) => (
							<Pressable
								key={c}
								onPress={() => setPlaceFilter(c)}
								style={[styles.filterChip, placeFilter === c && styles.filterChipOn]}
							>
								<Text style={[styles.filterTxt, placeFilter === c && styles.filterTxtOn]}>
									{c === "all" ? "All" : c}
								</Text>
							</Pressable>
						))}
					</ScrollView>
					{filteredPois.map((p) => (
						<View key={p.id} style={styles.poiRow}>
							<Ionicons
								name={
									p.category === "washroom"
										? "water"
										: p.category === "food"
											? "fast-food"
											: p.category === "study"
												? "book"
												: "bus"
								}
								size={22}
								color="#2563eb"
							/>
							<View style={{ flex: 1 }}>
								<Text style={styles.poiName}>{p.name}</Text>
								<Text style={styles.poiMeta}>
									{p.building} · {p.floorKey}
								</Text>
							</View>
						</View>
					))}
				</ScrollView>
			) : null}

			<Pressable onPress={() => void Linking.openURL(REPO)} style={styles.footerLink}>
				<Ionicons name="logo-github" size={16} color="#64748b" />
				<Text style={styles.footerLinkTxt}>SOEN390 reference repo</Text>
			</Pressable>

			<Modal visible={lectureModal !== null} transparent animationType="fade">
				<Pressable style={styles.modalBackdrop} onPress={() => setLectureModal(null)}>
					<Pressable style={styles.modalCard} onPress={(e) => e.stopPropagation()}>
						{lectureModal ? (
							<>
								<Text style={styles.modalTitle}>{lectureModal.title}</Text>
								<Text style={styles.modalMeta}>
									{lectureModal.courseCode} · {lectureModal.roomRaw}
								</Text>
								<Text style={styles.modalSection}>Directions (demo)</Text>
								{mockDirections(scanForRoom(lectureModal.roomRaw) ?? lectureModal.roomRaw).map((s, i) => (
									<Text key={i} style={styles.step}>
										{i + 1}. {s}
									</Text>
								))}
								<View style={styles.modalActions}>
									<Pressable onPress={() => setLectureModal(null)} style={styles.modalClose}>
										<Text style={styles.modalCloseTxt}>Close</Text>
									</Pressable>
									<Pressable
										onPress={() => {
											setLectureModal(null);
											router.push("/main/navigation");
										}}
										style={styles.modalNav}
									>
										<Text style={styles.modalNavTxt}>Open nav</Text>
									</Pressable>
								</View>
							</>
						) : null}
					</Pressable>
				</Pressable>
			</Modal>
		</View>
	);
}

const styles = StyleSheet.create({
	root: { flex: 1, backgroundColor: "#f8fafc" },
	hero: { paddingHorizontal: 16, paddingBottom: 8 },
	title: { fontSize: 26, fontWeight: "900", color: "#0f172a" },
	sub: { marginTop: 4, fontSize: 14, color: "#64748b" },
	segment: {
		flexDirection: "row",
		marginHorizontal: 16,
		backgroundColor: "#e2e8f0",
		borderRadius: 14,
		padding: 4,
		gap: 4,
	},
	segBtn: { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: "center" },
	segBtnOn: { backgroundColor: "#fff", shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 6, elevation: 2 },
	segTxt: { fontWeight: "700", color: "#64748b", fontSize: 13 },
	segTxtOn: { color: "#0f172a" },
	scrollPad: { padding: 16, paddingBottom: 80 },
	listPad: { padding: 16, paddingBottom: 80, gap: 10 },
	cardTitle: { fontSize: 16, fontWeight: "800", color: "#0f172a" },
	cardHint: { marginTop: 4, fontSize: 13, color: "#64748b", marginBottom: 10 },
	mapWrap: {
		alignSelf: "center",
		borderRadius: 16,
		overflow: "hidden",
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	buildingPick: {
		flexDirection: "row",
		flexWrap: "wrap",
		gap: 8,
		marginTop: 12,
		justifyContent: "center",
	},
	buildingPill: {
		paddingHorizontal: 12,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#fff",
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	buildingPillOn: { borderColor: "#2563eb", backgroundColor: "#eff6ff" },
	buildingPillTxt: { fontWeight: "700", color: "#475569", fontSize: 12 },
	buildingPillTxtOn: { color: "#1d4ed8" },
	section: { marginTop: 18, marginBottom: 8, fontSize: 12, fontWeight: "800", color: "#64748b" },
	floorRow: { maxHeight: 44 },
	floorChip: {
		paddingHorizontal: 14,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#fff",
		marginRight: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	floorChipOn: { borderColor: "#2563eb", backgroundColor: "#eff6ff" },
	floorChipTxt: { fontWeight: "700", color: "#475569", fontSize: 13 },
	floorChipTxtOn: { color: "#1d4ed8" },
	btnRow: { flexDirection: "row", gap: 10, marginTop: 16 },
	primary: {
		flex: 1,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 8,
		backgroundColor: "#2563eb",
		paddingVertical: 14,
		borderRadius: 12,
	},
	primaryTxt: { color: "#fff", fontWeight: "800", fontSize: 15 },
	outdoor: {
		flex: 1,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 8,
		backgroundColor: "#e2e8f0",
		paddingVertical: 14,
		borderRadius: 12,
	},
	outdoorTxt: { color: "#0f172a", fontWeight: "800", fontSize: 14 },
	lecCard: {
		backgroundColor: "#fff",
		borderRadius: 14,
		padding: 14,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		marginBottom: 10,
	},
	lecTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
	lecCode: { fontWeight: "800", color: "#2563eb", fontSize: 13 },
	lecTime: { fontSize: 12, color: "#64748b", fontWeight: "600" },
	lecTitle: { marginTop: 8, fontSize: 17, fontWeight: "800", color: "#0f172a" },
	lecRoom: { marginTop: 6, fontSize: 14, color: "#475569" },
	input: {
		borderWidth: 1,
		borderColor: "#e2e8f0",
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 12,
		fontSize: 16,
		backgroundColor: "#fff",
		color: "#0f172a",
	},
	parseBanner: {
		marginTop: 10,
		padding: 12,
		borderRadius: 12,
		backgroundColor: "#eff6ff",
		borderWidth: 1,
		borderColor: "#bfdbfe",
	},
	parseLbl: { fontSize: 11, fontWeight: "800", color: "#1d4ed8", textTransform: "uppercase" },
	parseVal: { marginTop: 4, fontSize: 18, fontWeight: "900", color: "#0f172a" },
	filterRow: { maxHeight: 44, marginTop: 12, marginBottom: 8 },
	filterChip: {
		paddingHorizontal: 12,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#fff",
		marginRight: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	filterChipOn: { backgroundColor: "#0f172a", borderColor: "#0f172a" },
	filterTxt: { fontWeight: "700", color: "#475569", fontSize: 12, textTransform: "capitalize" },
	filterTxtOn: { color: "#fff" },
	poiRow: {
		flexDirection: "row",
		alignItems: "center",
		gap: 12,
		padding: 14,
		backgroundColor: "#fff",
		borderRadius: 12,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		marginBottom: 8,
	},
	poiName: { fontSize: 15, fontWeight: "800", color: "#0f172a" },
	poiMeta: { marginTop: 2, fontSize: 12, color: "#64748b", fontWeight: "600" },
	footerLink: {
		position: "absolute",
		bottom: 12,
		left: 16,
		right: 16,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 6,
		paddingVertical: 8,
	},
	footerLinkTxt: { color: "#64748b", fontSize: 12, fontWeight: "600" },
	modalBackdrop: {
		flex: 1,
		backgroundColor: "rgba(15,23,42,0.45)",
		justifyContent: "center",
		padding: 24,
	},
	modalCard: {
		backgroundColor: "#fff",
		borderRadius: 16,
		padding: 18,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	modalTitle: { fontSize: 18, fontWeight: "900", color: "#0f172a" },
	modalMeta: { marginTop: 6, fontSize: 14, color: "#64748b", fontWeight: "600" },
	modalSection: { marginTop: 14, marginBottom: 8, fontSize: 12, fontWeight: "800", color: "#475569" },
	step: { fontSize: 14, color: "#334155", lineHeight: 20, marginBottom: 6 },
	modalActions: { flexDirection: "row", gap: 10, marginTop: 16 },
	modalClose: {
		flex: 1,
		paddingVertical: 12,
		borderRadius: 10,
		backgroundColor: "#f1f5f9",
		alignItems: "center",
	},
	modalCloseTxt: { fontWeight: "800", color: "#334155" },
	modalNav: { flex: 1, paddingVertical: 12, borderRadius: 10, backgroundColor: "#2563eb", alignItems: "center" },
	modalNavTxt: { fontWeight: "800", color: "#fff" },
});
