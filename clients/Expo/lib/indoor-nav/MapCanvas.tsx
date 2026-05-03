import React, { memo } from "react";
import Svg, {
	Circle,
	G,
	Line,
	Polygon,
	Polyline,
	Rect,
	Text as SvgText,
} from "react-native-svg";
import type { Vec2 } from "./types";

export type MapEdge = { from: Vec2; to: Vec2 };

export type RoomShapeMarker = {
	id: string;
	position: Vec2;
	name: string;
	width?: number;
	height?: number;
	highlight?: boolean;
	selected?: boolean;
	mapKind?: string;
};

type MapCanvasProps = {
	width: number;
	height: number;
	/** Map coordinate bounds (same space as node positions). */
	bounds: { minX: number; minY: number; maxX: number; maxY: number };
	nodes: { id: string; position: Vec2; label?: string }[];
	edges: MapEdge[];
	routePoints: Vec2[];
	/** Point markers (legacy / small POIs). */
	roomMarkers?: { id: string; position: Vec2; name: string; highlight?: boolean }[];
	/** Rectangles or circles for rooms and zones. */
	roomShapes?: RoomShapeMarker[];
	currentId?: string | null;
	destinationId?: string | null;
	/** Degrees: 0 = east, counter-clockwise for SVG rotation we convert in parent. */
	arrowDeg?: number | null;
};

function mapToScreen(
	p: Vec2,
	b: MapCanvasProps["bounds"],
	w: number,
	h: number,
	pad: number,
): Vec2 {
	const bw = Math.max(1e-6, b.maxX - b.minX);
	const bh = Math.max(1e-6, b.maxY - b.minY);
	const innerW = w - pad * 2;
	const innerH = h - pad * 2;
	const sx = pad + ((p.x - b.minX) / bw) * innerW;
	const sy = pad + ((p.y - b.minY) / bh) * innerH;
	return { x: sx, y: sy };
}

function MapCanvasInner(props: MapCanvasProps) {
	const pad = 16;
	const b = props.bounds;
	const { width: W, height: H } = props;

	const toS = (p: Vec2) => mapToScreen(p, b, W, H, pad);

	const routeScreen = props.routePoints.map(toS);
	const pointsStr = routeScreen.map((p) => `${p.x},${p.y}`).join(" ");

	return (
		<Svg width={W} height={H}>
			<Rect x={0} y={0} width={W} height={H} fill="#f4f6fb" rx={12} />
			{props.edges.map((e, i) => {
				const a = toS(e.from);
				const c = toS(e.to);
				return (
					<Line
						key={`e-${i}`}
						x1={a.x}
						y1={a.y}
						x2={c.x}
						y2={c.y}
						stroke="#cbd5e1"
						strokeWidth={2}
					/>
				);
			})}
			{pointsStr.length > 0 && (
				<Polyline
					points={pointsStr}
					fill="none"
					stroke="#2563eb"
					strokeWidth={4}
					strokeLinejoin="round"
					strokeLinecap="round"
				/>
			)}
			{props.roomShapes?.map((r) => {
				const p = toS(r.position);
				const w = r.width && r.width > 0 ? (r.width / (b.maxX - b.minX)) * (W - pad * 2) : 0;
				const h = r.height && r.height > 0 ? (r.height / (b.maxY - b.minY)) * (H - pad * 2) : 0;
				const fill =
					r.mapKind === "garden"
						? "#bbf7d0"
						: r.mapKind === "bathroom"
							? "#bae6fd"
							: r.mapKind === "stairs"
								? "#fde68a"
								: r.highlight
									? "#86efac"
									: "#e2e8f0";
				const stroke = r.selected ? "#2563eb" : "#64748b";
				const sw = r.selected ? 3 : 1;
				const label = r.name.length > 18 ? `${r.name.slice(0, 16)}…` : r.name;
				if (w > 2 && h > 2) {
					return (
						<G key={`sh-${r.id}`}>
							<Rect
								x={p.x}
								y={p.y}
								width={w}
								height={h}
								fill={fill}
								stroke={stroke}
								strokeWidth={sw}
								opacity={0.92}
								rx={3}
							/>
							<SvgText x={p.x + 4} y={p.y + 14} fill="#0f172a" fontSize="10" fontWeight="700">
								{label}
							</SvgText>
						</G>
					);
				}
				const fillDot = r.highlight ? "#22c55e" : "#94a3b8";
				return (
					<G key={`sh-${r.id}`}>
						<Circle cx={p.x + 4} cy={p.y + 4} r={r.selected ? 10 : 7} fill={fillDot} stroke={stroke} strokeWidth={sw} />
						<SvgText x={p.x + 14} y={p.y + 8} fill="#0f172a" fontSize="10" fontWeight="600">
							{label}
						</SvgText>
					</G>
				);
			})}
			{props.roomMarkers?.map((r) => {
				const p = toS(r.position);
				const fill = r.highlight ? "#22c55e" : "#94a3b8";
				return (
					<G key={r.id}>
						<Circle cx={p.x} cy={p.y} r={r.highlight ? 9 : 6} fill={fill} opacity={0.9} />
						<SvgText
							x={p.x + 10}
							y={p.y - 6}
							fill="#0f172a"
							fontSize="10"
							fontWeight="600"
						>
							{r.name.length > 22 ? `${r.name.slice(0, 20)}…` : r.name}
						</SvgText>
					</G>
				);
			})}
			{props.nodes.map((n) => {
				const p = toS(n.position);
				const isCur = n.id === props.currentId;
				const isDest = n.id === props.destinationId;
				const fill = isCur ? "#ea580c" : isDest ? "#16a34a" : "#64748b";
				return (
					<G key={n.id}>
						<Circle cx={p.x} cy={p.y} r={isCur ? 10 : 7} fill={fill} />
						{n.label && (
							<SvgText
								x={p.x + 10}
								y={p.y + 14}
								fill="#334155"
								fontSize="9"
							>
								{n.label.length > 18 ? `${n.label.slice(0, 16)}…` : n.label}
							</SvgText>
						)}
					</G>
				);
			})}
			{typeof props.arrowDeg === "number" && props.currentId && (
				<G>
					{(() => {
						const cur = props.nodes.find((n) => n.id === props.currentId);
						if (!cur) {
							return null;
						}
						const c = toS(cur.position);
						const r = 22;
						const rad = (props.arrowDeg * Math.PI) / 180;
						const tip = { x: c.x + Math.cos(rad) * r, y: c.y + Math.sin(rad) * r };
						const left = {
							x: c.x + Math.cos(rad + (2.4 * Math.PI) / 3) * (r * 0.55),
							y: c.y + Math.sin(rad + (2.4 * Math.PI) / 3) * (r * 0.55),
						};
						const right = {
							x: c.x + Math.cos(rad - (2.4 * Math.PI) / 3) * (r * 0.55),
							y: c.y + Math.sin(rad - (2.4 * Math.PI) / 3) * (r * 0.55),
						};
						return (
							<Polygon
								points={`${tip.x},${tip.y} ${left.x},${left.y} ${right.x},${right.y}`}
								fill="#dc2626"
								opacity={0.95}
							/>
						);
					})()}
				</G>
			)}
		</Svg>
	);
}

export const MapCanvas = memo(MapCanvasInner);
