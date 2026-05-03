import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
	ActivityIndicator,
	FlatList,
	Modal,
	Platform,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	View,
	useWindowDimensions,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import {
	cacheDirectory,
	EncodingType,
	readAsStringAsync,
	writeAsStringAsync,
} from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { CameraView, useCameraPermissions } from "expo-camera";

import { BUNDLED_DEFAULT_BUILDING, BUNDLED_SAMPLE_CAMPUS, resolveIndoorBundle } from "@/lib/indoor-nav/bundles";
import { EditorPanel, type EditorSelection } from "@/lib/indoor-nav/EditorPanel";
import { MapCanvas, type MapEdge, type RoomShapeMarker } from "@/lib/indoor-nav/MapCanvas";
import { buildIndoorInstructions } from "@/lib/indoor-nav/instructions";
import { parseBuildingJson, parseCampusJson, serializeBuilding, serializeCampus } from "@/lib/indoor-nav/parse";
import { findRoomsNear, getTodayEnglishName, lecturesForToday } from "@/lib/indoor-nav/proximity";
import { goalNodeIdForLocation, routeCampus, routeIndoor } from "@/lib/indoor-nav/routing";
import {
	loadString,
	removeKey,
	saveString,
	STORAGE_ACTIVE_BUILDING_JSON,
	STORAGE_ACTIVE_CAMPUS_JSON,
	STORAGE_NAV_MODE,
} from "@/lib/indoor-nav/storage";
import type { CampusMapV1, GraphNode, IndoorBuildingV1, IndoorLocation } from "@/lib/indoor-nav/types";

type NavMode = "indoor" | "campus";

type IndoorUiMode = "navigate" | "edit";

function isNavDestination(loc: IndoorLocation): boolean {
	if (loc.isNavObstacle) {
		return false;
	}
	if (loc.mapKind === "garden" || loc.mapKind === "corridor") {
		return false;
	}
	return true;
}

function boundsForFloor(building: IndoorBuildingV1, floor: number) {
	const nodes = building.graph.nodes.filter((n) => n.floor === floor);
	const rooms = building.locations.filter((l) => l.floor === floor);
	const xs: number[] = [];
	const ys: number[] = [];
	for (const n of nodes) {
		xs.push(n.position.x);
		ys.push(n.position.y);
	}
	for (const r of rooms) {
		xs.push(r.coordinates.x, r.coordinates.x + (r.size?.width ?? 0));
		ys.push(r.coordinates.y, r.coordinates.y + (r.size?.height ?? 0));
	}
	const pad = 2;
	if (xs.length === 0) {
		return { minX: 0, maxX: 20, minY: 0, maxY: 20 };
	}
	return {
		minX: Math.min(...xs) - pad,
		maxX: Math.max(...xs) + pad,
		minY: Math.min(...ys) - pad,
		maxY: Math.max(...ys) + pad,
	};
}

function campusBounds(c: CampusMapV1) {
	const pad = 3;
	const xs = c.nodes.map((n) => n.position.x);
	const ys = c.nodes.map((n) => n.position.y);
	return {
		minX: Math.min(0, ...xs) - pad,
		maxX: Math.max(c.bounds.width, ...xs) + pad,
		minY: Math.min(0, ...ys) - pad,
		maxY: Math.max(c.bounds.height, ...ys) + pad,
	};
}

function indoorEdgesForFloor(building: IndoorBuildingV1, floor: number): MapEdge[] {
	const byId = new Map(building.graph.nodes.map((n) => [n.id, n]));
	const out: MapEdge[] = [];
	for (const e of building.graph.edges) {
		const a = byId.get(e.from);
		const b = byId.get(e.to);
		if (!a || !b) {
			continue;
		}
		if (a.floor === floor && b.floor === floor) {
			out.push({ from: a.position, to: b.position });
		}
	}
	return out;
}

function routePointsOnFloor(path: string[], nodesById: Map<string, GraphNode>, floor: number) {
	const pts: { x: number; y: number }[] = [];
	for (const id of path) {
		const n = nodesById.get(id);
		if (n && n.floor === floor) {
			pts.push({ ...n.position });
		}
	}
	return pts;
}

function nextAlongPath(path: string[], currentNodeId: string | null): string | null {
	if (path.length === 0) {
		return null;
	}
	if (!currentNodeId) {
		return path[0] ?? null;
	}
	const idx = path.indexOf(currentNodeId);
	if (idx === -1) {
		return path[0] ?? null;
	}
	return path[idx + 1] ?? null;
}

function QrScannerModal(props: {
	visible: boolean;
	title: string;
	onClose: () => void;
	onScan: (data: string) => void;
}) {
	const [permission, requestPermission] = useCameraPermissions();
	const [manual, setManual] = useState("");
	const scanLock = useRef(false);

	useEffect(() => {
		if (props.visible) {
			scanLock.current = false;
			setManual("");
		}
	}, [props.visible]);

	const handleBarcode = useCallback(
		(e: { data: string }) => {
			if (scanLock.current) {
				return;
			}
			scanLock.current = true;
			props.onScan(e.data.trim());
			props.onClose();
		},
		[props],
	);

	return (
		<Modal visible={props.visible} animationType="slide" onRequestClose={props.onClose}>
			<View style={qrStyles.wrap}>
				<View style={qrStyles.header}>
					<Text style={qrStyles.title}>{props.title}</Text>
					<Pressable onPress={props.onClose} hitSlop={12}>
						<Ionicons name="close" size={28} color="#111" />
					</Pressable>
				</View>
				{Platform.OS !== "web" && permission && !permission.granted && (
					<Pressable style={qrStyles.permBtn} onPress={() => void requestPermission()}>
						<Text style={qrStyles.permText}>Allow camera to scan QR checkpoints</Text>
					</Pressable>
				)}
				{Platform.OS !== "web" && permission?.granted && (
					<View style={qrStyles.camBox}>
						<CameraView
							style={StyleSheet.absoluteFill}
							facing="back"
							barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
							onBarcodeScanned={handleBarcode}
						/>
					</View>
				)}
				<Text style={qrStyles.hint}>Or enter checkpoint payload manually:</Text>
				<TextInput
					value={manual}
					onChangeText={setManual}
					placeholder="e.g. nav:checkpoint:f0_entrance"
					autoCapitalize="none"
					style={qrStyles.input}
				/>
				<Pressable
					style={qrStyles.apply}
					onPress={() => {
						if (manual.trim()) {
							props.onScan(manual.trim());
							props.onClose();
						}
					}}
				>
					<Text style={qrStyles.applyText}>Use manual value</Text>
				</Pressable>
			</View>
		</Modal>
	);
}

const qrStyles = StyleSheet.create({
	wrap: { flex: 1, padding: 16, paddingTop: 48, backgroundColor: "#fff" },
	header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
	title: { fontSize: 18, fontWeight: "700", color: "#111" },
	permBtn: { marginTop: 12, padding: 12, backgroundColor: "#e0f2fe", borderRadius: 10 },
	permText: { color: "#0369a1", fontWeight: "600", textAlign: "center" },
	camBox: { marginTop: 12, height: 280, borderRadius: 12, overflow: "hidden", backgroundColor: "#000" },
	hint: { marginTop: 16, color: "#475569", fontSize: 13 },
	input: {
		marginTop: 8,
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderRadius: 10,
		padding: 12,
		fontSize: 15,
	},
	apply: {
		marginTop: 12,
		backgroundColor: "#2563eb",
		paddingVertical: 14,
		borderRadius: 12,
		alignItems: "center",
	},
	applyText: { color: "#fff", fontWeight: "700" },
});

export default function IndoorNavScreen() {
	const insets = useSafeAreaInsets();
	const { width: winW } = useWindowDimensions();
	const mapW = Math.min(winW - 32, 420);
	const mapH = 280;

	const [mode, setMode] = useState<NavMode>("indoor");
	const [indoorUiMode, setIndoorUiMode] = useState<IndoorUiMode>("navigate");
	const [editorSelection, setEditorSelection] = useState<EditorSelection>(null);
	const [building, setBuilding] = useState<IndoorBuildingV1>(BUNDLED_DEFAULT_BUILDING);
	const [campus, setCampus] = useState<CampusMapV1>(BUNDLED_SAMPLE_CAMPUS);
	const [viewedFloor, setViewedFloor] = useState(() => BUNDLED_DEFAULT_BUILDING.graph.nodes[0]?.floor ?? 0);
	const [currentNodeId, setCurrentNodeId] = useState(
		() => BUNDLED_DEFAULT_BUILDING.graph.nodes[0]?.id ?? "node_0",
	);
	const [campusNodeId, setCampusNodeId] = useState<string>("c_gate");
	const [destinationId, setDestinationId] = useState<string | null>(null);
	const [campusDestEntranceId, setCampusDestEntranceId] = useState<string | null>(null);
	const [indoorPath, setIndoorPath] = useState<string[]>([]);
	const [campusPath, setCampusPath] = useState<string[]>([]);
	const [stepIndex, setStepIndex] = useState(0);
	const [search, setSearch] = useState("");
	const [settingsOpen, setSettingsOpen] = useState(false);
	const [qrOpen, setQrOpen] = useState(false);
	const [qrContext, setQrContext] = useState<NavMode>("indoor");
	const [statusMsg, setStatusMsg] = useState<string | null>(null);
	const [demoOpen, setDemoOpen] = useState(false);
	const [busy, setBusy] = useState(true);
	const [roomSheet, setRoomSheet] = useState<IndoorLocation | null>(null);
	const lastProximityId = useRef<string | null>(null);
	const prevCheckpointRef = useRef<string | null>(null);

	const nodesById = useMemo(
		() => new Map(building.graph.nodes.map((n) => [n.id, n])),
		[building.graph.nodes],
	);

	const destination = useMemo(
		() => building.locations.find((l) => l.id === destinationId) ?? null,
		[building.locations, destinationId],
	);

	const instructions = useMemo(() => {
		if (!destination || indoorPath.length === 0) {
			return [];
		}
		return buildIndoorInstructions(indoorPath, nodesById, destination);
	}, [destination, indoorPath, nodesById]);

	const currentPosition = useMemo(() => {
		const n = nodesById.get(currentNodeId);
		return n?.position ?? { x: 0, y: 0 };
	}, [currentNodeId, nodesById]);

	useEffect(() => {
		let cancelled = false;
		(async () => {
			setBusy(true);
			try {
				const [rawBuilding, rawCampus, rawMode] = await Promise.all([
					loadString(STORAGE_ACTIVE_BUILDING_JSON),
					loadString(STORAGE_ACTIVE_CAMPUS_JSON),
					loadString(STORAGE_NAV_MODE),
				]);
				if (cancelled) {
					return;
				}
				if (rawBuilding) {
					const parsed = parseBuildingJson(rawBuilding);
					if (parsed.ok) {
						setBuilding(parsed.data);
						const nid = parsed.data.graph.nodes[0]?.id ?? "node_0";
						setCurrentNodeId(nid);
						const nn = parsed.data.graph.nodes.find((x) => x.id === nid);
						if (nn) {
							setViewedFloor(nn.floor);
						}
						prevCheckpointRef.current = nid;
					}
				}
				if (rawCampus) {
					const pc = parseCampusJson(rawCampus);
					if (pc.ok) {
						setCampus(pc.data);
					}
				}
				if (rawMode === "campus" || rawMode === "indoor") {
					setMode(rawMode);
				}
			} finally {
				if (!cancelled) {
					setBusy(false);
				}
			}
		})();
		return () => {
			cancelled = true;
		};
	}, []);

	useEffect(() => {
		if (prevCheckpointRef.current === null) {
			prevCheckpointRef.current = currentNodeId;
			return;
		}
		if (prevCheckpointRef.current !== currentNodeId) {
			prevCheckpointRef.current = currentNodeId;
			const n = nodesById.get(currentNodeId);
			if (n) {
				setViewedFloor(n.floor);
			}
		}
	}, [currentNodeId, nodesById]);

	useEffect(() => {
		setStepIndex(0);
	}, [destinationId, indoorPath]);

	useEffect(() => {
		if (!destination) {
			setIndoorPath([]);
			return;
		}
		const path = routeIndoor(building, currentNodeId, destination);
		if (!path) {
			setIndoorPath([]);
			setStatusMsg("No route found. Try another checkpoint.");
			return;
		}
		setIndoorPath(path);
		setStatusMsg(null);
	}, [building, currentNodeId, destination]);

	useEffect(() => {
		if (mode !== "campus") {
			setCampusPath([]);
			return;
		}
		if (!campusDestEntranceId) {
			setCampusPath([]);
			return;
		}
		const p = routeCampus(campus, campusNodeId, campusDestEntranceId);
		setCampusPath(p ?? []);
	}, [mode, campus, campusNodeId, campusDestEntranceId]);

	useEffect(() => {
		const hits = findRoomsNear(building.locations, currentPosition);
		const top = hits[0];
		if (!top) {
			lastProximityId.current = null;
			return;
		}
		if (lastProximityId.current === top.id) {
			return;
		}
		lastProximityId.current = top.id;
		setRoomSheet(top);
	}, [building.locations, currentPosition]);

	const goalNodeId = destination ? goalNodeIdForLocation(destination, building.graph.nodes) : null;

	const nextNodeId = useMemo(
		() => nextAlongPath(indoorPath, currentNodeId),
		[indoorPath, currentNodeId],
	);

	const arrowDeg = useMemo(() => {
		const cur = nodesById.get(currentNodeId);
		const nextId = nextNodeId;
		if (!cur || !nextId) {
			return null;
		}
		const next = nodesById.get(nextId);
		if (!next) {
			return null;
		}
		const dx = next.position.x - cur.position.x;
		const dy = next.position.y - cur.position.y;
		return (Math.atan2(dy, dx) * 180) / Math.PI;
	}, [currentNodeId, nextNodeId, nodesById]);

	const bounds = useMemo(() => boundsForFloor(building, viewedFloor), [building, viewedFloor]);
	const edges = useMemo(() => indoorEdgesForFloor(building, viewedFloor), [building, viewedFloor]);
	const routePoints = useMemo(
		() => routePointsOnFloor(indoorPath, nodesById, viewedFloor),
		[indoorPath, nodesById, viewedFloor],
	);

	const mapNodes = useMemo(() => {
		return building.graph.nodes
			.filter((n) => n.floor === viewedFloor)
			.map((n) => ({ id: n.id, position: n.position, label: n.label }));
	}, [building.graph.nodes, viewedFloor]);

	const roomShapes = useMemo((): RoomShapeMarker[] => {
		return building.locations
			.filter((l) => l.floor === viewedFloor)
			.map((l) => ({
				id: l.id,
				position: l.coordinates,
				width: l.size?.width,
				height: l.size?.height,
				name: l.shortLabel ?? l.name,
				highlight: l.id === destinationId,
				selected:
					indoorUiMode === "edit" &&
					editorSelection?.kind === "location" &&
					editorSelection.id === l.id,
				mapKind: l.mapKind,
			}));
	}, [building.locations, viewedFloor, destinationId, indoorUiMode, editorSelection]);

	const filteredDestinations = useMemo(() => {
		const q = search.trim().toLowerCase();
		const list = building.locations
			.filter(isNavDestination)
			.sort((a, b) => a.name.localeCompare(b.name));
		if (!q) {
			return list;
		}
		return list.filter(
			(l) =>
				l.name.toLowerCase().includes(q) ||
				l.id.toLowerCase().includes(q) ||
				(l.description?.toLowerCase().includes(q) ?? false) ||
				(l.roomCode?.toLowerCase().includes(q) ?? false),
		);
	}, [building.locations, search]);

	const onImportBuilding = useCallback(async () => {
		try {
			const res = await DocumentPicker.getDocumentAsync({
				type: "application/json",
				copyToCacheDirectory: true,
			});
			if (res.canceled || !res.assets?.[0]?.uri) {
				return;
			}
			const text = await readAsStringAsync(res.assets[0].uri);
			const parsed = parseBuildingJson(text);
			if (!parsed.ok) {
				setStatusMsg(parsed.error);
				return;
			}
			setBuilding(parsed.data);
			await saveString(STORAGE_ACTIVE_BUILDING_JSON, serializeBuilding(parsed.data));
			const first = parsed.data.graph.nodes[0]?.id ?? "node_0";
			setCurrentNodeId(first);
			const nn = parsed.data.graph.nodes.find((n) => n.id === first);
			if (nn) {
				setViewedFloor(nn.floor);
			}
			prevCheckpointRef.current = first;
			setDestinationId(null);
			setStatusMsg("Building map loaded.");
		} catch {
			setStatusMsg("Import failed.");
		}
	}, []);

	const onImportCampus = useCallback(async () => {
		try {
			const res = await DocumentPicker.getDocumentAsync({
				type: "application/json",
				copyToCacheDirectory: true,
			});
			if (res.canceled || !res.assets?.[0]?.uri) {
				return;
			}
			const text = await readAsStringAsync(res.assets[0].uri);
			const parsed = parseCampusJson(text);
			if (!parsed.ok) {
				setStatusMsg(parsed.error);
				return;
			}
			setCampus(parsed.data);
			await saveString(STORAGE_ACTIVE_CAMPUS_JSON, serializeCampus(parsed.data));
			setStatusMsg("Campus map loaded.");
		} catch {
			setStatusMsg("Campus import failed.");
		}
	}, []);

	const resetBuilding = useCallback(async () => {
		await removeKey(STORAGE_ACTIVE_BUILDING_JSON);
		setBuilding(BUNDLED_DEFAULT_BUILDING);
		const nid = BUNDLED_DEFAULT_BUILDING.graph.nodes[0]?.id ?? "node_0";
		setCurrentNodeId(nid);
		setViewedFloor(BUNDLED_DEFAULT_BUILDING.graph.nodes[0]?.floor ?? 0);
		prevCheckpointRef.current = nid;
		setDestinationId(null);
		setStatusMsg("Reset to bundled default building.");
	}, []);

	const persistBuilding = useCallback(async () => {
		await saveString(STORAGE_ACTIVE_BUILDING_JSON, serializeBuilding(building));
		setStatusMsg("Building map saved on device.");
	}, [building]);

	const exportBuildingJson = useCallback(async () => {
		try {
			const safe = building.building.name.replace(/[^\w-]+/g, "_").slice(0, 40);
			const name = `building_${safe}_${Date.now()}.json`;
			const base = cacheDirectory;
			if (!base) {
				setStatusMsg("Cache directory unavailable.");
				return;
			}
			const uri = `${base}${name}`;
			await writeAsStringAsync(uri, serializeBuilding(building), {
				encoding: EncodingType.UTF8,
			});
			if (await Sharing.isAvailableAsync()) {
				await Sharing.shareAsync(uri, { mimeType: "application/json", dialogTitle: "Export building map" });
			} else {
				setStatusMsg(`Saved export to: ${uri}`);
			}
		} catch {
			setStatusMsg("Export failed.");
		}
	}, [building]);
	const resetCampus = useCallback(async () => {
		await removeKey(STORAGE_ACTIVE_CAMPUS_JSON);
		setCampus(BUNDLED_SAMPLE_CAMPUS);
		setStatusMsg("Reset to sample campus.");
	}, []);

	const persistMode = useCallback(async (m: NavMode) => {
		setMode(m);
		await saveString(STORAGE_NAV_MODE, m);
	}, []);

	const applyQrPayload = useCallback(
		(data: string) => {
			if (qrContext === "indoor") {
				const match = building.graph.nodes.find((n) => n.qrPayload && n.qrPayload === data);
				if (match) {
					setCurrentNodeId(match.id);
					setStatusMsg(`Checkpoint: ${match.label ?? match.id}`);
					return;
				}
				setStatusMsg("Unknown indoor checkpoint.");
				return;
			}
			const cMatch = campus.nodes.find((n) => n.qrPayload && n.qrPayload === data);
			if (cMatch) {
				setCampusNodeId(cMatch.id);
				setStatusMsg(`Campus checkpoint: ${cMatch.label ?? cMatch.id}`);
				return;
			}
			setStatusMsg("Unknown campus checkpoint.");
		},
		[building.graph.nodes, campus.nodes, qrContext],
	);

	const enterBuildingFromCampus = useCallback(
		(bid: string) => {
			const b = campus.buildings.find((x) => x.id === bid);
			if (!b) {
				return;
			}
			const indoor = resolveIndoorBundle(b.indoorBundleId);
			if (!indoor) {
				setStatusMsg(`No bundled indoor data for: ${b.indoorBundleId}`);
				return;
			}
			setBuilding(indoor);
			const start = indoor.graph.nodes.find((n) => n.id === b.indoorStartNodeId);
			setCurrentNodeId(b.indoorStartNodeId);
			if (start) {
				setViewedFloor(start.floor);
				prevCheckpointRef.current = b.indoorStartNodeId;
			}
			void persistMode("indoor");
			setStatusMsg(`Entered ${b.name}.`);
		},
		[campus.buildings, persistMode],
	);

	const campusBoundsMemo = useMemo(() => campusBounds(campus), [campus]);
	const campusEdges = useMemo(() => {
		const byId = new Map(campus.nodes.map((n) => [n.id, n]));
		return campus.edges
			.map((e) => {
				const a = byId.get(e.from);
				const b = byId.get(e.to);
				if (!a || !b) {
					return null;
				}
				return { from: a.position, to: b.position };
			})
			.filter((x): x is MapEdge => !!x);
	}, [campus]);

	const campusRoutePoints = useMemo(() => {
		const byId = new Map(campus.nodes.map((n) => [n.id, n]));
		return campusPath.map((id) => byId.get(id)!.position);
	}, [campus, campusPath]);

	const campusNodesMap = useMemo(
		() => campus.nodes.map((n) => ({ id: n.id, position: n.position, label: n.label })),
		[campus.nodes],
	);

	const campusArrowDeg = useMemo(() => {
		const byId = new Map(campus.nodes.map((n) => [n.id, n]));
		const cur = byId.get(campusNodeId);
		const nextId = nextAlongPath(campusPath, campusNodeId);
		const next = nextId ? byId.get(nextId) : null;
		if (!cur || !next) {
			return null;
		}
		const dx = next.position.x - cur.position.x;
		const dy = next.position.y - cur.position.y;
		return (Math.atan2(dy, dx) * 180) / Math.PI;
	}, [campus.nodes, campusNodeId, campusPath]);

	const onPathIncludesCurrent = indoorPath.length > 0 && !indoorPath.includes(currentNodeId);

	if (busy) {
		return (
			<View style={[styles.center, { paddingTop: insets.top }]}>
				<ActivityIndicator size="large" color="#2563eb" />
				<Text style={styles.muted}>Loading navigation…</Text>
			</View>
		);
	}

	return (
		<View style={[styles.root, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 8 }]}>
			<View style={styles.topRow}>
				<Text style={styles.screenTitle}>Indoor Nav</Text>
				<Pressable onPress={() => setSettingsOpen(true)} hitSlop={10} style={styles.iconBtn}>
					<Ionicons name="settings-outline" size={24} color="#0f172a" />
				</Pressable>
			</View>

			<View style={styles.segment}>
				<Pressable
					style={[styles.segBtn, mode === "indoor" && styles.segBtnOn]}
					onPress={() => void persistMode("indoor")}
				>
					<Text style={[styles.segTxt, mode === "indoor" && styles.segTxtOn]}>Indoor</Text>
				</Pressable>
				<Pressable
					style={[styles.segBtn, mode === "campus" && styles.segBtnOn]}
					onPress={() => void persistMode("campus")}
				>
					<Text style={[styles.segTxt, mode === "campus" && styles.segTxtOn]}>Campus</Text>
				</Pressable>
			</View>

			{statusMsg && (
				<View style={styles.banner}>
					<Text style={styles.bannerText}>{statusMsg}</Text>
					<Pressable onPress={() => setStatusMsg(null)}>
						<Ionicons name="close-circle" size={22} color="#0f172a" />
					</Pressable>
				</View>
			)}

			{mode === "indoor" ? (
				<ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
					<Text style={styles.buildingName}>{building.building.name}</Text>
					<View style={styles.segment}>
						<Pressable
							style={[styles.segBtn, indoorUiMode === "navigate" && styles.segBtnOn]}
							onPress={() => {
								setIndoorUiMode("navigate");
								setEditorSelection(null);
							}}
						>
							<Text style={[styles.segTxt, indoorUiMode === "navigate" && styles.segTxtOn]}>Navigate</Text>
						</Pressable>
						<Pressable
							style={[styles.segBtn, indoorUiMode === "edit" && styles.segBtnOn]}
							onPress={() => setIndoorUiMode("edit")}
						>
							<Text style={[styles.segTxt, indoorUiMode === "edit" && styles.segTxtOn]}>Edit map</Text>
						</Pressable>
					</View>
					<Text style={styles.muted}>Floor (view)</Text>
					<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.floorRow}>
						{[...new Set(building.graph.nodes.map((n) => n.floor))]
							.sort((a, b) => a - b)
							.map((f) => (
								<Pressable
									key={f}
									onPress={() => setViewedFloor(f)}
									style={[styles.chip, viewedFloor === f && styles.chipOn]}
								>
									<Text style={[styles.chipTxt, viewedFloor === f && styles.chipTxtOn]}>{f}</Text>
								</Pressable>
							))}
					</ScrollView>

					<MapCanvas
						width={mapW}
						height={mapH}
						bounds={bounds}
						nodes={mapNodes}
						edges={edges}
						routePoints={routePoints}
						roomShapes={roomShapes}
						currentId={currentNodeId}
						destinationId={goalNodeId}
						arrowDeg={arrowDeg}
					/>

					{indoorUiMode === "navigate" ? (
						<>
							<View style={styles.row}>
								<Pressable
									style={styles.btn}
									onPress={() => {
										setQrContext("indoor");
										setQrOpen(true);
									}}
								>
									<Ionicons name="qr-code-outline" size={20} color="#fff" />
									<Text style={styles.btnTxt}> Scan QR</Text>
								</Pressable>
								<Pressable style={styles.btnSecondary} onPress={() => setDemoOpen(true)}>
									<Ionicons name="location-outline" size={20} color="#0f172a" />
									<Text style={styles.btnSecondaryTxt}> Demo location</Text>
								</Pressable>
							</View>

							{onPathIncludesCurrent && (
								<Text style={styles.warn}>
									You are off the computed route. Pick a checkpoint on the route or rescan QR.
								</Text>
							)}

							<Text style={styles.section}>Destination</Text>
							<TextInput
								value={search}
								onChangeText={setSearch}
								placeholder="Search rooms…"
								style={styles.input}
							/>
							<FlatList
								data={filteredDestinations}
								keyExtractor={(item) => item.id}
								scrollEnabled={false}
								renderItem={({ item }) => (
									<Pressable
										style={[styles.destRow, destinationId === item.id && styles.destRowOn]}
										onPress={() => setDestinationId(item.id)}
									>
										<Text style={styles.destName}>{item.name}</Text>
										<Text style={styles.destMeta}>
											Floor {item.floor}
											{item.roomCode ? ` · ${item.roomCode}` : ""}
										</Text>
									</Pressable>
								)}
							/>

							<Text style={styles.section}>Guide</Text>
							{instructions.length === 0 ? (
								<Text style={styles.muted}>Select a destination to see step-by-step guidance.</Text>
							) : (
								<View style={styles.guideCard}>
									<Text style={styles.guideStep}>
										Step {Math.min(stepIndex + 1, instructions.length)} / {instructions.length}
									</Text>
									<Text style={styles.guideBody}>
										{instructions[Math.min(stepIndex, instructions.length - 1)]}
									</Text>
									<View style={styles.row}>
										<Pressable
											style={styles.btnSecondary}
											onPress={() => setStepIndex((i) => Math.max(0, i - 1))}
										>
											<Text style={styles.btnSecondaryTxt}>Back</Text>
										</Pressable>
										<Pressable
											style={styles.btn}
											onPress={() => setStepIndex((i) => Math.min(instructions.length - 1, i + 1))}
										>
											<Text style={styles.btnTxt}>Next</Text>
										</Pressable>
									</View>
								</View>
							)}
						</>
					) : (
						<EditorPanel
							building={building}
							setBuilding={setBuilding}
							viewedFloor={viewedFloor}
							setViewedFloor={setViewedFloor}
							selection={editorSelection}
							setSelection={setEditorSelection}
							onPersist={persistBuilding}
							setStatusMsg={setStatusMsg}
						/>
					)}
				</ScrollView>
			) : (
				<ScrollView contentContainerStyle={styles.scroll}>
					<Text style={styles.buildingName}>{campus.name}</Text>
					<MapCanvas
						width={mapW}
						height={mapH}
						bounds={campusBoundsMemo}
						nodes={campusNodesMap}
						edges={campusEdges}
						routePoints={campusRoutePoints}
						currentId={campusNodeId}
						destinationId={campusDestEntranceId}
						arrowDeg={campusArrowDeg}
					/>
					<View style={styles.row}>
						<Pressable
							style={styles.btn}
							onPress={() => {
								setQrContext("campus");
								setQrOpen(true);
							}}
						>
							<Ionicons name="qr-code-outline" size={20} color="#fff" />
							<Text style={styles.btnTxt}> Scan QR</Text>
						</Pressable>
						<Pressable style={styles.btnSecondary} onPress={() => setDemoOpen(true)}>
							<Text style={styles.btnSecondaryTxt}>Demo campus node</Text>
						</Pressable>
					</View>
					<Text style={styles.section}>Destination building</Text>
					{campus.buildings.map((b) => (
						<Pressable
							key={b.id}
							style={[styles.destRow, campusDestEntranceId === b.entranceNodeId && styles.destRowOn]}
							onPress={() => setCampusDestEntranceId(b.entranceNodeId)}
						>
							<Text style={styles.destName}>{b.name}</Text>
							<Text style={styles.destMeta}>Entrance node</Text>
						</Pressable>
					))}
					{campusDestEntranceId && (
						<Pressable
							style={[styles.btn, { marginTop: 12 }]}
							onPress={() => {
								const b = campus.buildings.find((x) => x.entranceNodeId === campusDestEntranceId);
								if (b) {
									enterBuildingFromCampus(b.id);
								}
							}}
						>
							<Text style={styles.btnTxt}>Enter selected building</Text>
						</Pressable>
					)}
				</ScrollView>
			)}

			<QrScannerModal
				visible={qrOpen}
				title={qrContext === "indoor" ? "Scan indoor checkpoint" : "Scan campus checkpoint"}
				onClose={() => setQrOpen(false)}
				onScan={applyQrPayload}
			/>

			<Modal visible={demoOpen} animationType="fade" transparent>
				<Pressable style={styles.modalBackdrop} onPress={() => setDemoOpen(false)}>
					<Pressable style={styles.modalCard} onPress={(e) => e.stopPropagation()}>
						<Text style={styles.modalTitle}>
							{mode === "indoor" ? "Demo: pick checkpoint" : "Demo: campus node"}
						</Text>
						<ScrollView style={{ maxHeight: 360 }}>
							{(mode === "indoor" ? building.graph.nodes : campus.nodes).map((n) => (
								<Pressable
									key={n.id}
									style={styles.demoRow}
									onPress={() => {
										if (mode === "indoor") {
											const gn = n as GraphNode;
											setCurrentNodeId(gn.id);
										} else {
											setCampusNodeId(n.id);
										}
										setDemoOpen(false);
									}}
								>
									<Text style={styles.destName}>{("label" in n && n.label) || n.id}</Text>
									{"floor" in n && typeof n.floor === "number" && (
										<Text style={styles.destMeta}>Floor {n.floor}</Text>
									)}
								</Pressable>
							))}
						</ScrollView>
						<Pressable style={styles.btnSecondary} onPress={() => setDemoOpen(false)}>
							<Text style={styles.btnSecondaryTxt}>Close</Text>
						</Pressable>
					</Pressable>
				</Pressable>
			</Modal>

			<Modal visible={settingsOpen} animationType="slide" presentationStyle="pageSheet">
				<View style={[styles.settingsWrap, { paddingTop: insets.top + 12 }]}>
					<View style={styles.topRow}>
						<Text style={styles.screenTitle}>Navigation data</Text>
						<Pressable onPress={() => setSettingsOpen(false)}>
							<Text style={styles.link}>Done</Text>
						</Pressable>
					</View>
					<Text style={styles.muted}>
						Import JSON maps. Legacy repo `navigation.json` (locations only) is auto-upgraded with a simple
						graph.
					</Text>
					<Pressable style={styles.btn} onPress={onImportBuilding}>
						<Text style={styles.btnTxt}>Import building JSON</Text>
					</Pressable>
					<Pressable style={styles.btn} onPress={onImportCampus}>
						<Text style={styles.btnTxt}>Import campus JSON</Text>
					</Pressable>
					<Pressable style={styles.btnSecondary} onPress={resetBuilding}>
						<Text style={styles.btnSecondaryTxt}>Reset building to bundled default</Text>
					</Pressable>
					<Pressable style={styles.btnSecondary} onPress={resetCampus}>
						<Text style={styles.btnSecondaryTxt}>Reset campus to bundled sample</Text>
					</Pressable>
					<Pressable style={styles.btn} onPress={() => void persistBuilding()}>
						<Text style={styles.btnTxt}>Save building map (device)</Text>
					</Pressable>
					<Pressable style={styles.btn} onPress={() => void exportBuildingJson()}>
						<Text style={styles.btnTxt}>Export building JSON</Text>
					</Pressable>
				</View>
			</Modal>

			<Modal visible={!!roomSheet} animationType="slide" transparent>
				<Pressable style={styles.modalBackdrop} onPress={() => setRoomSheet(null)}>
					<Pressable style={styles.sheet} onPress={(e) => e.stopPropagation()}>
						{roomSheet && (
							<>
								<Text style={styles.sheetTitle}>{roomSheet.name}</Text>
								<Text style={styles.muted}>{roomSheet.description}</Text>
								{roomSheet.staff && roomSheet.staff.length > 0 && (
									<>
										<Text style={styles.section}>Teaching assistants</Text>
										{roomSheet.staff.map((s) => (
											<View key={s.email ?? s.name} style={styles.sheetBlock}>
												<Text style={styles.destName}>{s.name}</Text>
												<Text style={styles.destMeta}>
													{s.role}
													{s.deskLabel ? ` · ${s.deskLabel}` : ""}
												</Text>
												<Text style={styles.destMeta}>Hours: {s.officeHours ?? "—"}</Text>
												<Text style={styles.destMeta}>
													Days: {(s.officeDays ?? []).join(", ") || "—"}
												</Text>
												<Text style={styles.destMeta}>
													Courses: {(s.coursesTaught ?? []).join(", ") || "—"}
												</Text>
											</View>
										))}
									</>
								)}
								{roomSheet.lectures && roomSheet.lectures.length > 0 && (
									<>
										<Text style={styles.section}>Today ({getTodayEnglishName()})</Text>
										{lecturesForToday(roomSheet.lectures).length === 0 ? (
											<Text style={styles.muted}>No lectures scheduled today.</Text>
										) : (
											lecturesForToday(roomSheet.lectures).map((lec) => (
												<View key={`${lec.courseCode}-${lec.startTime}`} style={styles.sheetBlock}>
													<Text style={styles.destName}>
														{lec.courseName} {lec.courseCode ? `(${lec.courseCode})` : ""}
													</Text>
													<Text style={styles.destMeta}>
														{lec.instructor} · {lec.startTime}–{lec.endTime}
													</Text>
												</View>
											))
										)}
										<Text style={styles.section}>All scheduled</Text>
										{roomSheet.lectures.map((lec) => (
											<Text key={`${lec.day}-${lec.courseCode}-${lec.startTime}`} style={styles.destMeta}>
												{lec.day}: {lec.courseName} — {lec.instructor} ({lec.startTime}–{lec.endTime})
											</Text>
										))}
									</>
								)}
								{(!roomSheet.staff || roomSheet.staff.length === 0) &&
									(!roomSheet.lectures || roomSheet.lectures.length === 0) && (
										<Text style={styles.destMeta}>{roomSheet.additional_info ?? ""}</Text>
									)}
								<Pressable style={[styles.btn, { marginTop: 12 }]} onPress={() => setRoomSheet(null)}>
									<Text style={styles.btnTxt}>Close</Text>
								</Pressable>
							</>
						)}
					</Pressable>
				</Pressable>
			</Modal>
		</View>
	);
}

const styles = StyleSheet.create({
	root: { flex: 1, backgroundColor: "#fff", paddingHorizontal: 16 },
	center: { flex: 1, justifyContent: "center", alignItems: "center", gap: 12 },
	scroll: { paddingBottom: 32 },
	topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
	screenTitle: { fontSize: 22, fontWeight: "800", color: "#0f172a" },
	iconBtn: { padding: 6 },
	segment: {
		flexDirection: "row",
		marginTop: 12,
		backgroundColor: "#e2e8f0",
		borderRadius: 12,
		padding: 4,
	},
	segBtn: { flex: 1, paddingVertical: 10, alignItems: "center", borderRadius: 10 },
	segBtnOn: { backgroundColor: "#fff" },
	segTxt: { color: "#64748b", fontWeight: "600" },
	segTxtOn: { color: "#0f172a" },
	banner: {
		marginTop: 10,
		padding: 10,
		backgroundColor: "#fef9c3",
		borderRadius: 10,
		flexDirection: "row",
		justifyContent: "space-between",
		alignItems: "center",
		gap: 8,
	},
	bannerText: { flex: 1, color: "#713f12", fontSize: 13 },
	buildingName: { fontSize: 18, fontWeight: "700", marginTop: 8, color: "#0f172a" },
	muted: { color: "#64748b", fontSize: 13, marginTop: 4 },
	floorRow: { marginTop: 8, marginBottom: 8 },
	chip: {
		paddingHorizontal: 14,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#f1f5f9",
		marginRight: 8,
	},
	chipOn: { backgroundColor: "#2563eb" },
	chipTxt: { fontWeight: "600", color: "#334155" },
	chipTxtOn: { color: "#fff" },
	row: { flexDirection: "row", gap: 10, marginTop: 10 },
	btn: {
		flex: 1,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		backgroundColor: "#2563eb",
		paddingVertical: 12,
		borderRadius: 12,
		gap: 6,
	},
	btnTxt: { color: "#fff", fontWeight: "700" },
	btnSecondary: {
		flex: 1,
		alignItems: "center",
		justifyContent: "center",
		borderWidth: 1,
		borderColor: "#cbd5e1",
		paddingVertical: 12,
		borderRadius: 12,
		flexDirection: "row",
		gap: 6,
	},
	btnSecondaryTxt: { color: "#0f172a", fontWeight: "600" },
	warn: { marginTop: 8, color: "#b45309", fontSize: 13 },
	section: { marginTop: 16, fontSize: 15, fontWeight: "700", color: "#0f172a" },
	input: {
		marginTop: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 10,
		fontSize: 15,
	},
	destRow: {
		paddingVertical: 12,
		borderBottomWidth: StyleSheet.hairlineWidth,
		borderBottomColor: "#e2e8f0",
	},
	destRowOn: { backgroundColor: "#eff6ff" },
	destName: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
	destMeta: { fontSize: 13, color: "#64748b", marginTop: 2 },
	guideCard: {
		marginTop: 8,
		padding: 14,
		backgroundColor: "#f8fafc",
		borderRadius: 12,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	guideStep: { fontSize: 12, color: "#64748b", fontWeight: "600" },
	guideBody: { marginTop: 8, fontSize: 16, color: "#0f172a", lineHeight: 22 },
	modalBackdrop: {
		flex: 1,
		backgroundColor: "rgba(15,23,42,0.45)",
		justifyContent: "center",
		padding: 20,
	},
	modalCard: {
		backgroundColor: "#fff",
		borderRadius: 16,
		padding: 16,
		maxHeight: "80%",
	},
	modalTitle: { fontSize: 17, fontWeight: "700", marginBottom: 8, color: "#0f172a" },
	demoRow: { paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: "#e2e8f0" },
	settingsWrap: { flex: 1, paddingHorizontal: 16, gap: 12 },
	link: { color: "#2563eb", fontWeight: "700", fontSize: 16 },
	sheet: {
		backgroundColor: "#fff",
		borderTopLeftRadius: 18,
		borderTopRightRadius: 18,
		padding: 20,
		maxHeight: "70%",
		marginTop: "auto",
	},
	sheetTitle: { fontSize: 20, fontWeight: "800", color: "#0f172a" },
	sheetBlock: {
		marginTop: 10,
		paddingBottom: 8,
		borderBottomWidth: StyleSheet.hairlineWidth,
		borderBottomColor: "#f1f5f9",
	},
});
