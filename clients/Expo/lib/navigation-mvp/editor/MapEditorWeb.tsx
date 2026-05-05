import { useCallback, useMemo, useRef, useState } from "react";
import {
	Alert,
	Platform,
	Pressable,
	ScrollView,
	StyleSheet,
	Text,
	TextInput,
	View,
} from "react-native";
import Svg, { Circle, G, Line, Polygon, Rect, Text as SvgText } from "react-native-svg";

import type { MvpPoiType, NavigationMvpMapV1, Vec2 } from "@/lib/navigation-mvp/types";
import { mapBounds } from "@/lib/navigation-mvp/mapAdapters";
import { parseNavigationMvpMap } from "@/lib/navigation-mvp/validate";

const GRID = 20;

type Tool = "pan" | "wall" | "label" | "poi" | "delete";

function snap(v: number) {
	return Math.round(v / GRID) * GRID;
}

function snapOrtho(a: Vec2, b: Vec2): Vec2 {
	const dx = b.x - a.x;
	const dy = b.y - a.y;
	if (Math.abs(dx) >= Math.abs(dy)) {
		return { x: b.x, y: a.y };
	}
	return { x: a.x, y: b.y };
}

function cloneMap(m: NavigationMvpMapV1): NavigationMvpMapV1 {
	return JSON.parse(JSON.stringify(m)) as NavigationMvpMapV1;
}

function newId(prefix: string) {
	return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

type Props = {
	initialMap: NavigationMvpMapV1;
};

export function MapEditorWeb({ initialMap }: Props) {
	const [map, setMap] = useState<NavigationMvpMapV1>(() => cloneMap(initialMap));
	const [tool, setTool] = useState<Tool>("pan");
	const [poiType, setPoiType] = useState<MvpPoiType>("entrance");
	const [paste, setPaste] = useState("");
	const [view, setView] = useState({ scale: 1, panX: 0, panY: 0 });
	const [wallStart, setWallStart] = useState<Vec2 | null>(null);
	const dragRef = useRef<{ x: number; y: number; active: boolean }>({ x: 0, y: 0, active: false });
	const [history, setHistory] = useState<NavigationMvpMapV1[]>([cloneMap(initialMap)]);
	const [future, setFuture] = useState<NavigationMvpMapV1[]>([]);

	const bounds = useMemo(() => mapBounds(map), [map]);

	const pushHistory = useCallback((next: NavigationMvpMapV1) => {
		setHistory((h) => [...h, cloneMap(next)]);
		setFuture([]);
		setMap(next);
	}, []);

	const undo = useCallback(() => {
		setHistory((h) => {
			if (h.length <= 1) {
				return h;
			}
			const prev = h[h.length - 2]!;
			const last = h[h.length - 1]!;
			setFuture((f) => [cloneMap(last), ...f]);
			setMap(cloneMap(prev));
			return h.slice(0, -1);
		});
	}, []);

	const redo = useCallback(() => {
		setFuture((f) => {
			if (f.length === 0) {
				return f;
			}
			const [head, ...rest] = f;
			setHistory((h) => [...h, cloneMap(head)]);
			setMap(cloneMap(head));
			return rest;
		});
	}, []);

	const canvasW = 900;
	const canvasH = 560;
	const bw = Math.max(1e-6, bounds.maxX - bounds.minX);
	const bh = Math.max(1e-6, bounds.maxY - bounds.minY);
	const baseScale = (Math.min(canvasW, canvasH) / Math.max(bw, bh)) * 0.92;
	const scale = baseScale * view.scale;

	const toScreen = useCallback(
		(p: Vec2) => ({
			x: (p.x - bounds.minX) * scale + view.panX,
			y: (p.y - bounds.minY) * scale + view.panY,
		}),
		[bounds.minX, bounds.minY, scale, view.panX, view.panY],
	);

	const toMap = useCallback(
		(x: number, y: number): Vec2 => ({
			x: (x - view.panX) / scale + bounds.minX,
			y: (y - view.panY) / scale + bounds.minY,
		}),
		[bounds.minX, scale, view.panX, view.panY],
	);

	const onCanvasPress = (lx: number, ly: number) => {
		const p = toMap(lx, ly);
		const sx = snap(p.x);
		const sy = snap(p.y);

		if (tool === "pan") {
			return;
		}

		if (tool === "wall") {
			if (!wallStart) {
				setWallStart({ x: sx, y: sy });
				return;
			}
			const end = snapOrtho(wallStart, { x: sx, y: sy });
			const next = cloneMap(map);
			next.walls.push({ id: newId("wall"), points: [wallStart, end] });
			setWallStart(null);
			pushHistory(next);
			return;
		}

		if (tool === "label") {
			const text =
				typeof globalThis !== "undefined" && "prompt" in globalThis
					? // eslint-disable-next-line @typescript-eslint/no-explicit-any
						(globalThis as any).prompt("Room name?", "Room")
					: null;
			if (!text) {
				return;
			}
			const next = cloneMap(map);
			next.labels.push({ id: newId("lbl"), text: String(text), x: sx, y: sy });
			pushHistory(next);
			return;
		}

		if (tool === "poi") {
			const next = cloneMap(map);
			next.pois.push({ id: newId("poi"), type: poiType, x: sx, y: sy });
			pushHistory(next);
			return;
		}

		if (tool === "delete") {
			const hitR = 18 / scale;
			const next = cloneMap(map);
			let removed = false;
			const tryList = <T extends { id: string }>(arr: T[], pred: (t: T) => boolean) => {
				const idx = arr.findIndex(pred);
				if (idx >= 0) {
					arr.splice(idx, 1);
					removed = true;
				}
			};
			tryList(next.labels, (l) => Math.hypot(l.x - sx, l.y - sy) < hitR);
			if (!removed) {
				tryList(next.pois, (p) => Math.hypot(p.x - sx, p.y - sy) < hitR);
			}
			if (!removed) {
				tryList(next.nodes, (n) => Math.hypot(n.x - sx, n.y - sy) < hitR);
			}
			if (!removed) {
				tryList(next.walls, (w) => {
					if (w.points.length < 2) {
						return false;
					}
					const a = w.points[0]!;
					const b = w.points[w.points.length - 1]!;
					const distSeg = (ax: number, ay: number, bx: number, by: number, px: number, py: number) => {
						const abx = bx - ax;
						const aby = by - ay;
						const apx = px - ax;
						const apy = py - ay;
						const ab2 = abx * abx + aby * aby || 1;
						let t = (apx * abx + apy * aby) / ab2;
						t = Math.max(0, Math.min(1, t));
						const cx = ax + abx * t;
						const cy = ay + aby * t;
						return Math.hypot(px - cx, py - cy);
					};
					return distSeg(a.x, a.y, b.x, b.y, sx, sy) < hitR;
				});
			}
			if (removed) {
				next.edges = next.edges.filter(
					(e) => next.nodes.some((n) => n.id === e.from) && next.nodes.some((n) => n.id === e.to),
				);
				pushHistory(next);
			}
		}
	};

	const exportJson = () => {
		const json = JSON.stringify(map, null, 2);
		if (Platform.OS === "web" && typeof document !== "undefined") {
			const blob = new Blob([json], { type: "application/json" });
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = `${map.name.replace(/\s+/g, "_") || "map"}.json`;
			a.click();
			URL.revokeObjectURL(url);
			return;
		}
		Alert.alert("Export", "Web download is only available in the browser build.");
	};

	const applyPaste = () => {
		try {
			const raw = JSON.parse(paste);
			const parsed = parseNavigationMvpMap(raw);
			if (!parsed.ok) {
				Alert.alert("Import failed", parsed.error);
				return;
			}
			const next = cloneMap(parsed.data);
			setHistory([next]);
			setFuture([]);
			setMap(next);
			setPaste("");
		} catch {
			Alert.alert("Import failed", "Invalid JSON.");
		}
	};

	const gridLines = useMemo(() => {
		const lines: { x1: number; y1: number; x2: number; y2: number }[] = [];
		for (let gx = Math.floor(bounds.minX / GRID) * GRID; gx <= bounds.maxX; gx += GRID) {
			const a = toScreen({ x: gx, y: bounds.minY });
			const b = toScreen({ x: gx, y: bounds.maxY });
			lines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
		}
		for (let gy = Math.floor(bounds.minY / GRID) * GRID; gy <= bounds.maxY; gy += GRID) {
			const a = toScreen({ x: bounds.minX, y: gy });
			const b = toScreen({ x: bounds.maxX, y: gy });
			lines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
		}
		return lines;
	}, [bounds, toScreen]);

	return (
		<ScrollView contentContainerStyle={styles.page}>
			<Text style={styles.h1}>Floor plan editor (web)</Text>
			<Text style={styles.muted}>Big buttons, grid snap, import/export JSON. Undo/redo keeps edits safe.</Text>

			<View style={styles.topBar}>
				<Pressable style={styles.btn} onPress={undo}>
					<Text style={styles.btnTxt}>Undo</Text>
				</Pressable>
				<Pressable style={styles.btn} onPress={redo}>
					<Text style={styles.btnTxt}>Redo</Text>
				</Pressable>
				<Pressable style={[styles.btn, styles.primary]} onPress={exportJson}>
					<Text style={[styles.btnTxt, styles.btnTxtLight]}>Export JSON</Text>
				</Pressable>
			</View>

			<View style={styles.importRow}>
				<TextInput
					style={styles.input}
					multiline
					placeholder="Paste map JSON here…"
					value={paste}
					onChangeText={setPaste}
				/>
				<Pressable style={[styles.btn, styles.primary]} onPress={applyPaste}>
					<Text style={[styles.btnTxt, styles.btnTxtLight]}>Apply import</Text>
				</Pressable>
			</View>

			<View style={styles.toolbar}>
				{(
					[
						["pan", "Pan"],
						["wall", "Draw wall"],
						["label", "Room label"],
						["poi", "Add POI"],
						["delete", "Delete"],
					] as const
				).map(([t, label]) => (
					<Pressable key={t} style={[styles.tool, tool === t && styles.toolOn]} onPress={() => setTool(t)}>
						<Text style={[styles.toolTxt, tool === t && styles.toolTxtOn]}>{label}</Text>
					</Pressable>
				))}
			</View>

			{tool === "poi" && (
				<ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.poiRow}>
					{(["entrance", "elevator", "stairs", "toilet", "office", "classroom", "generic"] as MvpPoiType[]).map((t) => (
						<Pressable key={t} style={[styles.chip, poiType === t && styles.chipOn]} onPress={() => setPoiType(t)}>
							<Text style={[styles.chipTxt, poiType === t && styles.chipTxtOn]}>{t}</Text>
						</Pressable>
					))}
				</ScrollView>
			)}

			<View style={styles.zoomRow}>
				<Pressable style={styles.btn} onPress={() => setView((v) => ({ ...v, scale: Math.max(0.4, v.scale / 1.15) }))}>
					<Text style={styles.btnTxt}>Zoom out</Text>
				</Pressable>
				<Pressable style={styles.btn} onPress={() => setView((v) => ({ ...v, scale: Math.min(3, v.scale * 1.15) }))}>
					<Text style={styles.btnTxt}>Zoom in</Text>
				</Pressable>
				<Text style={styles.muted}>Grid {GRID}px · walls snap to 90°</Text>
			</View>

			<View style={styles.canvasWrap}>
				<View
					onStartShouldSetResponder={() => tool === "pan"}
					onMoveShouldSetResponder={() => tool === "pan"}
					onResponderGrant={(e) => {
						dragRef.current = { x: e.nativeEvent.pageX, y: e.nativeEvent.pageY, active: true };
					}}
					onResponderMove={(e) => {
						if (!dragRef.current.active) {
							return;
						}
						const dx = e.nativeEvent.pageX - dragRef.current.x;
						const dy = e.nativeEvent.pageY - dragRef.current.y;
						dragRef.current = { x: e.nativeEvent.pageX, y: e.nativeEvent.pageY, active: true };
						setView((v) => ({ ...v, panX: v.panX + dx, panY: v.panY + dy }));
					}}
					onResponderRelease={() => {
						dragRef.current.active = false;
					}}
					onResponderTerminate={() => {
						dragRef.current.active = false;
					}}
				>
					<Pressable
						onPress={(ev) => {
							const lx = ev.nativeEvent.locationX;
							const ly = ev.nativeEvent.locationY;
							if (tool !== "pan") {
								onCanvasPress(lx, ly);
							}
						}}
					>
						<Svg width={canvasW} height={canvasH}>
							<Rect x={0} y={0} width={canvasW} height={canvasH} fill="#ffffff" />
							{gridLines.map((ln, i) => (
								<Line
									key={`g-${i}`}
									x1={ln.x1}
									y1={ln.y1}
									x2={ln.x2}
									y2={ln.y2}
									stroke="#eef2ff"
									strokeWidth={1}
								/>
							))}
							{map.rooms.map((r) => {
								const pts = r.polygon.map((p) => {
									const s = toScreen(p);
									return `${s.x},${s.y}`;
								});
								return (
									<Polygon key={r.id} points={pts.join(" ")} fill="#e0e7ff" stroke="#6366f1" strokeWidth={1} opacity={0.35} />
								);
							})}
							{map.walls.map((w) => {
								const a = toScreen(w.points[0]!);
								const b = toScreen(w.points[w.points.length - 1]!);
								return <Line key={w.id} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#0f172a" strokeWidth={3} />;
							})}
							{map.labels.map((l) => {
								const s = toScreen({ x: l.x, y: l.y });
								return (
									<G key={l.id}>
										<SvgText x={s.x} y={s.y} fill="#0f172a" fontSize="12" fontWeight="700">
											{l.text}
										</SvgText>
									</G>
								);
							})}
							{map.pois.map((p) => {
								const s = toScreen({ x: p.x, y: p.y });
								return (
									<G key={p.id}>
										<Circle cx={s.x} cy={s.y} r={8} fill="#2563eb" />
										<SvgText x={s.x + 10} y={s.y + 4} fill="#1e293b" fontSize="10" fontWeight="600">
											{p.type}
										</SvgText>
									</G>
								);
							})}
							{map.nodes.map((n) => {
								const s = toScreen({ x: n.x, y: n.y });
								return (
									<G key={n.id}>
										<Circle cx={s.x} cy={s.y} r={5} fill="#f97316" />
									</G>
								);
							})}
							{wallStart && (
								<Circle cx={toScreen(wallStart).x} cy={toScreen(wallStart).y} r={6} fill="#22c55e" opacity={0.9} />
							)}
						</Svg>
					</Pressable>
				</View>
			</View>
		</ScrollView>
	);
}

const styles = StyleSheet.create({
	page: { padding: 16, gap: 12, alignItems: "stretch", maxWidth: 1040, alignSelf: "center", width: "100%" },
	h1: { fontSize: 24, fontWeight: "800", color: "#0f172a" },
	muted: { color: "#64748b", fontSize: 13 },
	topBar: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
	importRow: { gap: 8 },
	input: {
		minHeight: 90,
		borderWidth: 1,
		borderColor: "#cbd5e1",
		borderRadius: 10,
		padding: 10,
		fontFamily: Platform.select({ web: "monospace", default: undefined }),
		backgroundColor: "#fff",
	},
	toolbar: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
	tool: { paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10, backgroundColor: "#e2e8f0" },
	toolOn: { backgroundColor: "#1d4ed8" },
	toolTxt: { fontWeight: "700", color: "#0f172a" },
	toolTxtOn: { color: "#fff" },
	poiRow: { gap: 8, paddingVertical: 4 },
	chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 999, backgroundColor: "#e2e8f0", marginRight: 8 },
	chipOn: { backgroundColor: "#312e81" },
	chipTxt: { fontWeight: "700", color: "#0f172a" },
	chipTxtOn: { color: "#fff" },
	zoomRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, alignItems: "center" },
	canvasWrap: { borderWidth: 1, borderColor: "#cbd5e1", borderRadius: 12, overflow: "hidden", backgroundColor: "#fff" },
	btn: { paddingHorizontal: 12, paddingVertical: 10, borderRadius: 10, backgroundColor: "#e2e8f0" },
	primary: { backgroundColor: "#2563eb" },
	btnTxt: { fontWeight: "700", color: "#0f172a" },
	btnTxtLight: { color: "#f8fafc" },
});
