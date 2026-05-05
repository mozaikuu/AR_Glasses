import type { GraphEdge, GraphNode } from "@/lib/indoor-nav/types";
import type { NavigationMvpMapV1, Vec2 } from "./types";

export function mapBounds(map: NavigationMvpMapV1): { minX: number; minY: number; maxX: number; maxY: number } {
	let minX = Infinity;
	let minY = Infinity;
	let maxX = -Infinity;
	let maxY = -Infinity;

	const bump = (p: Vec2) => {
		minX = Math.min(minX, p.x);
		minY = Math.min(minY, p.y);
		maxX = Math.max(maxX, p.x);
		maxY = Math.max(maxY, p.y);
	};

	for (const w of map.walls) {
		for (const p of w.points) {
			bump(p);
		}
	}
	for (const r of map.rooms) {
		for (const p of r.polygon) {
			bump(p);
		}
	}
	for (const l of map.labels) {
		bump({ x: l.x, y: l.y });
	}
	for (const p of map.pois) {
		bump({ x: p.x, y: p.y });
	}
	for (const n of map.nodes) {
		bump({ x: n.x, y: n.y });
	}

	if (!Number.isFinite(minX)) {
		return { minX: 0, minY: 0, maxX: 400, maxY: 400 };
	}
	const pad = 24;
	return { minX: minX - pad, minY: minY - pad, maxX: maxX + pad, maxY: maxY + pad };
}

/** Convert MVP nodes/edges to the existing indoor-nav graph types (floor fixed to 0). */
export function toIndoorGraph(map: NavigationMvpMapV1): { nodes: GraphNode[]; edges: GraphEdge[] } {
	const nodes: GraphNode[] = map.nodes.map((n) => ({
		id: n.id,
		floor: 0,
		position: { x: n.x, y: n.y },
		label: n.label,
	}));
	const edges: GraphEdge[] = map.edges.map((e) => ({
		id: e.id,
		from: e.from,
		to: e.to,
		bidirectional: e.bidirectional !== false,
		weight: e.distance,
	}));
	return { nodes, edges };
}
