import type { NavigationMvpBundleV1, NavigationMvpMapV1 } from "./types";
import { parseBuildingBundle, parseNavigationMvpMap } from "./validate";

/**
 * Megaprompt-style entry: load building map JSON (bundled asset or fetched URL).
 */
export async function loadBuildingMap(source: unknown): Promise<NavigationMvpMapV1> {
	const parsed = parseNavigationMvpMap(source);
	if (!parsed.ok) {
		throw new Error(parsed.error);
	}
	return parsed.data;
}

/** Load multi-floor bundle (`uni-bundle.json`). */
export async function loadBuildingBundle(source: unknown): Promise<NavigationMvpBundleV1> {
	const parsed = parseBuildingBundle(source);
	if (!parsed.ok) {
		throw new Error(parsed.error);
	}
	return parsed.data;
}

export function getFloorMap(bundle: NavigationMvpBundleV1, floorIndex: number): NavigationMvpMapV1 {
	const f = bundle.floors.find((fl) => fl.index === floorIndex);
	if (!f) {
		throw new Error(`Unknown floor index ${floorIndex}`);
	}
	return f.map;
}

export function mapsByFloorIndex(bundle: NavigationMvpBundleV1): Map<number, NavigationMvpMapV1> {
	const m = new Map<number, NavigationMvpMapV1>();
	for (const fl of bundle.floors) {
		m.set(fl.index, fl.map);
	}
	return m;
}
