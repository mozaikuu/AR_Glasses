import { astar } from "@/lib/indoor-nav/graph";
import type { Vec2 } from "@/lib/indoor-nav/types";

import type { MvpStairLink, NavigationMvpMapV1 } from "./types";
import { ensureAutoEdges } from "./edges";
import { toIndoorGraph } from "./mapAdapters";

export type RouteLeg = { floorIndex: number; nodeIds: string[] };

export function nearestNodeId(map: NavigationMvpMapV1, x: number, y: number): string | null {
	if (map.nodes.length === 0) {
		return null;
	}
	let best: string | null = null;
	let bestD = Infinity;
	for (const n of map.nodes) {
		const d = Math.hypot(n.x - x, n.y - y);
		if (d < bestD) {
			bestD = d;
			best = n.id;
		}
	}
	return best;
}

export function routeBetweenNodeIds(
	map: NavigationMvpMapV1,
	startId: string,
	goalId: string,
): string[] | null {
	const withEdges = ensureAutoEdges(map);
	const { nodes, edges } = toIndoorGraph(withEdges);
	return astar(startId, goalId, nodes, edges);
}

export function nodeIdsToPolyline(map: NavigationMvpMapV1, nodeIds: string[]): Vec2[] {
	const byId = new Map(map.nodes.map((n) => [n.id, n]));
	const out: Vec2[] = [];
	for (const id of nodeIds) {
		const n = byId.get(id);
		if (n) {
			out.push({ x: n.x, y: n.y });
		}
	}
	return out;
}

export function routeLength(map: NavigationMvpMapV1, nodeIds: string[]): number {
	if (nodeIds.length < 2) {
		return 0;
	}
	const byId = new Map(map.nodes.map((n) => [n.id, n]));
	let sum = 0;
	for (let i = 1; i < nodeIds.length; i++) {
		const a = byId.get(nodeIds[i - 1]!);
		const b = byId.get(nodeIds[i]!);
		if (a && b) {
			sum += Math.hypot(b.x - a.x, b.y - a.y);
		}
	}
	return sum;
}

/**
 * Same-floor uses `routeBetweenNodeIds`. Multi-floor: chain A* legs via nearest graph node
 * to each stair link's (x, y) on consecutive floors (manifest `stairs`).
 */
export function routeMultiFloor(
	mapsByFloorIndex: Map<number, NavigationMvpMapV1>,
	stairs: MvpStairLink[],
	startFloor: number,
	goalFloor: number,
	startNodeId: string,
	goalNodeId: string,
): RouteLeg[] | null {
	if (startFloor === goalFloor) {
		const m = mapsByFloorIndex.get(startFloor);
		if (!m) {
			return null;
		}
		const path = routeBetweenNodeIds(m, startNodeId, goalNodeId);
		if (!path || path.length === 0) {
			return null;
		}
		return [{ floorIndex: startFloor, nodeIds: path }];
	}
	const inc = goalFloor > startFloor ? 1 : -1;
	const legs: RouteLeg[] = [];
	let curFloor = startFloor;
	let curNode = startNodeId;

	while (curFloor !== goalFloor) {
		const nextFloor = curFloor + inc;
		const link = stairs.find(
			(s) =>
				(s.fromFloor === curFloor && s.toFloor === nextFloor) ||
				(s.fromFloor === nextFloor && s.toFloor === curFloor),
		);
		if (!link) {
			return null;
		}
		const mCur = mapsByFloorIndex.get(curFloor);
		const mNext = mapsByFloorIndex.get(nextFloor);
		if (!mCur || !mNext) {
			return null;
		}
		const nStairCur = nearestNodeId(mCur, link.x, link.y);
		const nStairNext = nearestNodeId(mNext, link.x, link.y);
		if (!nStairCur || !nStairNext) {
			return null;
		}
		const toStair = routeBetweenNodeIds(mCur, curNode, nStairCur);
		if (!toStair || toStair.length === 0) {
			return null;
		}
		legs.push({ floorIndex: curFloor, nodeIds: toStair });
		curFloor = nextFloor;
		curNode = nStairNext;
	}
	const mGoal = mapsByFloorIndex.get(goalFloor);
	if (!mGoal) {
		return null;
	}
	const last = routeBetweenNodeIds(mGoal, curNode, goalNodeId);
	if (!last || last.length === 0) {
		return null;
	}
	legs.push({ floorIndex: goalFloor, nodeIds: last });
	return legs;
}

export function routeLegsTotalLength(
	mapsByFloorIndex: Map<number, NavigationMvpMapV1>,
	legs: RouteLeg[],
): number {
	let sum = 0;
	for (const leg of legs) {
		const m = mapsByFloorIndex.get(leg.floorIndex);
		if (m) {
			sum += routeLength(m, leg.nodeIds);
		}
	}
	return sum;
}
