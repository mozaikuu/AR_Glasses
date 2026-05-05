import type {
	BundleFloorEntry,
	MvpStairLink,
	NavigationMvpBundleV1,
	NavigationMvpMapV1,
	ParsedNavigationMvpBundle,
	ParsedNavigationMvpMap,
	Vec2,
} from "./types";
import { NAVIGATION_MVP_SCHEMA_VERSION } from "./types";

function isVec2(v: unknown): v is Vec2 {
	if (!v || typeof v !== "object") {
		return false;
	}
	const o = v as Record<string, unknown>;
	return typeof o.x === "number" && Number.isFinite(o.x) && typeof o.y === "number" && Number.isFinite(o.y);
}

function isVec2Array(a: unknown, minLen: number): a is Vec2[] {
	return Array.isArray(a) && a.length >= minLen && a.every(isVec2);
}

/**
 * Parse and validate unknown JSON into `NavigationMvpMapV1`.
 */
export function parseNavigationMvpMap(raw: unknown): ParsedNavigationMvpMap {
	if (!raw || typeof raw !== "object") {
		return { ok: false, error: "Map root must be an object." };
	}
	const o = raw as Record<string, unknown>;
	if (o.schemaVersion !== NAVIGATION_MVP_SCHEMA_VERSION) {
		return { ok: false, error: `Unsupported schemaVersion (expected ${NAVIGATION_MVP_SCHEMA_VERSION}).` };
	}
	if (typeof o.name !== "string" || !o.name.trim()) {
		return { ok: false, error: "Map name is required." };
	}
	if (typeof o.scale !== "number" || !Number.isFinite(o.scale) || o.scale <= 0) {
		return { ok: false, error: "Map scale must be a positive finite number." };
	}

	const walls = o.walls;
	const rooms = o.rooms;
	const labels = o.labels;
	const pois = o.pois;
	const nodes = o.nodes;
	const edges = o.edges;

	if (!Array.isArray(walls) || !Array.isArray(rooms) || !Array.isArray(labels) || !Array.isArray(pois)) {
		return { ok: false, error: "walls, rooms, labels, and pois must be arrays." };
	}
	if (!Array.isArray(nodes) || !Array.isArray(edges)) {
		return { ok: false, error: "nodes and edges must be arrays." };
	}

	const outWalls: NavigationMvpMapV1["walls"] = [];
	for (const w of walls) {
		if (!w || typeof w !== "object") {
			return { ok: false, error: "Invalid wall entry." };
		}
		const we = w as Record<string, unknown>;
		if (typeof we.id !== "string" || !we.id.trim()) {
			return { ok: false, error: "Each wall requires a non-empty id." };
		}
		if (!isVec2Array(we.points, 2)) {
			return { ok: false, error: `Wall ${we.id} needs at least two {x,y} points.` };
		}
		outWalls.push({ id: we.id.trim(), points: we.points });
	}

	const outRooms: NavigationMvpMapV1["rooms"] = [];
	for (const r of rooms) {
		if (!r || typeof r !== "object") {
			return { ok: false, error: "Invalid room entry." };
		}
		const re = r as Record<string, unknown>;
		if (typeof re.id !== "string" || !re.id.trim()) {
			return { ok: false, error: "Each room requires a non-empty id." };
		}
		if (!isVec2Array(re.polygon, 3)) {
			return { ok: false, error: `Room ${re.id} needs a polygon with at least three {x,y} points.` };
		}
		outRooms.push({
			id: re.id.trim(),
			polygon: re.polygon,
			name: typeof re.name === "string" ? re.name : undefined,
		});
	}

	const outLabels: NavigationMvpMapV1["labels"] = [];
	for (const l of labels) {
		if (!l || typeof l !== "object") {
			return { ok: false, error: "Invalid label entry." };
		}
		const le = l as Record<string, unknown>;
		if (typeof le.id !== "string" || !le.id.trim()) {
			return { ok: false, error: "Each label requires a non-empty id." };
		}
		if (typeof le.text !== "string" || typeof le.x !== "number" || typeof le.y !== "number") {
			return { ok: false, error: `Label ${le.id} needs text, x, and y.` };
		}
		outLabels.push({ id: le.id.trim(), text: le.text, x: le.x, y: le.y });
	}

	const allowedPoi = new Set([
		"entrance",
		"elevator",
		"stairs",
		"toilet",
		"office",
		"classroom",
		"generic",
	]);
	const outPois: NavigationMvpMapV1["pois"] = [];
	for (const p of pois) {
		if (!p || typeof p !== "object") {
			return { ok: false, error: "Invalid POI entry." };
		}
		const pe = p as Record<string, unknown>;
		if (typeof pe.id !== "string" || !pe.id.trim()) {
			return { ok: false, error: "Each POI requires a non-empty id." };
		}
		if (typeof pe.type !== "string" || !allowedPoi.has(pe.type)) {
			return { ok: false, error: `POI ${pe.id} has invalid type.` };
		}
		if (typeof pe.x !== "number" || typeof pe.y !== "number") {
			return { ok: false, error: `POI ${pe.id} needs numeric x and y.` };
		}
		outPois.push({
			id: pe.id.trim(),
			type: pe.type as NavigationMvpMapV1["pois"][number]["type"],
			x: pe.x,
			y: pe.y,
		});
	}

	const outNodes: NavigationMvpMapV1["nodes"] = [];
	for (const n of nodes) {
		if (!n || typeof n !== "object") {
			return { ok: false, error: "Invalid node entry." };
		}
		const ne = n as Record<string, unknown>;
		if (typeof ne.id !== "string" || !ne.id.trim()) {
			return { ok: false, error: "Each node requires a non-empty id." };
		}
		if (typeof ne.x !== "number" || typeof ne.y !== "number") {
			return { ok: false, error: `Node ${ne.id} needs numeric x and y.` };
		}
		outNodes.push({
			id: ne.id.trim(),
			x: ne.x,
			y: ne.y,
			label: typeof ne.label === "string" ? ne.label : undefined,
		});
	}

	const nodeIds = new Set(outNodes.map((n) => n.id));
	const outEdges: NavigationMvpMapV1["edges"] = [];
	for (const e of edges) {
		if (!e || typeof e !== "object") {
			return { ok: false, error: "Invalid edge entry." };
		}
		const ee = e as Record<string, unknown>;
		if (typeof ee.id !== "string" || !ee.id.trim()) {
			return { ok: false, error: "Each edge requires a non-empty id." };
		}
		if (typeof ee.from !== "string" || typeof ee.to !== "string") {
			return { ok: false, error: `Edge ${ee.id} needs from and to node ids.` };
		}
		if (!nodeIds.has(ee.from) || !nodeIds.has(ee.to)) {
			return { ok: false, error: `Edge ${ee.id} references unknown node(s).` };
		}
		const dist =
			typeof ee.distance === "number" && Number.isFinite(ee.distance) && ee.distance > 0 ? ee.distance : undefined;
		outEdges.push({
			id: ee.id.trim(),
			from: ee.from,
			to: ee.to,
			distance: dist,
			bidirectional: typeof ee.bidirectional === "boolean" ? ee.bidirectional : undefined,
		});
	}

	const data: NavigationMvpMapV1 = {
		schemaVersion: NAVIGATION_MVP_SCHEMA_VERSION,
		name: o.name.trim(),
		scale: o.scale,
		walls: outWalls,
		rooms: outRooms,
		labels: outLabels,
		pois: outPois,
		nodes: outNodes,
		edges: outEdges,
	};
	return { ok: true, data };
}

/**
 * Parse `uni-bundle.json` (multi-floor building with embedded maps).
 */
export function parseBuildingBundle(raw: unknown): ParsedNavigationMvpBundle {
	if (!raw || typeof raw !== "object") {
		return { ok: false, error: "Bundle root must be an object." };
	}
	const o = raw as Record<string, unknown>;
	if (o.schemaVersion !== NAVIGATION_MVP_SCHEMA_VERSION) {
		return { ok: false, error: `Unsupported schemaVersion (expected ${NAVIGATION_MVP_SCHEMA_VERSION}).` };
	}
	if (typeof o.name !== "string" || !o.name.trim()) {
		return { ok: false, error: "Bundle name is required." };
	}
	const floors = o.floors;
	const stairs = o.stairs;
	if (!Array.isArray(floors) || floors.length === 0) {
		return { ok: false, error: "floors must be a non-empty array." };
	}
	if (!Array.isArray(stairs)) {
		return { ok: false, error: "stairs must be an array." };
	}

	const outFloors: BundleFloorEntry[] = [];
	for (const f of floors) {
		if (!f || typeof f !== "object") {
			return { ok: false, error: "Invalid floor entry." };
		}
		const fe = f as Record<string, unknown>;
		if (typeof fe.index !== "number" || !Number.isInteger(fe.index)) {
			return { ok: false, error: "Each floor needs an integer index." };
		}
		if (typeof fe.level !== "string" || !fe.level.trim()) {
			return { ok: false, error: "Each floor needs a level name." };
		}
		const vr = fe.verticalRange;
		if (
			!Array.isArray(vr) ||
			vr.length !== 2 ||
			typeof vr[0] !== "number" ||
			typeof vr[1] !== "number"
		) {
			return { ok: false, error: "Each floor needs verticalRange [number, number]." };
		}
		const mapRaw = fe.map;
		const parsedMap = parseNavigationMvpMap(mapRaw);
		if (!parsedMap.ok) {
			return { ok: false, error: `Floor ${fe.index}: ${parsedMap.error}` };
		}
		const mapPath = typeof fe.mapPath === "string" ? fe.mapPath : undefined;
		outFloors.push({
			index: fe.index,
			level: fe.level.trim(),
			verticalRange: [vr[0], vr[1]],
			mapPath,
			map: parsedMap.data,
		});
	}

	const outStairs: MvpStairLink[] = [];
	for (const s of stairs) {
		if (!s || typeof s !== "object") {
			return { ok: false, error: "Invalid stair entry." };
		}
		const se = s as Record<string, unknown>;
		if (typeof se.id !== "string" || !se.id.trim()) {
			return { ok: false, error: "Each stair link needs an id." };
		}
		if (
			typeof se.x !== "number" ||
			typeof se.y !== "number" ||
			typeof se.fromFloor !== "number" ||
			typeof se.toFloor !== "number"
		) {
			return { ok: false, error: `Stair ${se.id} needs x, y, fromFloor, toFloor.` };
		}
		outStairs.push({
			id: se.id.trim(),
			x: se.x,
			y: se.y,
			fromFloor: se.fromFloor,
			toFloor: se.toFloor,
		});
	}

	const data: NavigationMvpBundleV1 = {
		schemaVersion: NAVIGATION_MVP_SCHEMA_VERSION,
		name: o.name.trim(),
		floors: outFloors,
		stairs: outStairs,
	};
	return { ok: true, data };
}
