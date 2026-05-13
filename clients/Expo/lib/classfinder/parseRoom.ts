/** Parse free text for a building–room token (SOEN390-style). */

export function tryParseCampusRoom(raw: string): string | null {
	const value = raw.trim().replace(/\s+/g, " ");
	if (!value) {
		return null;
	}
	const m = value.match(/^([A-Za-z]{1,4})\s*[-]?\s*([A-Za-z]?\d[\w.\-]*)$/i);
	if (!m) {
		return null;
	}
	return `${m[1]!.toUpperCase()}-${m[2]!.toUpperCase()}`;
}

export function scanForRoom(value: string): string | null {
	const v = value.trim();
	for (let i = 0; i < v.length; i++) {
		const parsed = tryParseCampusRoom(v.slice(i));
		if (parsed) {
			return parsed;
		}
	}
	return null;
}
