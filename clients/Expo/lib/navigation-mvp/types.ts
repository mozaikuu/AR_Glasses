/**
 * Indoor navigation MVP map format (Megaprompt-aligned, pixel / map units).
 * Coordinates are simple 2D numbers; not geographic lat/lon.
 */

export const NAVIGATION_MVP_SCHEMA_VERSION = 1 as const;

export type Vec2 = { x: number; y: number };

export type MvpWall = {
	id: string;
	/** Two or more points forming a polyline in map space. */
	points: Vec2[];
};

export type MvpRoom = {
	id: string;
	/** Closed polygon in map space (first point may repeat last; both accepted). */
	polygon: Vec2[];
	name?: string;
};

export type MvpLabel = {
	id: string;
	text: string;
	x: number;
	y: number;
};

export type MvpPoiType =
	| "entrance"
	| "elevator"
	| "stairs"
	| "toilet"
	| "office"
	| "classroom"
	| "generic";

export type MvpPoi = {
	id: string;
	type: MvpPoiType;
	x: number;
	y: number;
};

export type MvpNode = {
	id: string;
	x: number;
	y: number;
	label?: string;
};

export type MvpEdge = {
	id: string;
	from: string;
	to: string;
	/** Optional; default is Euclidean distance derived from node positions. */
	distance?: number;
	bidirectional?: boolean;
};

export type NavigationMvpMapV1 = {
	schemaVersion: typeof NAVIGATION_MVP_SCHEMA_VERSION;
	name: string;
	scale: number;
	walls: MvpWall[];
	rooms: MvpRoom[];
	labels: MvpLabel[];
	pois: MvpPoi[];
	nodes: MvpNode[];
	edges: MvpEdge[];
};

export type ParsedNavigationMvpMap =
	| { ok: true; data: NavigationMvpMapV1 }
	| { ok: false; error: string };

export type MvpStairLink = {
	id: string;
	x: number;
	y: number;
	fromFloor: number;
	toFloor: number;
};

export type BundleFloorEntry = {
	index: number;
	level: string;
	verticalRange: [number, number];
	mapPath?: string;
	map: NavigationMvpMapV1;
};

export type NavigationMvpBundleV1 = {
	schemaVersion: typeof NAVIGATION_MVP_SCHEMA_VERSION;
	name: string;
	floors: BundleFloorEntry[];
	stairs: MvpStairLink[];
};

export type ParsedNavigationMvpBundle =
	| { ok: true; data: NavigationMvpBundleV1 }
	| { ok: false; error: string };
