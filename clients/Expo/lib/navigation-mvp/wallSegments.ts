import type { MvpWall } from "./types";

const EPS = 1e-9;

/**
 * True iff closed segments AB and CD intersect (including endpoints).
 * Parallel non-overlapping segments return false.
 */
export function segmentsIntersect(
	ax: number,
	ay: number,
	bx: number,
	by: number,
	cx: number,
	cy: number,
	dx: number,
	dy: number,
): boolean {
	const bxax = bx - ax;
	const byay = by - ay;
	const dxcx = dx - cx;
	const dycy = dy - cy;
	const denom = bxax * dycy - byay * dxcx;
	if (Math.abs(denom) < EPS) {
		return false;
	}
	const cxax = cx - ax;
	const cyay = cy - ay;
	const t = (cxax * dycy - cyay * dxcx) / denom;
	const u = (cxax * byay - cyay * bxax) / denom;
	return t >= -1e-6 && t <= 1 + 1e-6 && u >= -1e-6 && u <= 1 + 1e-6;
}

export type WallSeg = { x1: number; y1: number; x2: number; y2: number };

/** Flatten wall polylines into 2-point segments (map units). */
export function wallSegmentsFromMap(walls: MvpWall[]): WallSeg[] {
	const out: WallSeg[] = [];
	for (const w of walls) {
		const pts = w.points;
		for (let i = 0; i < pts.length - 1; i++) {
			const p = pts[i]!;
			const q = pts[i + 1]!;
			const dx = q.x - p.x;
			const dy = q.y - p.y;
			if (dx * dx + dy * dy < 1e-12) {
				continue;
			}
			out.push({ x1: p.x, y1: p.y, x2: q.x, y2: q.y });
		}
	}
	return out;
}

export function segmentCrossesWallSegments(
	ax: number,
	ay: number,
	bx: number,
	by: number,
	wallSegs: WallSeg[],
): boolean {
	for (const s of wallSegs) {
		if (segmentsIntersect(ax, ay, bx, by, s.x1, s.y1, s.x2, s.y2)) {
			return true;
		}
	}
	return false;
}
