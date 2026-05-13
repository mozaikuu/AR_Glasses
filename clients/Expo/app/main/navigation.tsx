/**
 * Indoor navigation MVP (Megaprompt mobile flow).
 * Multi-floor: loads `uni-bundle.json`; single-floor degenerates to one slab.
 */
import buildingBundleJson from "@/assets/navigation/uni/uni-bundle.json";
import {
	mapBounds,
	mapsByFloorIndex,
	nearestNodeId,
	nodeIdsToPolyline,
	parseBuildingBundle,
	routeBetweenNodeIds,
	routeLegsTotalLength,
	routeMultiFloor,
} from "@/lib/navigation-mvp";
import type { MvpLabel, NavigationMvpBundleV1, NavigationMvpMapV1, RouteLeg, Vec2 } from "@/lib/navigation-mvp";
import { Ionicons } from "@expo/vector-icons";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Modal,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	useWindowDimensions,
	View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle, G, Line, Polygon, Polyline, Rect, Text as SvgText } from "react-native-svg";

type DestKey = string;

type DestItem = { key: DestKey; title: string; subtitle: string };

const bundleParsed = parseBuildingBundle(buildingBundleJson);

function cloneBundle(b: NavigationMvpBundleV1): NavigationMvpBundleV1 {
	return JSON.parse(JSON.stringify(b)) as NavigationMvpBundleV1;
}

function makeDestKey(floor: number, kind: "label" | "poi" | "node", id: string): DestKey {
	return `${floor}|${kind}:${id}`;
}

function parseDestKey(k: DestKey): { floor: number; kind: string; id: string } | null {
	const pipe = k.indexOf("|");
	if (pipe < 0) {
		return null;
	}
	const floor = Number(k.slice(0, pipe));
	const rest = k.slice(pipe + 1);
	const colon = rest.indexOf(":");
	if (colon < 0 || !Number.isInteger(floor)) {
		return null;
	}
	return { floor, kind: rest.slice(0, colon), id: rest.slice(colon + 1) };
}

function getMapForFloor(bundle: NavigationMvpBundleV1, floor: number): NavigationMvpMapV1 | null {
	const f = bundle.floors.find((fl) => fl.index === floor);
	return f?.map ?? null;
}

function mapToScreen(
	p: Vec2,
	b: { minX: number; minY: number; maxX: number; maxY: number },
	w: number,
	h: number,
	pad: number,
): Vec2 {
	const bw = Math.max(1e-6, b.maxX - b.minX);
	const bh = Math.max(1e-6, b.maxY - b.minY);
	const innerW = w - pad * 2;
	const innerH = h - pad * 2;
	return {
		x: pad + ((p.x - b.minX) / bw) * innerW,
		y: pad + ((p.y - b.minY) / bh) * innerH,
	};
}

function destKeyToNodeId(bundle: NavigationMvpBundleV1, key: DestKey): string | null {
	const p = parseDestKey(key);
	if (!p) {
		return null;
	}
	const map = getMapForFloor(bundle, p.floor);
	if (!map) {
		return null;
	}
	if (p.kind === "node") {
		return map.nodes.some((n) => n.id === p.id) ? p.id : null;
	}
	if (p.kind === "label") {
		const l = map.labels.find((x) => x.id === p.id);
		return l ? nearestNodeId(map, l.x, l.y) : null;
	}
	if (p.kind === "poi") {
		const po = map.pois.find((x) => x.id === p.id);
		return po ? nearestNodeId(map, po.x, po.y) : null;
	}
	return null;
}

function destTitle(bundle: NavigationMvpBundleV1, key: DestKey): string {
	const p = parseDestKey(key);
	if (!p) {
		return "";
	}
	const map = getMapForFloor(bundle, p.floor);
	if (!map) {
		return "";
	}
	const fl = bundle.floors.find((f) => f.index === p.floor);
	const suffix = bundle.floors.length > 1 && fl ? ` (${fl.level})` : "";
	if (p.kind === "node") {
		const n = map.nodes.find((x) => x.id === p.id);
		return `${n?.label ?? n?.id ?? p.id}${suffix}`;
	}
	if (p.kind === "label") {
		return `${map.labels.find((l) => l.id === p.id)?.text ?? p.id}${suffix}`;
	}
	const po = map.pois.find((x) => x.id === p.id);
	return `${po ? po.type.replace(/_/g, " ") : p.id}${suffix}`;
}

function buildDestListForFloor(map: NavigationMvpMapV1, floorIndex: number, multi: boolean): DestItem[] {
	const items: DestItem[] = [];
	for (const l of map.labels) {
		items.push({
			key: makeDestKey(floorIndex, "label", l.id),
			title: l.text,
			subtitle: multi ? "Room / area" : "Room / area",
		});
	}
	for (const p of map.pois) {
		items.push({
			key: makeDestKey(floorIndex, "poi", p.id),
			title: `${p.type.replace(/_/g, " ")}`,
			subtitle: "Point of interest",
		});
	}
	for (const n of map.nodes) {
		items.push({
			key: makeDestKey(floorIndex, "node", n.id),
			title: n.label ?? n.id,
			subtitle: "Path node",
		});
	}
	items.sort((a, b) => a.title.localeCompare(b.title));
	return items;
}

function filterDest(items: DestItem[], q: string): DestItem[] {
	const s = q.trim().toLowerCase();
	if (!s) {
		return items;
	}
	return items.filter((d) => d.title.toLowerCase().includes(s) || d.subtitle.toLowerCase().includes(s));
}

function LabelEditRow({
	label,
	floorIndex,
	onCommit,
}: {
	label: MvpLabel;
	floorIndex: number;
	onCommit: (floor: number, id: string, patch: { text?: string; x?: number; y?: number }) => void;
}) {
	const [text, setText] = useState(label.text);
	const [sx, setSx] = useState(String(label.x));
	const [sy, setSy] = useState(String(label.y));

	useEffect(() => {
		setText(label.text);
		setSx(String(label.x));
		setSy(String(label.y));
	}, [label.id, label.text, label.x, label.y]);

	const flush = () => {
		const x = Number.parseFloat(sx);
		const y = Number.parseFloat(sy);
		onCommit(floorIndex, label.id, {
			text,
			...(Number.isFinite(x) ? { x } : {}),
			...(Number.isFinite(y) ? { y } : {}),
		});
	};

	return (
		<View style={styles.labelEditCard}>
			<Text style={styles.labelEditId}>{label.id}</Text>
			<Text style={styles.labelEditFieldLbl}>Name</Text>
			<TextInput
				value={text}
				onChangeText={setText}
				onBlur={flush}
				style={styles.labelEditInput}
				placeholder="Label text"
				placeholderTextColor="#94a3b8"
			/>
			<Text style={styles.labelEditFieldLbl}>Position (map units)</Text>
			<View style={styles.labelEditXYRow}>
				<TextInput
					value={sx}
					onChangeText={setSx}
					onBlur={flush}
					style={[styles.labelEditInput, styles.labelEditHalf]}
					keyboardType="numbers-and-punctuation"
					placeholder="x"
					placeholderTextColor="#94a3b8"
				/>
				<TextInput
					value={sy}
					onChangeText={setSy}
					onBlur={flush}
					style={[styles.labelEditInput, styles.labelEditHalf]}
					keyboardType="numbers-and-punctuation"
					placeholder="y"
					placeholderTextColor="#94a3b8"
				/>
			</View>
		</View>
	);
}

export default function NavigationMvpTab() {
	const insets = useSafeAreaInsets();
	const { width: winW, height: winH } = useWindowDimensions();

	const [bundle, setBundle] = useState<NavigationMvpBundleV1 | null>(() =>
		bundleParsed.ok ? cloneBundle(bundleParsed.data) : null,
	);

	const multiFloor = (bundle?.floors.length ?? 0) > 1;

	const destItems = useMemo(() => {
		if (!bundle) {
			return [];
		}
		const out: DestItem[] = [];
		for (const fl of bundle.floors) {
			const part = buildDestListForFloor(fl.map, fl.index, multiFloor);
			for (const d of part) {
				out.push(
					multiFloor
						? { ...d, title: `${d.title} (${fl.level})`, subtitle: d.subtitle }
						: { ...d, title: d.title, subtitle: d.subtitle },
				);
			}
		}
		out.sort((a, b) => a.title.localeCompare(b.title));
		return out;
	}, [bundle, multiFloor]);

	const [activeFloorIndex, setActiveFloorIndex] = useState(0);
	const map = useMemo(() => (bundle ? getMapForFloor(bundle, activeFloorIndex) : null), [bundle, activeFloorIndex]);
	const bounds = useMemo(() => (map ? mapBounds(map) : null), [map]);

	const [search, setSearch] = useState("");
	const filtered = useMemo(() => filterDest(destItems, search), [destItems, search]);

	const [startKey, setStartKey] = useState<DestKey | null>(null);
	const [endKey, setEndKey] = useState<DestKey | null>(null);
	const [phase, setPhase] = useState<"pick" | "map">("pick");
	const [routeLegs, setRouteLegs] = useState<RouteLeg[] | null>(null);
	const [routeErr, setRouteErr] = useState<string | null>(null);

	const [menuOpen, setMenuOpen] = useState(false);
	const [labelEditOpen, setLabelEditOpen] = useState(false);
	const [editLabelsFloorIndex, setEditLabelsFloorIndex] = useState(0);

	const openLabelEditor = useCallback(() => {
		setMenuOpen(false);
		setEditLabelsFloorIndex(activeFloorIndex);
		setLabelEditOpen(true);
	}, [activeFloorIndex]);

	const mapsMap = useMemo(() => (bundle ? mapsByFloorIndex(bundle) : new Map()), [bundle]);

	const updateLabel = useCallback(
		(floorIndex: number, labelId: string, patch: { text?: string; x?: number; y?: number }) => {
			setBundle((prev) => {
				if (!prev) {
					return prev;
				}
				const next = cloneBundle(prev);
				const fl = next.floors.find((f) => f.index === floorIndex);
				if (!fl) {
					return prev;
				}
				const idx = fl.map.labels.findIndex((l) => l.id === labelId);
				if (idx < 0) {
					return prev;
				}
				const cur = fl.map.labels[idx]!;
				fl.map.labels[idx] = {
					...cur,
					...(patch.text !== undefined ? { text: patch.text } : {}),
					...(patch.x !== undefined && Number.isFinite(patch.x) ? { x: patch.x } : {}),
					...(patch.y !== undefined && Number.isFinite(patch.y) ? { y: patch.y } : {}),
				};
				return next;
			});
		},
		[],
	);

	const routePolyline = useMemo(() => {
		if (!bundle || !map || !routeLegs) {
			return [];
		}
		const leg = routeLegs.find((l) => l.floorIndex === activeFloorIndex);
		if (!leg || leg.nodeIds.length === 0) {
			return [];
		}
		return nodeIdsToPolyline(map, leg.nodeIds);
	}, [bundle, map, routeLegs, activeFloorIndex]);

	const routeDist = useMemo(() => {
		if (!bundle || !routeLegs) {
			return 0;
		}
		return routeLegsTotalLength(mapsMap, routeLegs);
	}, [bundle, routeLegs, mapsMap]);

	if (!bundle || !map || !bounds) {
		return (
			<View style={styles.centered}>
				<Text style={styles.title}>Navigation</Text>
				<Text style={styles.muted}>{bundleParsed.ok ? "Building bundle failed to load." : bundleParsed.error}</Text>
			</View>
		);
	}

	const mapW = Math.min(winW - 24, 560);
	const mapH = Math.min(Math.max(280, winH * 0.46), 460);
	const pad = 14;

	const toS = (p: Vec2) => mapToScreen(p, bounds, mapW, mapH, pad);
	const routePts = routePolyline.map(toS).map((p) => `${p.x},${p.y}`).join(" ");

	const computeRoute = () => {
		setRouteErr(null);
		if (!startKey || !endKey || startKey === endKey) {
			setRouteErr("Pick two different places.");
			return;
		}
		const ps = parseDestKey(startKey);
		const pe = parseDestKey(endKey);
		if (!ps || !pe) {
			setRouteErr("Invalid selection.");
			return;
		}
		const a = destKeyToNodeId(bundle, startKey);
		const b = destKeyToNodeId(bundle, endKey);
		if (!a || !b) {
			setRouteErr("Could not snap selection to the walk graph.");
			return;
		}
		if (ps.floor === pe.floor) {
			const m = getMapForFloor(bundle, ps.floor);
			if (!m) {
				setRouteErr("Missing floor map.");
				return;
			}
			const path = routeBetweenNodeIds(m, a, b);
			if (!path || path.length === 0) {
				setRouteErr("No path found between those points.");
				return;
			}
			setRouteLegs([{ floorIndex: ps.floor, nodeIds: path }]);
			setActiveFloorIndex(ps.floor);
			setPhase("map");
			return;
		}
		const legs = routeMultiFloor(mapsMap, bundle.stairs, ps.floor, pe.floor, a, b);
		if (!legs) {
			setRouteErr("No multi-floor path (missing stair links between those floors).");
			return;
		}
		setRouteLegs(legs);
		setActiveFloorIndex(ps.floor);
		setPhase("map");
	};

	const resetFlow = () => {
		setPhase("pick");
		setRouteLegs(null);
		setRouteErr(null);
	};

	const clearRoute = () => setRouteLegs(null);

	const endParsed = endKey ? parseDestKey(endKey) : null;
	const destName = endKey ? destTitle(bundle, endKey) : "";
	const crossHint =
		routeLegs && routeLegs.length > 1 ? ` ${routeLegs.length} legs — use floor tabs to view each segment.` : "";

	const floorForLabelEdit = bundle.floors.find((f) => f.index === editLabelsFloorIndex) ?? bundle.floors[0]!;
	const labelsBeingEdited = floorForLabelEdit.map.labels;

	const navModals = (
		<>
			<Modal visible={menuOpen} transparent animationType="fade" onRequestClose={() => setMenuOpen(false)}>
				<View style={styles.menuOverlay}>
					<Pressable style={StyleSheet.absoluteFillObject} onPress={() => setMenuOpen(false)} />
					<View style={[styles.menuSheet, { top: insets.top + 44 }]}>
						<Pressable onPress={openLabelEditor} style={styles.menuItem}>
							<Ionicons name="create-outline" size={20} color="#334155" />
							<Text style={styles.menuItemTxt}>Edit labels</Text>
						</Pressable>
					</View>
				</View>
			</Modal>
			<Modal visible={labelEditOpen} animationType="slide" onRequestClose={() => setLabelEditOpen(false)}>
				<View style={[styles.labelModalRoot, { paddingTop: insets.top + 8, paddingBottom: insets.bottom + 16 }]}>
					<View style={styles.labelModalHeader}>
						<Text style={styles.labelModalTitle}>Edit labels</Text>
						<Pressable onPress={() => setLabelEditOpen(false)} hitSlop={12}>
							<Text style={styles.labelModalDone}>Done</Text>
						</Pressable>
					</View>
					{multiFloor ? (
						<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.labelModalTabs}>
							{bundle.floors.map((fl) => (
								<Pressable
									key={fl.index}
									onPress={() => setEditLabelsFloorIndex(fl.index)}
									style={[
										styles.floorPill,
										editLabelsFloorIndex === fl.index && styles.floorPillOn,
										styles.labelModalTabPill,
									]}
								>
									<Text style={[styles.floorPillTxt, editLabelsFloorIndex === fl.index && styles.floorPillTxtOn]}>
										{fl.level}
									</Text>
								</Pressable>
							))}
						</ScrollView>
					) : null}
					<ScrollView style={styles.labelModalScroll} keyboardShouldPersistTaps="handled">
						{labelsBeingEdited.length === 0 ? (
							<Text style={styles.muted}>No labels on this floor.</Text>
						) : (
							labelsBeingEdited.map((l) => (
								<LabelEditRow key={l.id} label={l} floorIndex={floorForLabelEdit.index} onCommit={updateLabel} />
							))
						)}
					</ScrollView>
				</View>
			</Modal>
		</>
	);

	if (phase === "map") {
		return (
			<>
				<View style={styles.screen}>
					<View style={styles.headerRow}>
						<Pressable onPress={resetFlow} style={styles.backBtn}>
							<Text style={styles.backBtnTxt}>← Back</Text>
						</Pressable>
						<View style={styles.headerSpacer} />
						<Pressable onPress={() => setMenuOpen(true)} style={styles.menuBtn} hitSlop={10}>
							<Ionicons name="ellipsis-vertical" size={22} color="#334155" />
						</Pressable>
					</View>
					{bundle.floors.length > 1 ? (
						<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.floorTabs}>
							{bundle.floors.map((fl) => (
								<Pressable
									key={fl.index}
									onPress={() => setActiveFloorIndex(fl.index)}
									style={[styles.floorPill, activeFloorIndex === fl.index && styles.floorPillOn]}
								>
									<Text style={[styles.floorPillTxt, activeFloorIndex === fl.index && styles.floorPillTxtOn]}>
										{fl.level}
									</Text>
								</Pressable>
							))}
						</ScrollView>
					) : null}
					<View style={styles.mapWrap}>
						<Svg width={mapW} height={mapH} style={styles.svgCard}>
							<Rect x={0} y={0} width={mapW} height={mapH} fill="#f4f6fb" rx={12} />
							{map.rooms.map((r) => {
								const pts = r.polygon.map(toS).map((p) => `${p.x},${p.y}`).join(" ");
								return <Polygon key={r.id} points={pts} fill="#e2e8f0" stroke="#94a3b8" strokeWidth={1} />;
							})}
							{map.walls.flatMap((w) => {
								if (w.points.length < 2) {
									return [];
								}
								return w.points.slice(0, -1).map((p, i) => {
									const q = w.points[i + 1]!;
									const a = toS(p);
									const b = toS(q);
									return (
										<Line
											key={`${w.id}-${i}`}
											x1={a.x}
											y1={a.y}
											x2={b.x}
											y2={b.y}
											stroke="#1e293b"
											strokeWidth={3}
											strokeLinecap="square"
										/>
									);
								});
							})}
							{routePts.length > 0 && (
								<Polyline
									points={routePts}
									fill="none"
									stroke="#2563eb"
									strokeWidth={6}
									strokeLinejoin="round"
									strokeLinecap="round"
								/>
							)}
							{map.labels.map((l) => {
								const p = toS({ x: l.x, y: l.y });
								return (
									<G key={l.id}>
										<Circle cx={p.x} cy={p.y} r={5} fill="#0f172a" />
										<SvgText x={p.x + 8} y={p.y + 4} fill="#0f172a" fontSize={11} fontWeight="600">
											{l.text.length > 22 ? `${l.text.slice(0, 20)}…` : l.text}
										</SvgText>
									</G>
								);
							})}
							{map.pois.map((poi) => {
								const p = toS({ x: poi.x, y: poi.y });
								return (
									<Circle key={poi.id} cx={p.x} cy={p.y} r={7} fill="#c026d3" stroke="#fff" strokeWidth={2} />
								);
							})}
						</Svg>
					</View>
					<View style={[styles.bottomCard, { paddingBottom: 12 + insets.bottom }]}>
						<Text style={styles.cardTitle}>Destination</Text>
						<Text style={styles.cardDest}>{destName || "—"}</Text>
						{endParsed && multiFloor ? (
							<Text style={styles.cardMeta}>
								Start floor {parseDestKey(startKey!)?.floor ?? "?"} → Dest floor {endParsed.floor}
							</Text>
						) : null}
						<Text style={styles.cardDist}>
							{routeLegs && routeLegs.length > 0
								? `Distance (graph): ${Math.round(routeDist)}.${crossHint}`
								: "Route hidden. Use Clear route after a preview, or go back to change start and destination."}
						</Text>
						<View style={styles.cardActions}>
							<Pressable onPress={clearRoute} style={styles.secondaryBtn}>
								<Text style={styles.secondaryBtnTxt}>Clear route</Text>
							</Pressable>
							<Pressable onPress={resetFlow} style={styles.secondaryBtn}>
								<Text style={styles.secondaryBtnTxt}>Change places</Text>
							</Pressable>
						</View>
					</View>
				</View>
				{navModals}
			</>
		);
	}

	return (
		<>
			<View style={styles.screen}>
				<View style={styles.titleRow}>
					<View style={styles.titleRowTextWrap}>
						<Text style={styles.heroTitle}>Where do you want to go?</Text>
					</View>
					<Pressable onPress={() => setMenuOpen(true)} style={styles.menuBtn} hitSlop={10}>
						<Ionicons name="ellipsis-vertical" size={22} color="#334155" />
					</Pressable>
				</View>
				<Text style={styles.sub}>Search, then choose start and destination (labels, POIs, or path nodes).</Text>
				{bundle.floors.length > 1 ? (
					<Text style={styles.hintSmall}>
						Multi-floor building: picks can be on different levels if stair links exist.
					</Text>
				) : null}
				<TextInput
					value={search}
					onChangeText={setSearch}
					placeholder="Search rooms and places"
					placeholderTextColor="#94a3b8"
					style={styles.search}
					autoCapitalize="none"
					autoCorrect={false}
				/>
				{routeErr ? <Text style={styles.err}>{routeErr}</Text> : null}
				<ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
					<Text style={styles.section}>Start</Text>
					{filtered.map((d) => (
						<Pressable
							key={`s-${d.key}`}
							onPress={() => setStartKey(d.key)}
							style={[styles.row, startKey === d.key && styles.rowOn]}
						>
							<Text style={styles.rowTitle}>{d.title}</Text>
							<Text style={styles.rowSub}>{d.subtitle}</Text>
						</Pressable>
					))}
					<Text style={styles.section}>Destination</Text>
					{filtered.map((d) => (
						<Pressable
							key={`e-${d.key}`}
							onPress={() => setEndKey(d.key)}
							style={[styles.row, endKey === d.key && styles.rowOn]}
						>
							<Text style={styles.rowTitle}>{d.title}</Text>
							<Text style={styles.rowSub}>{d.subtitle}</Text>
						</Pressable>
					))}
				</ScrollView>
				<Pressable
					onPress={computeRoute}
					style={[styles.primary, (!startKey || !endKey || startKey === endKey) && styles.primaryOff]}
					disabled={!startKey || !endKey || startKey === endKey}
				>
					<Text style={styles.primaryTxt}>Preview route</Text>
				</Pressable>
			</View>
			{navModals}
		</>
	);
}

const styles = StyleSheet.create({
	screen: { flex: 1, padding: 16, backgroundColor: "#fff" },
	centered: { flex: 1, justifyContent: "center", padding: 24, backgroundColor: "#fff" },
	heroTitle: { fontSize: 24, fontWeight: "800", color: "#0f172a" },
	title: { fontSize: 22, fontWeight: "800", color: "#0f172a" },
	sub: { marginTop: 8, fontSize: 14, color: "#64748b", lineHeight: 20 },
	hintSmall: { marginTop: 6, fontSize: 12, color: "#94a3b8" },
	muted: { marginTop: 8, color: "#94a3b8" },
	search: {
		marginTop: 14,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 12,
		fontSize: 16,
		color: "#0f172a",
		backgroundColor: "#f8fafc",
	},
	err: { marginTop: 10, color: "#b91c1c", fontWeight: "600" },
	section: { marginTop: 14, marginBottom: 6, fontSize: 13, fontWeight: "700", color: "#475569" },
	list: { flex: 1, marginTop: 8 },
	listContent: { paddingBottom: 24 },
	row: {
		paddingVertical: 12,
		paddingHorizontal: 14,
		borderRadius: 10,
		backgroundColor: "#f8fafc",
		marginBottom: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	rowOn: { borderColor: "#2563eb", backgroundColor: "#eff6ff" },
	rowTitle: { fontSize: 16, fontWeight: "700", color: "#0f172a" },
	rowSub: { marginTop: 2, fontSize: 12, color: "#64748b" },
	primary: {
		marginTop: 8,
		backgroundColor: "#2563eb",
		paddingVertical: 14,
		borderRadius: 12,
		alignItems: "center",
	},
	primaryOff: { opacity: 0.45 },
	primaryTxt: { color: "#fff", fontWeight: "800", fontSize: 16 },
	headerRow: { flexDirection: "row", alignItems: "center", marginBottom: 8 },
	backBtn: { paddingVertical: 8, paddingHorizontal: 4 },
	backBtnTxt: { color: "#2563eb", fontWeight: "700", fontSize: 15 },
	floorTabs: { maxHeight: 44, marginBottom: 8 },
	floorPill: {
		paddingHorizontal: 14,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#f1f5f9",
		marginRight: 8,
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	floorPillOn: { backgroundColor: "#eff6ff", borderColor: "#2563eb" },
	floorPillTxt: { fontWeight: "700", color: "#475569", fontSize: 14 },
	floorPillTxtOn: { color: "#1d4ed8" },
	mapWrap: { flex: 1, alignItems: "center", justifyContent: "center" },
	svgCard: { borderRadius: 12, overflow: "hidden" },
	bottomCard: {
		marginTop: 8,
		padding: 16,
		borderRadius: 16,
		backgroundColor: "#f8fafc",
		borderWidth: 1,
		borderColor: "#e2e8f0",
	},
	cardTitle: { fontSize: 12, fontWeight: "700", color: "#64748b", textTransform: "uppercase" },
	cardDest: { marginTop: 4, fontSize: 18, fontWeight: "800", color: "#0f172a" },
	cardMeta: { marginTop: 4, fontSize: 13, color: "#64748b" },
	cardDist: { marginTop: 6, fontSize: 14, color: "#475569" },
	cardActions: { flexDirection: "row", gap: 10, marginTop: 12 },
	secondaryBtn: {
		flex: 1,
		paddingVertical: 10,
		borderRadius: 10,
		backgroundColor: "#fff",
		borderWidth: 1,
		borderColor: "#cbd5e1",
		alignItems: "center",
	},
	secondaryBtnTxt: { fontWeight: "700", color: "#334155", fontSize: 14 },
	titleRow: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		gap: 8,
	},
	titleRowTextWrap: { flex: 1, minWidth: 0, paddingRight: 4 },
	menuBtn: { padding: 6 },
	headerSpacer: { flex: 1 },
	menuOverlay: { flex: 1, backgroundColor: "rgba(15, 23, 42, 0.35)" },
	menuSheet: {
		position: "absolute",
		right: 12,
		backgroundColor: "#fff",
		borderRadius: 12,
		minWidth: 200,
		shadowColor: "#000",
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.12,
		shadowRadius: 8,
		elevation: 6,
		borderWidth: 1,
		borderColor: "#e2e8f0",
		overflow: "hidden",
	},
	menuItem: {
		flexDirection: "row",
		alignItems: "center",
		gap: 10,
		paddingVertical: 14,
		paddingHorizontal: 16,
	},
	menuItemTxt: { fontSize: 16, fontWeight: "600", color: "#0f172a" },
	labelModalRoot: { flex: 1, backgroundColor: "#fff", paddingHorizontal: 16 },
	labelModalHeader: {
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "space-between",
		marginBottom: 8,
	},
	labelModalTitle: { fontSize: 20, fontWeight: "800", color: "#0f172a" },
	labelModalDone: { fontSize: 16, fontWeight: "700", color: "#2563eb" },
	labelModalTabs: { maxHeight: 48, marginBottom: 4 },
	labelModalTabPill: { marginRight: 8 },
	labelModalScroll: { flex: 1 },
	labelEditCard: {
		padding: 14,
		borderRadius: 12,
		backgroundColor: "#f8fafc",
		borderWidth: 1,
		borderColor: "#e2e8f0",
		marginBottom: 12,
	},
	labelEditId: { fontSize: 11, color: "#94a3b8", fontFamily: "monospace", marginBottom: 8 },
	labelEditFieldLbl: { fontSize: 12, fontWeight: "700", color: "#64748b", marginBottom: 4 },
	labelEditInput: {
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderRadius: 10,
		paddingHorizontal: 12,
		paddingVertical: 10,
		fontSize: 16,
		color: "#0f172a",
		backgroundColor: "#fff",
		marginBottom: 10,
	},
	labelEditXYRow: { flexDirection: "row", gap: 10, marginBottom: 4 },
	labelEditHalf: { flex: 1, marginBottom: 0 },
});
