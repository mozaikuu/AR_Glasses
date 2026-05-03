import type { CampusMapV1, IndoorBuildingV1 } from "./types";
import defaultBuilding from "./data/default-building.json";
import sampleCampus from "./data/campus.sample.json";
import { validateCampusMapV1, validateIndoorBuildingV1 } from "./validate";

const defaultParsed = validateIndoorBuildingV1(defaultBuilding as unknown);
if (!defaultParsed.ok) {
	throw new Error(`Bundled default building invalid: ${defaultParsed.error}`);
}

const campusParsed = validateCampusMapV1(sampleCampus as unknown);
if (!campusParsed.ok) {
	throw new Error(`Bundled campus invalid: ${campusParsed.error}`);
}

export const BUNDLED_DEFAULT_BUILDING: IndoorBuildingV1 = defaultParsed.data;
export const BUNDLED_SAMPLE_CAMPUS: CampusMapV1 = campusParsed.data;

/** Resolve indoor dataset for a campus building reference. MVP: only `default`. */
export function resolveIndoorBundle(bundleId: string): IndoorBuildingV1 | null {
	if (bundleId === "default") {
		return BUNDLED_DEFAULT_BUILDING;
	}
	return null;
}
