import type { NavigationMvpMapV1, MvpEdge, MvpNode } from "./types";

function dist(a: MvpNode, b: MvpNode): number {
	return Math.hypot(a.x - b.x, a.y - b.y);
}

/**
 * If the map has nodes but no edges, synthesize a sparse graph by connecting each node
 * to its k nearest neighbors within `maxDistance`.
 */
export function ensureAutoEdges(map: NavigationMvpMapV1, k = 3, maxDistance = 320): NavigationMvpMapV1 {
	if (map.edges.length > 0 || map.nodes.length < 2) {
		return map;
	}

	const edges: MvpEdge[] = [];
	const used = new Set<string>();
	const key = (a: string, b: string) => [a, b].sort().join("--");

	for (const n of map.nodes) {
		const others = map.nodes
			.filter((m) => m.id !== n.id)
			.map((m) => ({ m, d: dist(n, m) }))
			.filter(({ d }) => d <= maxDistance)
			.sort((a, b) => a.d - b.d)
			.slice(0, k);

		for (const { m, d } of others) {
			const k0 = key(n.id, m.id);
			if (used.has(k0)) {
				continue;
			}
			used.add(k0);
			edges.push({
				id: `auto_${n.id}__${m.id}`,
				from: n.id,
				to: m.id,
				distance: d,
				bidirectional: true,
			});
		}
	}

	return { ...map, edges };
}
