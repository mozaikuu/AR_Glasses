import type { GraphEdge, GraphNode, IndoorBuildingV1, IndoorLocation } from "./types";

function nextEdgeId(edges: GraphEdge[]): string {
	let n = edges.length;
	while (edges.some((e) => e.id === `edge_${n}`)) {
		n += 1;
	}
	return `edge_${n}`;
}

function nextNodeId(nodes: GraphNode[], prefix: string): string {
	let n = nodes.length;
	while (nodes.some((x) => x.id === `${prefix}_${n}`)) {
		n += 1;
	}
	return `${prefix}_${n}`;
}

export function addGraphNode(
	building: IndoorBuildingV1,
	partial: Omit<GraphNode, "id"> & { id?: string },
): IndoorBuildingV1 {
	const id = partial.id ?? nextNodeId(building.graph.nodes, "node");
	const node: GraphNode = {
		id,
		floor: partial.floor,
		position: { ...partial.position },
		label: partial.label,
		qrPayload: partial.qrPayload ?? `nav:checkpoint:${id}`,
	};
	return {
		...building,
		graph: {
			nodes: [...building.graph.nodes, node],
			edges: building.graph.edges,
		},
	};
}

export function updateGraphNode(building: IndoorBuildingV1, id: string, patch: Partial<GraphNode>): IndoorBuildingV1 {
	return {
		...building,
		graph: {
			nodes: building.graph.nodes.map((n) =>
				n.id === id
					? {
							...n,
							...patch,
							position: patch.position ? { ...patch.position } : n.position,
						}
					: n,
			),
			edges: building.graph.edges,
		},
	};
}

export function deleteGraphNode(building: IndoorBuildingV1, id: string): IndoorBuildingV1 {
	return {
		...building,
		locations: building.locations.map((loc) =>
			loc.nearestNodeId === id ? { ...loc, nearestNodeId: undefined } : loc,
		),
		graph: {
			nodes: building.graph.nodes.filter((n) => n.id !== id),
			edges: building.graph.edges.filter((e) => e.from !== id && e.to !== id),
		},
	};
}

export function addGraphEdge(
	building: IndoorBuildingV1,
	from: string,
	to: string,
	bidirectional = true,
): IndoorBuildingV1 {
	const id = nextEdgeId(building.graph.edges);
	const edge: GraphEdge = { id, from, to, bidirectional };
	return {
		...building,
		graph: {
			nodes: building.graph.nodes,
			edges: [...building.graph.edges, edge],
		},
	};
}

export function deleteGraphEdge(building: IndoorBuildingV1, edgeId: string): IndoorBuildingV1 {
	return {
		...building,
		graph: {
			nodes: building.graph.nodes,
			edges: building.graph.edges.filter((e) => e.id !== edgeId),
		},
	};
}

export function addLocation(building: IndoorBuildingV1, loc: IndoorLocation): IndoorBuildingV1 {
	return {
		...building,
		locations: [...building.locations, { ...loc }],
	};
}

export function updateLocation(building: IndoorBuildingV1, id: string, patch: Partial<IndoorLocation>): IndoorBuildingV1 {
	return {
		...building,
		locations: building.locations.map((l) =>
			l.id === id
				? {
						...l,
						...patch,
						coordinates: patch.coordinates ? { ...patch.coordinates } : l.coordinates,
						size: patch.size ? { ...patch.size } : l.size,
					}
				: l,
		),
	};
}

export function deleteLocation(building: IndoorBuildingV1, id: string): IndoorBuildingV1 {
	return {
		...building,
		locations: building.locations.filter((l) => l.id !== id),
	};
}

export function ensureFloorMeta(building: IndoorBuildingV1, floor: number, width = 120, height = 80): IndoorBuildingV1 {
	if (building.floors.some((f) => f.floor === floor)) {
		return building;
	}
	return {
		...building,
		floors: [
			...building.floors,
			{ id: `floor_${floor}`, floor, width, height },
		].sort((a, b) => a.floor - b.floor),
	};
}
