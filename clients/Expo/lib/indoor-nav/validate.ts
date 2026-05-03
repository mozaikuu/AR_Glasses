import type {
	CampusMapV1,
	GraphEdge,
	GraphNode,
	IndoorBuildingV1,
	IndoorLocation,
	ParsedBuilding,
	ParsedCampus,
} from "./types";

function isVec2(v: unknown): v is { x: number; y: number } {
	if (!v || typeof v !== "object") {
		return false;
	}
	const o = v as Record<string, unknown>;
	return typeof o.x === "number" && typeof o.y === "number";
}

function isGraphNode(v: unknown): v is GraphNode {
	if (!v || typeof v !== "object") {
		return false;
	}
	const o = v as Record<string, unknown>;
	return (
		typeof o.id === "string" &&
		typeof o.floor === "number" &&
		isVec2(o.position)
	);
}

function isGraphEdge(v: unknown): v is GraphEdge {
	if (!v || typeof v !== "object") {
		return false;
	}
	const o = v as Record<string, unknown>;
	return typeof o.id === "string" && typeof o.from === "string" && typeof o.to === "string";
}

function isIndoorLocation(v: unknown): v is IndoorLocation {
	if (!v || typeof v !== "object") {
		return false;
	}
	const o = v as Record<string, unknown>;
	return (
		typeof o.id === "string" &&
		typeof o.name === "string" &&
		typeof o.floor === "number" &&
		isVec2(o.coordinates)
	);
}

function uniqueIds(ids: string[]): string | null {
	const seen = new Set<string>();
	for (const id of ids) {
		if (seen.has(id)) {
			return `Duplicate id: ${id}`;
		}
		seen.add(id);
	}
	return null;
}

export function validateIndoorBuildingV1(data: unknown): ParsedBuilding {
	if (!data || typeof data !== "object") {
		return { ok: false, error: "Invalid JSON: expected an object." };
	}
	const root = data as Record<string, unknown>;
	if (root.schemaVersion !== 1) {
		return { ok: false, error: "Missing or unsupported schemaVersion (expected 1)." };
	}
	if (!root.building || typeof root.building !== "object") {
		return { ok: false, error: "Missing building metadata." };
	}
	const b = root.building as Record<string, unknown>;
	if (typeof b.name !== "string" || !b.name.trim()) {
		return { ok: false, error: "building.name is required." };
	}
	if (!Array.isArray(root.floors) || root.floors.length === 0) {
		return { ok: false, error: "floors must be a non-empty array." };
	}
	for (const f of root.floors) {
		if (!f || typeof f !== "object") {
			return { ok: false, error: "Invalid floor entry." };
		}
		const fl = f as Record<string, unknown>;
		if (
			typeof fl.id !== "string" ||
			typeof fl.floor !== "number" ||
			typeof fl.width !== "number" ||
			typeof fl.height !== "number"
		) {
			return { ok: false, error: "Each floor needs id, floor, width, height." };
		}
	}
	if (!root.graph || typeof root.graph !== "object") {
		return { ok: false, error: "Missing graph." };
	}
	const g = root.graph as Record<string, unknown>;
	if (!Array.isArray(g.nodes) || !Array.isArray(g.edges)) {
		return { ok: false, error: "graph.nodes and graph.edges must be arrays." };
	}
	const nodes = g.nodes.filter(isGraphNode);
	if (nodes.length !== g.nodes.length) {
		return { ok: false, error: "One or more graph nodes are invalid." };
	}
	const edges = g.edges.filter(isGraphEdge);
	if (edges.length !== g.edges.length) {
		return { ok: false, error: "One or more graph edges are invalid." };
	}
	const nodeDup = uniqueIds(nodes.map((n) => n.id));
	if (nodeDup) {
		return { ok: false, error: nodeDup };
	}
	const edgeDup = uniqueIds(edges.map((e) => e.id));
	if (edgeDup) {
		return { ok: false, error: edgeDup };
	}
	const nodeIds = new Set(nodes.map((n) => n.id));
	for (const e of edges) {
		if (!nodeIds.has(e.from) || !nodeIds.has(e.to)) {
			return { ok: false, error: `Edge ${e.id} references unknown node.` };
		}
	}
	if (!Array.isArray(root.locations)) {
		return { ok: false, error: "locations must be an array." };
	}
	const locations = root.locations.filter(isIndoorLocation);
	if (locations.length !== root.locations.length) {
		return { ok: false, error: "One or more locations are invalid." };
	}
	const locDup = uniqueIds(locations.map((l) => l.id));
	if (locDup) {
		return { ok: false, error: locDup };
	}
	for (const loc of locations) {
		if (loc.nearestNodeId && !nodeIds.has(loc.nearestNodeId)) {
			return { ok: false, error: `Location ${loc.id} has unknown nearestNodeId.` };
		}
	}

	const out: IndoorBuildingV1 = {
		schemaVersion: 1,
		building: { name: String(b.name), address: typeof b.address === "string" ? b.address : undefined },
		floors: root.floors as IndoorBuildingV1["floors"],
		graph: { nodes, edges },
		locations,
		assets:
			root.assets && typeof root.assets === "object"
				? (root.assets as IndoorBuildingV1["assets"])
				: undefined,
	};
	return { ok: true, data: out };
}

export function validateCampusMapV1(data: unknown): ParsedCampus {
	if (!data || typeof data !== "object") {
		return { ok: false, error: "Invalid campus JSON." };
	}
	const root = data as Record<string, unknown>;
	if (root.schemaVersion !== 1) {
		return { ok: false, error: "Campus schemaVersion must be 1." };
	}
	if (typeof root.name !== "string" || !root.name.trim()) {
		return { ok: false, error: "Campus name is required." };
	}
	if (!root.bounds || typeof root.bounds !== "object") {
		return { ok: false, error: "Campus bounds required." };
	}
	const bounds = root.bounds as Record<string, unknown>;
	if (typeof bounds.width !== "number" || typeof bounds.height !== "number") {
		return { ok: false, error: "bounds.width and bounds.height must be numbers." };
	}
	if (!Array.isArray(root.nodes) || !Array.isArray(root.edges) || !Array.isArray(root.buildings)) {
		return { ok: false, error: "Campus nodes, edges, and buildings arrays required." };
	}
	const nodes: CampusMapV1["nodes"] = [];
	for (const n of root.nodes) {
		if (!n || typeof n !== "object") {
			return { ok: false, error: "Invalid campus node." };
		}
		const o = n as Record<string, unknown>;
		if (typeof o.id !== "string" || !isVec2(o.position)) {
			return { ok: false, error: "Campus node needs id and position." };
		}
		nodes.push({
			id: o.id,
			position: o.position,
			label: typeof o.label === "string" ? o.label : undefined,
			kind: o.kind === "path" || o.kind === "entrance" || o.kind === "landmark" ? o.kind : undefined,
			buildingId: typeof o.buildingId === "string" ? o.buildingId : undefined,
			qrPayload: typeof o.qrPayload === "string" ? o.qrPayload : undefined,
		});
	}
	const edges: CampusMapV1["edges"] = [];
	for (const e of root.edges) {
		if (!e || typeof e !== "object") {
			return { ok: false, error: "Invalid campus edge." };
		}
		const o = e as Record<string, unknown>;
		if (typeof o.id !== "string" || typeof o.from !== "string" || typeof o.to !== "string") {
			return { ok: false, error: "Campus edge needs id, from, to." };
		}
		edges.push({
			id: o.id,
			from: o.from,
			to: o.to,
			bidirectional: typeof o.bidirectional === "boolean" ? o.bidirectional : undefined,
			weight: typeof o.weight === "number" ? o.weight : undefined,
		});
	}
	const buildings: CampusMapV1["buildings"] = [];
	for (const b of root.buildings) {
		if (!b || typeof b !== "object") {
			return { ok: false, error: "Invalid campus building entry." };
		}
		const o = b as Record<string, unknown>;
		if (
			typeof o.id !== "string" ||
			typeof o.name !== "string" ||
			typeof o.entranceNodeId !== "string" ||
			typeof o.indoorBundleId !== "string" ||
			typeof o.indoorStartNodeId !== "string"
		) {
			return { ok: false, error: "Each building needs id, name, entranceNodeId, indoorBundleId, indoorStartNodeId." };
		}
		buildings.push({
			id: o.id,
			name: o.name,
			entranceNodeId: o.entranceNodeId,
			indoorBundleId: o.indoorBundleId,
			indoorStartNodeId: o.indoorStartNodeId,
		});
	}
	const dup = uniqueIds(nodes.map((n) => n.id));
	if (dup) {
		return { ok: false, error: dup };
	}
	const nset = new Set(nodes.map((n) => n.id));
	for (const e of edges) {
		if (!nset.has(e.from) || !nset.has(e.to)) {
			return { ok: false, error: `Campus edge ${e.id} references unknown node.` };
		}
	}
	for (const b of buildings) {
		if (!nset.has(b.entranceNodeId)) {
			return { ok: false, error: `Building ${b.id} entranceNodeId not found on campus graph.` };
		}
	}

	const out: CampusMapV1 = {
		schemaVersion: 1,
		name: root.name,
		bounds: { width: bounds.width, height: bounds.height },
		nodes,
		edges,
		buildings,
	};
	return { ok: true, data: out };
}
