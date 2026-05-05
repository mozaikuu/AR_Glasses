import type { GraphEdge, GraphNode, Vec2 } from "./types";

export function distance(a: Vec2, b: Vec2): number {
	const dx = a.x - b.x;
	const dy = a.y - b.y;
	return Math.hypot(dx, dy);
}

function edgeWeight(
	nodesById: Map<string, GraphNode>,
	e: GraphEdge,
	forward: boolean,
): number {
	if (typeof e.weight === "number" && e.weight > 0) {
		return e.weight;
	}
	const a = nodesById.get(forward ? e.from : e.to);
	const b = nodesById.get(forward ? e.to : e.from);
	if (!a || !b) {
		return 1;
	}
	return Math.max(0.01, distance(a.position, b.position));
}

/** Undirected adjacency list (each edge added both ways when bidirectional). */
export function buildAdjacency(
	nodes: GraphNode[],
	edges: GraphEdge[],
): Map<string, { to: string; weight: number; edgeId: string }[]> {
	const byId = new Map(nodes.map((n) => [n.id, n]));
	const adj = new Map<string, { to: string; weight: number; edgeId: string }[]>();

	for (const n of nodes) {
		adj.set(n.id, []);
	}

	for (const e of edges) {
		const bi = e.bidirectional !== false;
		const wForward = edgeWeight(byId, e, true);
		adj.get(e.from)?.push({ to: e.to, weight: wForward, edgeId: e.id });
		if (bi) {
			const wBack = edgeWeight(byId, e, false);
			adj.get(e.to)?.push({ to: e.from, weight: wBack, edgeId: e.id });
		}
	}

	return adj;
}

export function astar(
	startId: string,
	goalId: string,
	nodes: GraphNode[],
	edges: GraphEdge[],
): string[] | null {
	const byId = new Map(nodes.map((n) => [n.id, n]));
	if (!byId.has(startId) || !byId.has(goalId)) {
		return null;
	}

	const adj = buildAdjacency(nodes, edges);
	const heuristic = (id: string): number => {
		const a = byId.get(id);
		const g = byId.get(goalId);
		if (!a || !g) {
			return 0;
		}
		return distance(a.position, g.position);
	};

	const open = new Set<string>([startId]);
	const cameFrom = new Map<string, string>();
	const gScore = new Map<string, number>();
	const fScore = new Map<string, number>();

	for (const n of nodes) {
		gScore.set(n.id, Infinity);
		fScore.set(n.id, Infinity);
	}
	gScore.set(startId, 0);
	fScore.set(startId, heuristic(startId));

	while (open.size > 0) {
		let current = "";
		let bestF = Infinity;
		for (const id of open) {
			const f = fScore.get(id) ?? Infinity;
			if (f < bestF) {
				bestF = f;
				current = id;
			}
		}

		if (current === goalId) {
			const path: string[] = [];
			let c: string | undefined = current;
			while (c) {
				path.push(c);
				c = cameFrom.get(c);
			}
			path.reverse();
			return path;
		}

		open.delete(current);
		const neigh = adj.get(current) ?? [];
		for (const { to, weight } of neigh) {
			const tentative = (gScore.get(current) ?? Infinity) + weight;
			if (tentative < (gScore.get(to) ?? Infinity)) {
				cameFrom.set(to, current);
				gScore.set(to, tentative);
				fScore.set(to, tentative + heuristic(to));
				open.add(to);
			}
		}
	}

	return null;
}

/** A* on campus graph (same structure as indoor graph). */
export function astarCampus(
	startId: string,
	goalId: string,
	nodes: { id: string; position: Vec2 }[],
	edges: { id: string; from: string; to: string; bidirectional?: boolean; weight?: number }[],
): string[] | null {
	const graphNodes: GraphNode[] = nodes.map((n) => ({
		id: n.id,
		floor: 0,
		position: n.position,
	}));
	const graphEdges: GraphEdge[] = edges.map((e) => ({
		id: e.id,
		from: e.from,
		to: e.to,
		bidirectional: e.bidirectional,
		weight: e.weight,
	}));
	return astar(startId, goalId, graphNodes, graphEdges);
}
