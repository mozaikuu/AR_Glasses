import { astar, astarCampus, distance } from "./graph";
import type { CampusMapV1, GraphNode, IndoorBuildingV1, IndoorLocation } from "./types";

export function goalNodeIdForLocation(
	location: IndoorLocation,
	nodes: GraphNode[],
): string | null {
	if (location.nearestNodeId) {
		const exists = nodes.some((n) => n.id === location.nearestNodeId);
		if (exists) {
			return location.nearestNodeId;
		}
	}
	const onFloor = nodes.filter((n) => n.floor === location.floor);
	if (onFloor.length === 0) {
		return null;
	}
	let best: GraphNode | null = null;
	let bestD = Infinity;
	for (const n of onFloor) {
		const d = distance(n.position, location.coordinates);
		if (d < bestD) {
			bestD = d;
			best = n;
		}
	}
	return best?.id ?? null;
}

export function routeIndoor(
	building: IndoorBuildingV1,
	startNodeId: string,
	destination: IndoorLocation,
): string[] | null {
	const goal = goalNodeIdForLocation(destination, building.graph.nodes);
	if (!goal) {
		return null;
	}
	return astar(startNodeId, goal, building.graph.nodes, building.graph.edges);
}

export function routeCampus(
	campus: CampusMapV1,
	startNodeId: string,
	goalNodeId: string,
): string[] | null {
	return astarCampus(startNodeId, goalNodeId, campus.nodes, campus.edges);
}
