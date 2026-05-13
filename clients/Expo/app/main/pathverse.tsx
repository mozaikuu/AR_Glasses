/**
 * Pathverse-style tab: SQLite graph (native), A* runway preview, camera strip, OCR simulator.
 * Inspired by https://github.com/anas-dev725/pathverse-ar-app
 */
import { Ionicons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import { router } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Alert,
	Linking,
	Platform,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	useWindowDimensions,
	View,
} from "react-native";
import Svg, { Circle, G, Line, Polygon, Polyline, Text as SvgText } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { astar } from "@/lib/indoor-nav/graph";
import type { GraphEdge, GraphNode } from "@/lib/indoor-nav/types";
import {
	loadPathverseGraph,
	type PathverseEdgeRow,
	type PathverseNodeRow,
} from "@/lib/pathverse/graphStore";

const REPO = "https://github.com/anas-dev725/pathverse-ar-app";

const VB_W = 280;
const VB_H = 240;

function toIndoorGraph(nodes: PathverseNodeRow[], edges: PathverseEdgeRow[]): {
	nodes: GraphNode[];
	edges: GraphEdge[];
} {
	const gn: GraphNode[] = nodes.map((n) => ({
		id: n.id,
		floor: 0,
		position: { x: n.x, y: n.y },
		label: n.name,
	}));
	const ge: GraphEdge[] = edges.map((e, i) => ({
		id: `pv_${i}_${e.node1_id}_${e.node2_id}`,
		from: e.node1_id,
		to: e.node2_id,
		bidirectional: true,
		weight: e.distance,
	}));
	return { nodes: gn, edges: ge };
}

function chevronTriangle(cx: number, cy: number, ang: number, size: number): string {
	const tipX = cx + Math.cos(ang) * size;
	const tipY = cy + Math.sin(ang) * size;
	const baseX = cx - Math.cos(ang) * size * 0.35;
	const baseY = cy - Math.sin(ang) * size * 0.35;
	const perp = ang + Math.PI / 2;
	const hx = Math.cos(perp) * size * 0.55;
	const hy = Math.sin(perp) * size * 0.55;
	return `${tipX},${tipY} ${baseX + hx},${baseY + hy} ${baseX - hx},${baseY - hy}`;
}

function runwayChevrons(
	pts: { x: number; y: number }[],
	step: number,
): { key: string; pts: string }[] {
	const out: { key: string; pts: string }[] = [];
	let k = 0;
	for (let i = 0; i < pts.length - 1; i++) {
		const a = pts[i]!;
		const b = pts[i + 1]!;
		const dx = b.x - a.x;
		const dy = b.y - a.y;
		const len = Math.hypot(dx, dy) || 1;
		const ux = dx / len;
		const uy = dy / len;
		const ang = Math.atan2(uy, ux);
		for (let d = step; d < len - step * 0.5; d += step) {
			const cx = a.x + ux * d;
			const cy = a.y + uy * d;
			out.push({ key: `ch_${k++}`, pts: chevronTriangle(cx, cy, ang, 9) });
		}
	}
	return out;
}

export default function PathverseTab() {
	const insets = useSafeAreaInsets();
	const { width: winW } = useWindowDimensions();
	const mapW = Math.min(winW - 32, 360);

	const [pvNodes, setPvNodes] = useState<PathverseNodeRow[]>([]);
	const [pvEdges, setPvEdges] = useState<PathverseEdgeRow[]>([]);
	const [startId, setStartId] = useState<string | null>("it_gate");
	const [endId, setEndId] = useState<string | null>("it_lab_1");
	const [pathIds, setPathIds] = useState<string[]>([]);
	const [ocrQuery, setOcrQuery] = useState("");
	const [dash, setDash] = useState(0);

	const [perm, requestPerm] = useCameraPermissions();

	const reload = useCallback(() => {
		const { nodes, edges } = loadPathverseGraph();
		setPvNodes(nodes);
		setPvEdges(edges);
	}, []);

	useEffect(() => {
		reload();
	}, [reload]);

	const runAstar = useCallback(() => {
		if (!startId || !endId) {
			Alert.alert("Pick nodes", "Choose start and destination.");
			return;
		}
		const { nodes: gn, edges: ge } = toIndoorGraph(pvNodes, pvEdges);
		const p = astar(startId, endId, gn, ge);
		if (!p || p.length === 0) {
			Alert.alert("No path", "Try different nodes.");
			setPathIds([]);
			return;
		}
		setPathIds(p);
	}, [startId, endId, pvNodes, pvEdges]);

	useEffect(() => {
		if (!startId || !endId || pvNodes.length === 0) {
			setPathIds([]);
			return;
		}
		const { nodes: gn, edges: ge } = toIndoorGraph(pvNodes, pvEdges);
		const p = astar(startId, endId, gn, ge);
		setPathIds(p ?? []);
	}, [startId, endId, pvNodes, pvEdges]);

	useEffect(() => {
		const t = setInterval(() => setDash((d) => (d + 3) % 80), 60);
		return () => clearInterval(t);
	}, []);

	const byId = useMemo(() => new Map(pvNodes.map((n) => [n.id, n])), [pvNodes]);

	const pathPts = useMemo(() => {
		return pathIds.map((id) => {
			const n = byId.get(id);
			return n ? { x: n.x, y: n.y } : null;
		}).filter(Boolean) as { x: number; y: number }[];
	}, [pathIds, byId]);

	const chevrons = useMemo(() => runwayChevrons(pathPts, 22), [pathPts]);

	const simulateOcr = () => {
		const q = ocrQuery.trim().toLowerCase();
		if (!q) {
			Alert.alert("OCR", "Type part of a room name (e.g. “lab”, “lift”).");
			return;
		}
		const hit = pvNodes.find((n) => n.name.toLowerCase().includes(q));
		if (!hit) {
			Alert.alert("No match", "Try another substring.");
			return;
		}
		setStartId(hit.id);
		Alert.alert("Anchored", `Matched “${hit.name}”. Set as start node.`);
	};

	const camReady = perm?.granted === true;

	return (
		<ScrollView
			style={styles.screen}
			contentContainerStyle={[styles.content, { paddingBottom: 28 + insets.bottom }]}
		>
			<Text style={styles.title}>Pathverse AR</Text>
			<Text style={styles.sub}>
				Local graph + A* runway (neon). SQLite on device; web uses the same graph in memory. Full Viro AR is not bundled.
			</Text>

			<View style={[styles.mapCard, { width: mapW }]}>
				<Svg width={mapW} height={(mapW * VB_H) / VB_W} viewBox={`0 0 ${VB_W} ${VB_H}`}>
					<SvgText x={8} y={16} fill="#64748b" fontSize={11} fontWeight="600">
						Runway preview (map units)
					</SvgText>
					{pvEdges.map((e, i) => {
						const a = byId.get(e.node1_id);
						const b = byId.get(e.node2_id);
						if (!a || !b) {
							return null;
						}
						const ia = pathIds.indexOf(e.node1_id);
						const ib = pathIds.indexOf(e.node2_id);
						const onPath = ia >= 0 && ib >= 0 && Math.abs(ia - ib) === 1;
						return (
							<Line
								key={`e_${i}`}
								x1={a.x}
								y1={a.y}
								x2={b.x}
								y2={b.y}
								stroke={onPath ? "#22c55e" : "rgba(148,163,184,0.35)"}
								strokeWidth={onPath ? 5 : 2}
							/>
						);
					})}
					{pathPts.length > 1 && (
						<Polyline
							points={pathPts.map((p) => `${p.x},${p.y}`).join(" ")}
							fill="none"
							stroke="#bef264"
							strokeWidth={4}
							strokeLinejoin="round"
							strokeLinecap="round"
							strokeDasharray="10 18"
							strokeDashoffset={-dash}
						/>
					)}
					{chevrons.map((c) => (
						<Polygon key={c.key} points={c.pts} fill="#86efac" opacity={0.95} />
					))}
					{pvNodes.map((n) => {
						const sel = n.id === startId || n.id === endId;
						const onPath = pathIds.includes(n.id);
						return (
							<G key={n.id}>
								<Circle
									cx={n.x}
									cy={n.y}
									r={sel ? 10 : onPath ? 8 : 6}
									fill={sel ? "#22c55e" : onPath ? "#4ade80" : "#334155"}
									stroke="#fff"
									strokeWidth={2}
								/>
								<SvgText x={n.x + 12} y={n.y + 4} fill="#e2e8f0" fontSize={10} fontWeight="700">
									{n.name.length > 14 ? `${n.name.slice(0, 12)}…` : n.name}
								</SvgText>
							</G>
						);
					})}
				</Svg>
			</View>

			<Text style={styles.section}>From → To</Text>
			<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
				{pvNodes.map((n) => (
					<Pressable
						key={`s-${n.id}`}
						onPress={() => setStartId(n.id)}
						style={[styles.chip, startId === n.id && styles.chipOn]}
					>
						<Text style={[styles.chipTxt, startId === n.id && styles.chipTxtOn]}>{n.name}</Text>
					</Pressable>
				))}
			</ScrollView>
			<ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
				{pvNodes.map((n) => (
					<Pressable
						key={`g-${n.id}`}
						onPress={() => setEndId(n.id)}
						style={[styles.chip, endId === n.id && styles.chipGoal]}
					>
						<Text style={[styles.chipTxt, endId === n.id && styles.chipTxtOn]}>{n.name}</Text>
					</Pressable>
				))}
			</ScrollView>

			<Pressable onPress={runAstar} style={styles.secondary}>
				<Ionicons name="flash" size={18} color="#0f172a" />
				<Text style={styles.secondaryTxt}>Re-run A*</Text>
			</Pressable>

			<Text style={styles.section}>OCR simulator</Text>
			<Text style={styles.hint}>Type a substring of a node name to snap your start (like ambient sign text).</Text>
			<TextInput
				value={ocrQuery}
				onChangeText={setOcrQuery}
				placeholder="e.g. lift, lab, faculty"
				placeholderTextColor="#64748b"
				style={styles.input}
			/>
			<Pressable onPress={simulateOcr} style={styles.ocrBtn}>
				<Ionicons name="scan" size={18} color="#fff" />
				<Text style={styles.ocrBtnTxt}>Match & anchor</Text>
			</Pressable>

			<Text style={styles.section}>Camera (AR preview strip)</Text>
			<View style={styles.camBox}>
				{Platform.OS === "web" ? (
					<View style={styles.camPlaceholder}>
						<Ionicons name="videocam-off" size={36} color="#64748b" />
						<Text style={styles.camPhTxt}>Camera runs on iOS / Android builds.</Text>
					</View>
				) : !camReady ? (
					<Pressable onPress={() => void requestPerm()} style={styles.camPlaceholder}>
						<Ionicons name="camera" size={36} color="#22c55e" />
						<Text style={styles.camPhTxt}>Tap to allow camera (Pathverse-style live view).</Text>
					</Pressable>
				) : (
					<CameraView style={StyleSheet.absoluteFill} facing="back" />
				)}
			</View>

			<View style={styles.rowActions}>
				<Pressable onPress={() => void Linking.openURL(REPO)} style={styles.linkBtn}>
					<Ionicons name="logo-github" size={18} color="#fff" />
					<Text style={styles.linkBtnTxt}>Upstream repo</Text>
				</Pressable>
				<Pressable onPress={() => router.push("/main/navigation")} style={styles.primary}>
					<Ionicons name="map" size={18} color="#fff" />
					<Text style={styles.primaryTxt}>Uni floor nav</Text>
				</Pressable>
			</View>
		</ScrollView>
	);
}

const styles = StyleSheet.create({
	screen: { flex: 1, backgroundColor: "#0b1220" },
	content: { padding: 16, paddingTop: 10 },
	title: { fontSize: 26, fontWeight: "800", color: "#f8fafc" },
	sub: { marginTop: 8, fontSize: 14, lineHeight: 20, color: "#94a3b8" },
	mapCard: {
		alignSelf: "center",
		marginTop: 14,
		borderRadius: 16,
		overflow: "hidden",
		backgroundColor: "#020617",
		borderWidth: 1,
		borderColor: "#1e293b",
	},
	section: { marginTop: 16, marginBottom: 8, fontSize: 12, fontWeight: "800", color: "#64748b", letterSpacing: 0.6 },
	hint: { fontSize: 13, color: "#64748b", marginBottom: 8 },
	chipRow: { maxHeight: 44, marginBottom: 6 },
	chip: {
		paddingHorizontal: 12,
		paddingVertical: 8,
		borderRadius: 20,
		backgroundColor: "#1e293b",
		marginRight: 8,
		borderWidth: 1,
		borderColor: "#334155",
	},
	chipOn: { backgroundColor: "#14532d", borderColor: "#22c55e" },
	chipGoal: { backgroundColor: "#1e3a5f", borderColor: "#38bdf8" },
	chipTxt: { fontSize: 12, fontWeight: "700", color: "#cbd5e1" },
	chipTxtOn: { color: "#fff" },
	secondary: {
		marginTop: 10,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 8,
		backgroundColor: "#e2e8f0",
		paddingVertical: 11,
		borderRadius: 12,
	},
	secondaryTxt: { fontWeight: "800", color: "#0f172a", fontSize: 14 },
	input: {
		borderWidth: 1,
		borderColor: "#334155",
		borderRadius: 12,
		paddingHorizontal: 14,
		paddingVertical: 11,
		fontSize: 15,
		color: "#f1f5f9",
		backgroundColor: "#0f172a",
	},
	ocrBtn: {
		marginTop: 10,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 8,
		backgroundColor: "#15803d",
		paddingVertical: 12,
		borderRadius: 12,
	},
	ocrBtnTxt: { color: "#fff", fontWeight: "800", fontSize: 15 },
	camBox: {
		height: 200,
		borderRadius: 14,
		overflow: "hidden",
		backgroundColor: "#020617",
		borderWidth: 1,
		borderColor: "#1e293b",
	},
	camPlaceholder: {
		...StyleSheet.absoluteFillObject,
		justifyContent: "center",
		alignItems: "center",
		padding: 16,
		gap: 10,
	},
	camPhTxt: { color: "#94a3b8", textAlign: "center", fontSize: 14, lineHeight: 20 },
	rowActions: { flexDirection: "row", gap: 10, marginTop: 16 },
	linkBtn: {
		flex: 1,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 6,
		backgroundColor: "#1e293b",
		paddingVertical: 13,
		borderRadius: 12,
		borderWidth: 1,
		borderColor: "#334155",
	},
	linkBtnTxt: { color: "#e2e8f0", fontWeight: "800", fontSize: 13 },
	primary: {
		flex: 1,
		flexDirection: "row",
		alignItems: "center",
		justifyContent: "center",
		gap: 6,
		backgroundColor: "#2563eb",
		paddingVertical: 13,
		borderRadius: 12,
	},
	primaryTxt: { color: "#fff", fontWeight: "800", fontSize: 13 },
});
