import { migrateLegacyNavigationJson } from "./migrate";
import { validateCampusMapV1, validateIndoorBuildingV1 } from "./validate";
import type { CampusMapV1, IndoorBuildingV1, ParsedBuilding, ParsedCampus } from "./types";

export function parseBuildingJson(rawText: string): ParsedBuilding {
	let parsed: unknown;
	try {
		parsed = JSON.parse(rawText) as unknown;
	} catch {
		return { ok: false, error: "File is not valid JSON." };
	}

	const v1 = validateIndoorBuildingV1(parsed);
	if (v1.ok) {
		return v1;
	}

	const migrated = migrateLegacyNavigationJson(parsed);
	if (migrated) {
		const again = validateIndoorBuildingV1(migrated);
		if (again.ok) {
			return again;
		}
		return { ok: false, error: again.error };
	}

	return { ok: false, error: v1.ok ? "Unknown error" : v1.error };
}

export function parseCampusJson(rawText: string): ParsedCampus {
	let parsed: unknown;
	try {
		parsed = JSON.parse(rawText) as unknown;
	} catch {
		return { ok: false, error: "Campus file is not valid JSON." };
	}
	return validateCampusMapV1(parsed);
}

export function serializeBuilding(data: IndoorBuildingV1): string {
	return JSON.stringify(data, null, 2);
}

export function serializeCampus(data: CampusMapV1): string {
	return JSON.stringify(data, null, 2);
}
