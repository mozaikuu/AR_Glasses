/**
 * Versioned schemas for indoor navigation MVP.
 * `IndoorBuildingV1` is the primary building dataset (graph + rooms + schedules).
 * `CampusMapV1` is optional campus-level routing between building entrances.
 */

export type Vec2 = { x: number; y: number };

export type NavigationStaff = {
	name: string;
	deskLabel?: string;
	role?: string;
	email?: string;
	officeDays?: string[];
	officeHours?: string;
	coursesTaught?: string[];
};

export type LectureSlot = {
	courseName: string;
	courseCode?: string;
	instructor: string;
	day: string;
	startTime: string;
	endTime: string;
};

/** Semantic kind for map editor and rendering (optional on legacy data). */
export type MapPlaceKind =
	| "room"
	| "stairs"
	| "bathroom"
	| "elevator"
	| "office"
	| "lecture_room"
	| "lab"
	| "corridor"
	| "service"
	| "garden"
	| "storage"
	| "general";

/** A navigable POI / room (extends legacy navigation.json location fields). */
export type IndoorLocation = {
	id: string;
	name: string;
	floor: number;
	coordinates: Vec2;
	description?: string;
	additional_info?: string;
	placeType?: string | number;
	proximityRadius?: number;
	staff?: NavigationStaff[];
	lectures?: LectureSlot[];
	/** Graph node used as routing anchor for this room (recommended). */
	nearestNodeId?: string;
	/** Building number from notation like 2-1-46 (building 2). */
	buildingId?: string;
	/** Full code e.g. `2-1-46` for display and export. */
	roomCode?: string;
	/** Map editor category. */
	mapKind?: MapPlaceKind;
	/** Short marker on map (e.g. `46`, `S`, `B`). */
	shortLabel?: string;
	/** Footprint in map units (top-left at coordinates). */
	size?: { width: number; height: number };
	/** If true, do not treat as a navigable destination in lists. */
	isNavObstacle?: boolean;
};

export type GraphNode = {
	id: string;
	floor: number;
	position: Vec2;
	label?: string;
	/** If set, QR scan must match this exact string to snap here. */
	qrPayload?: string;
};

export type GraphEdge = {
	id: string;
	from: string;
	to: string;
	/** Default true if omitted. */
	bidirectional?: boolean;
	/** Optional override; default is Euclidean distance from node positions. */
	weight?: number;
};

export type FloorMeta = {
	id: string;
	floor: number;
	width: number;
	height: number;
	backgroundImageUri?: string;
};

export type IndoorBuildingV1 = {
	schemaVersion: 1;
	building: { name: string; address?: string };
	floors: FloorMeta[];
	graph: { nodes: GraphNode[]; edges: GraphEdge[] };
	locations: IndoorLocation[];
	assets?: {
		lidarRef?: string;
		panoramas?: Record<string, string>;
	};
};

export type CampusNodeKind = "path" | "entrance" | "landmark";

export type CampusNode = {
	id: string;
	position: Vec2;
	label?: string;
	kind?: CampusNodeKind;
	/** When kind is entrance, links to building id for handoff UI. */
	buildingId?: string;
	qrPayload?: string;
};

export type CampusEdge = {
	id: string;
	from: string;
	to: string;
	bidirectional?: boolean;
	weight?: number;
};

export type CampusBuildingRef = {
	id: string;
	name: string;
	/** Campus graph node id (usually an entrance). */
	entranceNodeId: string;
	/** Key into bundled or imported indoor datasets. */
	indoorBundleId: string;
	/** First indoor graph node id after entering this building. */
	indoorStartNodeId: string;
};

export type CampusMapV1 = {
	schemaVersion: 1;
	name: string;
	bounds: { width: number; height: number };
	nodes: CampusNode[];
	edges: CampusEdge[];
	buildings: CampusBuildingRef[];
};

export type ParsedBuilding =
	| { ok: true; data: IndoorBuildingV1 }
	| { ok: false; error: string };

export type ParsedCampus =
	| { ok: true; data: CampusMapV1 }
	| { ok: false; error: string };
