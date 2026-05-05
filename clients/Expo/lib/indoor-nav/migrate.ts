import { distance } from "./graph";
import type {
	FloorMeta,
	GraphEdge,
	GraphNode,
	IndoorBuildingV1,
	IndoorLocation,
} from "./types";

type LegacyNavJson = {
	building?: { name?: string; address?: string };
	locations?: IndoorLocation[];
};

function mean(nums: number[]): number {
	if (nums.length === 0) {
		return 0;
	}
	return nums.reduce((a, b) => a + b, 0) / nums.length;
}

/**
 * If JSON has legacy `navigation.json` shape (no graph / schemaVersion),
 * synthesize a star-like graph per floor so routing still works for MVP imports.
 */
export function migrateLegacyNavigationJson(raw: unknown): IndoorBuildingV1 | null {
	if (!raw || typeof raw !== "object") {
		return null;
	}
	const root = raw as LegacyNavJson;
	if (!Array.isArray(root.locations) || root.locations.length === 0) {
		return null;
	}
	// Already v1?
	if ("schemaVersion" in root && (root as { schemaVersion?: unknown }).schemaVersion === 1) {
		return null;
	}

	const locations: IndoorLocation[] = root.locations
		.filter(
			(loc): loc is IndoorLocation =>
				!!loc &&
				typeof loc === "object" &&
				typeof (loc as IndoorLocation).id === "string" &&
				typeof (loc as IndoorLocation).name === "string" &&
				typeof (loc as IndoorLocation).floor === "number" &&
				typeof (loc as IndoorLocation).coordinates === "object",
		)
		.map((loc) => ({ ...loc }));

	const floorsSet = new Set(locations.map((l) => l.floor));
	const floors: FloorMeta[] = [...floorsSet].sort((a, b) => a - b).map((f) => {
		const onFloor = locations.filter((l) => l.floor === f);
		const xs: number[] = [];
		const ys: number[] = [];
		for (const l of onFloor) {
			xs.push(l.coordinates.x, l.coordinates.x + (l.size?.width ?? 0));
			ys.push(l.coordinates.y, l.coordinates.y + (l.size?.height ?? 0));
		}
		const pad = 3;
		const minX = Math.min(...xs) - pad;
		const maxX = Math.max(...xs) + pad;
		const minY = Math.min(...ys) - pad;
		const maxY = Math.max(...ys) + pad;
		return {
			id: `floor_${f}`,
			floor: f,
			width: Math.max(8, maxX - minX),
			height: Math.max(8, maxY - minY),
		};
	});

	const nodes: GraphNode[] = [];
	const edges: GraphEdge[] = [];
	let edgeSeq = 0;

	for (const f of floorsSet) {
		const onFloor = locations.filter((l) => l.floor === f);
		const cx = mean(onFloor.map((l) => l.coordinates.x));
		const cy = mean(onFloor.map((l) => l.coordinates.y));
		const hubId = `hub_floor_${f}`;
		nodes.push({
			id: hubId,
			floor: f,
			position: { x: cx, y: cy },
			label: `Floor ${f} hub`,
			qrPayload: `nav:checkpoint:${hubId}`,
		});

		for (const loc of onFloor) {
			const nid = `node_${loc.id}`;
			nodes.push({
				id: nid,
				floor: f,
				position: { ...loc.coordinates },
				label: loc.name,
				qrPayload: `nav:checkpoint:${nid}`,
			});
			loc.nearestNodeId = nid;
			const w = distance({ x: cx, y: cy }, loc.coordinates);
			edges.push({
				id: `e_${edgeSeq++}`,
				from: hubId,
				to: nid,
				bidirectional: true,
				weight: Math.max(0.5, w),
			});
		}
	}

	const sortedFloors = [...floorsSet].sort((a, b) => a - b);
	for (let i = 0; i < sortedFloors.length - 1; i++) {
		const a = sortedFloors[i];
		const b = sortedFloors[i + 1];
		const ha = `hub_floor_${a}`;
		const hb = `hub_floor_${b}`;
		edges.push({
			id: `e_${edgeSeq++}`,
			from: ha,
			to: hb,
			bidirectional: true,
			weight: 5,
		});
	}

	const buildingName =
		root.building && typeof root.building.name === "string" && root.building.name.trim()
			? root.building.name
			: "Imported Building";

	const out: IndoorBuildingV1 = {
		schemaVersion: 1,
		building: {
			name: buildingName,
			address:
				root.building && typeof root.building.address === "string"
					? root.building.address
					: undefined,
		},
		floors,
		graph: { nodes, edges },
		locations,
	};
	return out;
}
