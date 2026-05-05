import { distance } from "./graph";
import type { IndoorLocation, LectureSlot, Vec2 } from "./types";

const DAY_NAMES = [
	"Sunday",
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
] as const;

export function getTodayEnglishName(date = new Date()): string {
	return DAY_NAMES[date.getDay()] ?? "Sunday";
}

export function lecturesForToday(lectures: LectureSlot[] | undefined, date = new Date()): LectureSlot[] {
	if (!lectures?.length) {
		return [];
	}
	const today = getTodayEnglishName(date);
	return lectures.filter((l) => l.day === today);
}

function isProximityTarget(loc: IndoorLocation): boolean {
	if (loc.mapKind === "garden") {
		return false;
	}
	if (loc.isNavObstacle) {
		return false;
	}
	return true;
}

/** Rooms whose center is within radius of `position` (map units). */
export function findRoomsNear(
	locations: IndoorLocation[],
	position: Vec2,
): IndoorLocation[] {
	const hits: IndoorLocation[] = [];
	for (const loc of locations) {
		if (!isProximityTarget(loc)) {
			continue;
		}
		const r = typeof loc.proximityRadius === "number" ? loc.proximityRadius : 2;
		const d = distance(position, loc.coordinates);
		if (d <= r) {
			hits.push(loc);
		}
	}
	return hits.sort((a, b) => {
		const da = distance(position, a.coordinates);
		const db = distance(position, b.coordinates);
		return da - db;
	});
}
