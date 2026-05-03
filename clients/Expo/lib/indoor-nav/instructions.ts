import { distance } from "./graph";
import type { GraphNode, IndoorLocation, Vec2 } from "./types";

function angleBetween(ax: number, ay: number, bx: number, by: number): number {
	const la = Math.hypot(ax, ay);
	const lb = Math.hypot(bx, by);
	if (la < 1e-6 || lb < 1e-6) {
		return 0;
	}
	const dot = (ax * bx + ay * by) / (la * lb);
	return Math.acos(Math.max(-1, Math.min(1, dot)));
}

function crossZ(ax: number, ay: number, bx: number, by: number): number {
	return ax * by - ay * bx;
}

/** Bearing from p0 -> p1 in degrees, 0 = east, 90 = north (y up). */
function bearing(p0: Vec2, p1: Vec2): number {
	return (Math.atan2(p1.y - p0.y, p1.x - p0.x) * 180) / Math.PI;
}

function turnHint(prev: Vec2, cur: Vec2, next: Vec2): string {
	const v1 = { x: cur.x - prev.x, y: cur.y - prev.y };
	const v2 = { x: next.x - cur.x, y: next.y - cur.y };
	const deg = (angleBetween(v1.x, v1.y, v2.x, v2.y) * 180) / Math.PI;
	const c = crossZ(v1.x, v1.y, v2.x, v2.y);
	if (deg < 25) {
		return "Continue straight.";
	}
	if (c > 0) {
		return deg > 120 ? "Turn around." : "Turn left.";
	}
	return deg > 120 ? "Turn around." : "Turn right.";
}

export function buildIndoorInstructions(
	pathNodeIds: string[],
	nodesById: Map<string, GraphNode>,
	goalLocation: IndoorLocation | undefined,
): string[] {
	if (pathNodeIds.length === 0) {
		return [];
	}
	if (pathNodeIds.length === 1) {
		const n = nodesById.get(pathNodeIds[0]);
		const label = n?.label ?? n?.id ?? "checkpoint";
		return [`You are at ${label}.`];
	}

	const steps: string[] = [];
	for (let i = 0; i < pathNodeIds.length - 1; i++) {
		const a = nodesById.get(pathNodeIds[i]);
		const b = nodesById.get(pathNodeIds[i + 1]);
		if (!a || !b) {
			continue;
		}
		if (a.floor !== b.floor) {
			steps.push(
				`Change floor (was ${a.floor}, now ${b.floor}). Use stairs or elevator, then continue.`,
			);
			continue;
		}
		const dist = distance(a.position, b.position);
		const toward = b.label ?? b.id;
		if (i === 0) {
			steps.push(`Head toward ${toward} (${dist.toFixed(0)} m along the map).`);
		} else {
			const prev = nodesById.get(pathNodeIds[i - 1]);
			if (prev) {
				steps.push(turnHint(prev.position, a.position, b.position));
			}
			steps.push(`Continue to ${toward} (${dist.toFixed(0)} m).`);
		}
	}

	const lastId = pathNodeIds[pathNodeIds.length - 1];
	const last = nodesById.get(lastId);
	if (goalLocation) {
		steps.push(`Arrived near ${goalLocation.name}.`);
	} else if (last?.label) {
		steps.push(`Arrived at ${last.label}.`);
	} else {
		steps.push("You have reached the destination area.");
	}

	return steps;
}

/** Next bearing in degrees for arrow UI: direction from current to next node. */
export function bearingToNext(
	currentId: string,
	nextId: string | undefined,
	nodesById: Map<string, GraphNode>,
): number | null {
	if (!nextId) {
		return null;
	}
	const a = nodesById.get(currentId);
	const b = nodesById.get(nextId);
	if (!a || !b) {
		return null;
	}
	return bearing(a.position, b.position);
}
