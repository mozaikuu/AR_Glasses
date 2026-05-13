import type { NavigationMvpMapV1, MvpEdge, MvpNode } from "./types";
import { segmentCrossesWallSegments, wallSegmentsFromMap, type WallSeg } from "./wallSegments";

function dist(a: MvpNode, b: MvpNode): number {
	return Math.hypot(a.x - b.x, a.y - b.y);
}

/** Upper bound for k-NN auto edges from node spread (map units / metres). */
export function computeMaxAutoEdgeDistance(nodes: MvpNode[]): number {
	if (nodes.length < 2) {
		return 120;
	}
	let minX = Infinity;
	let minY = Infinity;
	let maxX = -Infinity;
	let maxY = -Infinity;
	for (const n of nodes) {
		minX = Math.min(minX, n.x);
		minY = Math.min(minY, n.y);
		maxX = Math.max(maxX, n.x);
		maxY = Math.max(maxY, n.y);
	}
	const diag = Math.hypot(maxX - minX, maxY - minY);
	return Math.min(520, Math.max(40, diag * 0.42));
}

export function filterEdgesCrossingWalls(map: NavigationMvpMapV1): MvpEdge[] {
	const segs = wallSegmentsFromMap(map.walls);
	const byId = new Map(map.nodes.map((n) => [n.id, n]));
	const out: MvpEdge[] = [];
	for (const e of map.edges) {
		const a = byId.get(e.from);
		const b = byId.get(e.to);
		if (!a || !b) {
			continue;
		}
		if (segmentCrossesWallSegments(a.x, a.y, b.x, b.y, segs)) {
			continue;
		}
		out.push(e);
	}
	return out;
}

function buildWallSafeAutoEdges(
	map: NavigationMvpMapV1,
	wallSegs: WallSeg[],
	k: number,
	maxDistance: number,
): MvpEdge[] {
	const nodes = map.nodes;
	if (nodes.length < 2) {
		return [];
	}
	const edges: MvpEdge[] = [];
	const used = new Set<string>();
	const pairKey = (a: string, b: string) => [a, b].sort().join("--");

	for (const n of nodes) {
		const others = nodes
			.filter((m) => m.id !== n.id)
			.map((m) => ({ m, d: dist(n, m) }))
			.filter(({ d }) => d <= maxDistance)
			.sort((a, b) => a.d - b.d);

		let added = 0;
		for (const { m, d } of others) {
			if (added >= k) {
				break;
			}
			if (segmentCrossesWallSegments(n.x, n.y, m.x, m.y, wallSegs)) {
				continue;
			}
			const pk = pairKey(n.id, m.id);
			if (used.has(pk)) {
				continue;
			}
			used.add(pk);
			edges.push({
				id: `auto_${n.id}__${m.id}`,
				from: n.id,
				to: m.id,
				distance: d,
				bidirectional: true,
			});
			added++;
		}
	}
	return edges;
}

/**
 * If the map has nodes but no edges, synthesize a sparse graph by connecting each node
 * to its k nearest neighbors within `maxDistance`, **skipping links whose segment crosses a wall**.
 */
export function ensureAutoEdges(map: NavigationMvpMapV1, k = 14, maxDistance?: number): NavigationMvpMapV1 {
	if (map.edges.length > 0 || map.nodes.length < 2) {
		return map;
	}
	const wallSegs = wallSegmentsFromMap(map.walls);
	const maxD = maxDistance ?? computeMaxAutoEdgeDistance(map.nodes);
	const edges = buildWallSafeAutoEdges(map, wallSegs, k, maxD);
	return { ...map, edges };
}

/**
 * Build the graph passed to A*: keep explicit edges that do not cut through walls; if none remain,
 * synthesize wall-safe k-NN edges with progressively larger neighborhoods until some edges exist.
 */
export function prepareRoutingMap(map: NavigationMvpMapV1): NavigationMvpMapV1 {
	const wallSegs = wallSegmentsFromMap(map.walls);
	const maxBase = computeMaxAutoEdgeDistance(map.nodes);
	let edges: MvpEdge[] = [];

	if (map.edges.length > 0) {
		edges = filterEdgesCrossingWalls(map);
	}
	if (edges.length === 0) {
		const baseMap: NavigationMvpMapV1 = { ...map, edges: [] };
		for (let attempt = 0; attempt < 6; attempt++) {
			const k = 12 + attempt * 8;
			const maxD = Math.min(560, maxBase * (1 + attempt * 0.28));
			edges = buildWallSafeAutoEdges(baseMap, wallSegs, k, maxD);
			if (edges.length > 0) {
				break;
			}
		}
	}
	return { ...map, edges };
}
