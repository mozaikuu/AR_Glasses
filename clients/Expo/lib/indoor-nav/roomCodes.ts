/**
 * Room notation: `B-F-R` e.g. `2-1-46` = building 2, floor 1, room 46.
 */

export type ParsedRoomCode = {
	buildingId: string;
	floor: number;
	room: string;
};

const CODE_RE = /^(\d+)-(\d+)-(.+)$/;

export function parseRoomCode(code: string): ParsedRoomCode | null {
	const t = code.trim();
	const m = t.match(CODE_RE);
	if (!m) {
		return null;
	}
	const buildingId = m[1];
	const floor = Number.parseInt(m[2], 10);
	if (!Number.isFinite(floor)) {
		return null;
	}
	const room = m[3].trim();
	if (!room) {
		return null;
	}
	return { buildingId, floor, room };
}

export function formatRoomCode(buildingId: string, floor: number, room: string): string {
	return `${buildingId}-${floor}-${room}`;
}

/** Suggest location id from room code (safe for JSON ids). */
export function idFromRoomCode(code: string): string {
	const p = parseRoomCode(code);
	if (!p) {
		return `loc_${code.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
	}
	return `b${p.buildingId}_f${p.floor}_r${p.room.replace(/\s+/g, "_")}`;
}
