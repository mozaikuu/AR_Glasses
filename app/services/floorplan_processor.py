"""
LiDAR / point cloud / textured mesh → multi-floor 2D floorplan JSON (MVP).

Uses trimesh + numpy + OpenCV. Optional matplotlib for --preview PNGs.
"""

from __future__ import annotations

import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


# Mesh section: shorter segments than 0.15 m are often real geometry on low-poly GLBs; 0.06 m ≈ hundreds of walls for Uni_textured.
DEFAULT_MESH_MIN_SEGMENT_M = 0.06


def _require_trimesh():
	try:
		import trimesh  # type: ignore

		return trimesh
	except Exception as exc:  # pragma: no cover
		raise ImportError(
			"trimesh is required. Install with: pip install -r app/requirements-navigation-mvp.txt"
		) from exc


def _require_cv2():
	try:
		import cv2  # type: ignore

		return cv2
	except Exception as exc:  # pragma: no cover
		raise ImportError(
			"opencv-python-headless is required. "
			"Install with: pip install -r app/requirements-navigation-mvp.txt"
		) from exc


def _axis_index(vertical: str) -> int:
	v = vertical.lower()
	if v == "x":
		return 0
	if v == "y":
		return 1
	if v == "z":
		return 2
	raise ValueError(f"vertical_axis must be x, y, or z; got {vertical!r}")


def _plane_origin(vertical_axis: str, height: float) -> np.ndarray:
	o = np.zeros(3, dtype=np.float64)
	o[_axis_index(vertical_axis)] = float(height)
	return o


def _plane_normal(vertical_axis: str) -> np.ndarray:
	n = np.zeros(3, dtype=np.float64)
	n[_axis_index(vertical_axis)] = 1.0
	return n


def _load_mesh_combined(path: Path) -> Any:
	"""Load GLB/GLTF/OBJ/PLY as a single Trimesh (Scene concatenated)."""
	trimesh = _require_trimesh()
	loaded = trimesh.load(str(path), process=False)
	if isinstance(loaded, trimesh.Scene):
		if len(loaded.geometry) == 0:
			raise ValueError("Empty scene.")
		parts = []
		for g in loaded.geometry.values():
			if isinstance(g, trimesh.Trimesh):
				parts.append(g)
		if not parts:
			raise ValueError("Scene contains no triangle meshes.")
		return trimesh.util.concatenate(parts)
	if isinstance(loaded, trimesh.Trimesh):
		return loaded
	raise ValueError(f"Expected mesh or scene, got {type(loaded)}")


def _try_load_mesh_with_faces(path: Path) -> Optional[Any]:
	try:
		m = _load_mesh_combined(path)
	except Exception:
		return None
	if len(getattr(m, "faces", [])) == 0:
		return None
	return m


def _extract_wall_faces(mesh: Any, vertical_axis: str, normal_threshold: float = 0.3) -> Any:
	"""Keep near-vertical faces (|n_axis| small) — floors/ceilings/stairs mostly filtered out."""
	trimesh = _require_trimesh()
	vi = _axis_index(vertical_axis)
	n_abs = np.abs(np.asarray(mesh.face_normals)[:, vi])
	wall_mask = n_abs < float(normal_threshold)
	faces = np.asarray(mesh.faces)[wall_mask]
	if len(faces) == 0:
		warnings.warn("No wall-like faces after normal filter; using full mesh for section.", UserWarning)
		faces = np.asarray(mesh.faces)
	return trimesh.Trimesh(vertices=np.asarray(mesh.vertices), faces=faces, process=False)


def _extract_horizontal_faces(mesh: Any, vertical_axis: str, threshold: float = 0.7) -> Any:
	vi = _axis_index(vertical_axis)
	n_abs = np.abs(np.asarray(mesh.face_normals)[:, vi])
	mask = n_abs >= float(threshold)
	faces = np.asarray(mesh.faces)[mask]
	return _require_trimesh().Trimesh(vertices=np.asarray(mesh.vertices), faces=faces, process=False)


def _walls_from_mesh_section(
	wall_mesh: Any,
	vertical_axis: str,
	slice_height: float,
	*,
	min_segment_m: float = DEFAULT_MESH_MIN_SEGMENT_M,
	max_walls: int = 25_000,
) -> Tuple[List[Dict[str, Any]], Tuple[float, float, float, float]]:
	"""Cross-section wall mesh at slice_height → 2-point wall segments in plan (to_2D) coordinates."""
	origin = _plane_origin(vertical_axis, slice_height)
	normal = _plane_normal(vertical_axis)
	section = wall_mesh.section(plane_origin=origin, plane_normal=normal)
	if section is None:
		return [], (0.0, 0.0, 1.0, 800)
	path2d, _ = section.to_2D()
	walls: List[Dict[str, Any]] = []
	wi = 0
	for entity in path2d.entities:
		pts = path2d.vertices[entity.points]
		if len(pts) < 2:
			continue
		for i in range(len(pts) - 1):
			x1, y1 = float(pts[i][0]), float(pts[i][1])
			x2, y2 = float(pts[i + 1][0]), float(pts[i + 1][1])
			if math.hypot(x2 - x1, y2 - y1) < min_segment_m:
				continue
			walls.append({"id": f"w_{wi}", "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}]})
			wi += 1
			if wi >= max_walls:
				break
		if wi >= max_walls:
			break
		if getattr(entity, "closed", False) and len(pts) > 2:
			x1, y1 = float(pts[-1][0]), float(pts[-1][1])
			x2, y2 = float(pts[0][0]), float(pts[0][1])
			if math.hypot(x2 - x1, y2 - y1) >= min_segment_m and wi < max_walls:
				walls.append({"id": f"w_{wi}", "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}]})
				wi += 1
		if wi >= max_walls:
			break
	if not walls:
		return [], (0.0, 0.0, 1.0, 800)
	xs: List[float] = []
	ys: List[float] = []
	for w in walls:
		for p in w["points"]:
			xs.append(float(p["x"]))
			ys.append(float(p["y"]))
	margin = 1.0
	min_x, max_x = min(xs) - margin, max(xs) + margin
	min_y, max_y = min(ys) - margin, max(ys) + margin
	pixels = 800
	scale = pixels / max(max_x - min_x, max_y - min_y, 1e-6)
	return walls, (float(min_x), float(min_y), float(scale), int(pixels))


def _rasterize_walls_grid(
	walls: List[Dict[str, Any]],
	*,
	resolution_m: float,
	margin_m: float = 1.0,
	pad_px: int = 10,
	line_thickness: int = 2,
) -> Tuple[np.ndarray, Tuple[float, float]]:
	"""Binary grid 255 = wall, 0 = empty. Returns (grid, (min_x, min_y) world origin of pixel (0,0))."""
	cv2 = _require_cv2()
	xs: List[float] = []
	ys: List[float] = []
	for w in walls:
		for p in w["points"]:
			xs.append(float(p["x"]))
			ys.append(float(p["y"]))
	if not xs:
		return np.zeros((10, 10), dtype=np.uint8), (0.0, 0.0)
	min_x, max_x = min(xs) - margin_m, max(xs) + margin_m
	min_y, max_y = min(ys) - margin_m, max(ys) + margin_m
	w_m = max_x - min_x
	h_m = max_y - min_y
	W = int(w_m / resolution_m) + 2 * pad_px
	H = int(h_m / resolution_m) + 2 * pad_px
	W = max(W, 8)
	H = max(H, 8)
	grid = np.zeros((H, W), dtype=np.uint8)

	def w2g(x: float, y: float) -> Tuple[int, int]:
		ix = int((x - min_x) / resolution_m) + pad_px
		iy = int((y - min_y) / resolution_m) + pad_px
		return max(0, min(W - 1, ix)), max(0, min(H - 1, iy))

	for w in walls:
		pts = w["points"]
		if len(pts) < 2:
			continue
		for i in range(len(pts) - 1):
			a = w2g(float(pts[i]["x"]), float(pts[i]["y"]))
			b = w2g(float(pts[i + 1]["x"]), float(pts[i + 1]["y"]))
			cv2.line(grid, a, b, 255, line_thickness)
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
	grid = cv2.dilate(grid, kernel, iterations=1)
	return grid, (float(min_x), float(min_y))


def detect_stair_shafts_mesh(
	mesh: Any,
	vertical_axis: str,
	floor_bands: Sequence[FloorBand],
	*,
	horizontal_thresh: float = 0.7,
	cell_m: float = 0.5,
) -> List[Dict[str, Any]]:
	"""Horizontal faces whose centroid lies in the vertical gap between consecutive floor bands → stair links."""
	if len(floor_bands) < 2:
		return []
	vi = _axis_index(vertical_axis)
	ai = (vi + 1) % 3
	bi = (vi + 2) % 3
	sorted_bands = sorted(floor_bands, key=lambda b: b.v_lo)
	horiz_mesh = _extract_horizontal_faces(mesh, vertical_axis, horizontal_thresh)
	verts = np.asarray(horiz_mesh.vertices)
	faces = np.asarray(horiz_mesh.faces)
	if len(faces) == 0:
		return []
	centroids = verts[faces].mean(axis=1)

	cv2 = _require_cv2()
	stairs: List[Dict[str, Any]] = []
	sid = 0

	for i in range(len(sorted_bands) - 1):
		lo_b = sorted_bands[i]
		hi_b = sorted_bands[i + 1]
		gap_lo = float(lo_b.v_hi)
		gap_hi = float(hi_b.v_lo)
		if gap_hi < gap_lo:
			gap_lo, gap_hi = gap_hi, gap_lo
		if gap_hi - gap_lo < 0.05:
			gap_mid = (lo_b.v_hi + hi_b.v_lo) * 0.5
			gap_lo, gap_hi = gap_mid - 0.25, gap_mid + 0.25

		xy_pts: List[Tuple[float, float]] = []
		for fi in range(len(faces)):
			vc = float(centroids[fi, vi])
			if gap_lo - 0.08 <= vc <= gap_hi + 0.08:
				xy_pts.append((float(centroids[fi, ai]), float(centroids[fi, bi])))
		if len(xy_pts) < 5:
			continue
		xs = np.array([p[0] for p in xy_pts])
		ys = np.array([p[1] for p in xy_pts])
		xmin, xmax = float(xs.min()), float(xs.max())
		ymin, ymax = float(ys.min()), float(ys.max())
		nx = max(1, int(math.ceil((xmax - xmin) / cell_m)))
		ny = max(1, int(math.ceil((ymax - ymin) / cell_m)))
		ix = np.clip(((xs - xmin) / (xmax - xmin + 1e-9) * (nx - 1)).astype(np.int32), 0, nx - 1)
		iy = np.clip(((ys - ymin) / (ymax - ymin + 1e-9) * (ny - 1)).astype(np.int32), 0, ny - 1)
		grid = np.zeros((ny, nx), dtype=np.uint8)
		for j in range(len(xy_pts)):
			grid[int(iy[j]), int(ix[j])] = 255
		num, labels, stats, _ = cv2.connectedComponentsWithStats(grid, connectivity=8)
		for lab in range(1, num):
			area = int(stats[lab, cv2.CC_STAT_AREA])
			if area < 2:
				continue
			cx = stats[lab, cv2.CC_STAT_LEFT] + stats[lab, cv2.CC_STAT_WIDTH] * 0.5
			cy = stats[lab, cv2.CC_STAT_TOP] + stats[lab, cv2.CC_STAT_HEIGHT] * 0.5
			wx = xmin + (cx / max(nx - 1, 1)) * (xmax - xmin)
			wy = ymin + (cy / max(ny - 1, 1)) * (ymax - ymin)
			stairs.append(
				{
					"id": f"st_{sid}",
					"x": float(wx),
					"y": float(wy),
					"fromFloor": int(lo_b.index),
					"toFloor": int(hi_b.index),
				}
			)
			sid += 1
	return stairs


def load_scan_points_array(path: Path, *, mesh_sample_points: int = 400_000) -> np.ndarray:
	trimesh = _require_trimesh()
	sfx = path.suffix.lower()
	loaded = trimesh.load(str(path), process=False)

	if isinstance(loaded, trimesh.Scene):
		if len(loaded.geometry) == 0:
			raise ValueError("Empty scene.")
		parts = []
		for g in loaded.geometry.values():
			if isinstance(g, trimesh.Trimesh):
				parts.append(g)
		if not parts:
			raise ValueError("Scene contains no triangle meshes.")
		mesh = trimesh.util.concatenate(parts)
	elif isinstance(loaded, trimesh.Trimesh):
		mesh = loaded
	elif isinstance(loaded, trimesh.PointCloud):
		pts = np.asarray(loaded.vertices, dtype=np.float64)
		if pts.size == 0:
			raise ValueError("Empty point cloud.")
		return pts
	else:
		raise ValueError(f"Unsupported trimesh type: {type(loaded)}")

	if sfx in (".glb", ".gltf") or len(mesh.faces) > 0:
		if len(mesh.vertices) == 0:
			raise ValueError("Empty mesh.")
		np.random.seed(42)
		pts, _ = trimesh.sample.sample_surface(mesh, int(mesh_sample_points))
		return np.asarray(pts, dtype=np.float64)

	pts = np.asarray(mesh.vertices, dtype=np.float64)
	if pts.size == 0:
		raise ValueError("Empty geometry.")
	return pts


def voxel_downsample(points: np.ndarray, voxel_size: float) -> np.ndarray:
	if len(points) == 0:
		return points
	q = np.floor(points / voxel_size).astype(np.int64)
	_, unique_idx = np.unique(q, axis=0, return_index=True)
	return points[unique_idx]


def _bbox_vertical_axis_np(points: np.ndarray) -> str:
	ext = points.max(axis=0) - points.min(axis=0)
	i = int(np.argmin(ext))
	return ("x", "y", "z")[i]


def _find_peaks_1d(hist: np.ndarray, min_height: float, min_distance: int) -> np.ndarray:
	"""Simple peak finder (no scipy required)."""
	h = np.asarray(hist, dtype=np.float64)
	peaks: List[int] = []
	for i in range(1, len(h) - 1):
		if h[i] < min_height:
			continue
		if h[i] < h[i - 1] or h[i] < h[i + 1]:
			continue
		if h[i] == h[i - 1] and h[i] == h[i + 1]:
			continue
		if peaks and i - peaks[-1] < min_distance:
			if h[i] > h[peaks[-1]]:
				peaks[-1] = i
			continue
		peaks.append(i)
	return np.array(peaks, dtype=np.int32)


@dataclass
class FloorBand:
	"""One vertical occupancy band; v_ref is histogram slab centre for mesh.section."""

	index: int
	name: str
	v_lo: float
	v_hi: float
	v_ref: float = 0.0


def detect_floor_bands(
	points: np.ndarray,
	vertical_axis: str,
	*,
	bin_width: float = 0.1,
	floor_band_half_height: float = 1.5,
	min_mass_frac: float = 0.02,
	min_peak_distance_bins: int = 8,
) -> List[FloorBand]:
	"""
	1D vertical histogram → peaks = floor slab centers.
	Each band is [peak - floor_band_half_height, peak + floor_band_half_height], merged if overlapping.
	"""
	vi = _axis_index(vertical_axis)
	v = points[:, vi]
	vmin, vmax = float(v.min()), float(v.max())
	if vmax - vmin < 0.5:
		mid = (vmin + vmax) * 0.5
		return [FloorBand(0, "Ground", vmin, vmax, mid)]

	edges = np.arange(vmin, vmax + bin_width, bin_width)
	hist, _ = np.histogram(v, bins=edges)
	total = float(np.sum(hist)) + 1e-9
	min_h = max(np.max(hist) * 0.06, total * min_mass_frac / max(len(hist), 1))
	peaks = _find_peaks_1d(hist, min_height=min_h, min_distance=min_peak_distance_bins)

	if len(peaks) == 0:
		mid = (vmin + vmax) * 0.5
		return [FloorBand(0, "Ground", vmin, vmax, mid)]

	centers = edges[peaks] + bin_width * 0.5
	items: List[Tuple[float, float, float]] = [
		(float(c - floor_band_half_height), float(c + floor_band_half_height), float(c)) for c in centers
	]
	items.sort(key=lambda t: t[0])
	merged_rows: List[List[Any]] = []
	for lo, hi, pc in items:
		if not merged_rows or lo > merged_rows[-1][1] + bin_width * 2:
			merged_rows.append([lo, hi, [pc]])
		else:
			merged_rows[-1][1] = max(float(merged_rows[-1][1]), hi)
			merged_rows[-1][2].append(pc)

	out: List[FloorBand] = []
	for i, row in enumerate(merged_rows):
		lo, hi, pcs = float(row[0]), float(row[1]), row[2]
		v_ref = float(np.mean(np.asarray(pcs, dtype=np.float64)))
		name = "Ground" if i == 0 else f"Level {i}"
		out.append(FloorBand(i, name, lo, hi, v_ref))
	return out


def _slice_band_to_planar_xy(
	points: np.ndarray,
	vertical_axis: str,
	v_lo: float,
	v_hi: float,
	voxel_size: float,
) -> np.ndarray:
	"""All points in vertical band, projected to 2D (horizontal plane)."""
	vi = _axis_index(vertical_axis)
	ai = (vi + 1) % 3
	bi = (vi + 2) % 3
	mask = (points[:, vi] >= v_lo) & (points[:, vi] <= v_hi)
	sel = points[mask]
	if len(sel) == 0:
		return np.zeros((0, 2), dtype=np.float64)
	down = voxel_downsample(sel, voxel_size)
	return np.column_stack([down[:, ai], down[:, bi]])


def _slice_at_height_to_planar_xy(
	points: np.ndarray,
	vertical_axis: str,
	slice_center: float,
	thickness: float,
	voxel_size: float,
) -> np.ndarray:
	vi = _axis_index(vertical_axis)
	ai = (vi + 1) % 3
	bi = (vi + 2) % 3
	down = voxel_downsample(points, voxel_size)
	half = thickness / 2.0
	lo, hi = slice_center - half, slice_center + half
	mask = (down[:, vi] >= lo) & (down[:, vi] <= hi)
	sel = down[mask]
	if len(sel) == 0:
		return np.zeros((0, 2), dtype=np.float64)
	return np.column_stack([sel[:, ai], sel[:, bi]])


def _occupancy_grid_np(
	xy: np.ndarray,
	pixels: int = 800,
	margin: float = 1.0,
	*,
	sparse: bool = False,
	return_raw: bool = False,
) -> Tuple[Any, Tuple[float, float, float, float], Any]:
	cv2 = _require_cv2()
	if len(xy) == 0:
		raise ValueError("No points in horizontal slice.")
	min_x = float(xy[:, 0].min() - margin)
	max_x = float(xy[:, 0].max() + margin)
	min_y = float(xy[:, 1].min() - margin)
	max_y = float(xy[:, 1].max() + margin)
	w = max_x - min_x
	h = max_y - min_y
	scale = pixels / max(w, h, 1e-3)
	img = (255 * np.ones((pixels, pixels), dtype=np.uint8)).astype(np.uint8)
	ix = ((xy[:, 0] - min_x) * scale).astype(np.int32)
	iy = ((xy[:, 1] - min_y) * scale).astype(np.int32)
	ix = np.clip(ix, 0, pixels - 1)
	iy = np.clip(iy, 0, pixels - 1)
	img[iy, ix] = 0
	raw = img.copy()
	kernel = np.ones((7, 7), dtype=np.uint8) if sparse else np.ones((3, 3), dtype=np.uint8)
	iters = 2 if sparse else 1
	img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iters)
	thick = np.ones((5, 5), dtype=np.uint8)
	inv = 255 - img
	inv = cv2.dilate(inv, thick, iterations=2)
	img = 255 - inv
	bounds = (min_x, min_y, scale, pixels)
	return img, bounds, raw


def _segment_length_world(
	x1: float,
	y1: float,
	x2: float,
	y2: float,
	scale: float,
) -> float:
	return math.hypot((x2 - x1) / scale, (y2 - y1) / scale)


def _hough_walls_tuned(
	img,
	bounds: Tuple[float, float, float, float],
	*,
	min_len_world: float = 0.5,
	max_segments: int = 400,
) -> List[Dict[str, Any]]:
	cv2 = _require_cv2()
	min_x, min_y, scale, pixels = bounds
	edges = cv2.Canny(img, 40, 120)
	if int(np.count_nonzero(edges)) < 50:
		edges = cv2.Canny(255 - img, 40, 120)
	min_len_px = max(8, int(pixels / 80))
	lines = cv2.HoughLinesP(
		edges,
		1,
		math.pi / 360.0,
		threshold=25,
		minLineLength=min_len_px,
		maxLineGap=18,
	)
	walls: List[Dict[str, Any]] = []
	if lines is None:
		return walls
	for idx, ln in enumerate(lines[: max_segments * 2]):
		x1, y1, x2, y2 = ln[0]
		wx1 = min_x + x1 / scale
		wy1 = min_y + y1 / scale
		wx2 = min_x + x2 / scale
		wy2 = min_y + y2 / scale
		if _segment_length_world(wx1, wy1, wx2, wy2, scale) < min_len_world:
			continue
		walls.append({"id": f"w_{idx}", "points": [{"x": wx1, "y": wy1}, {"x": wx2, "y": wy2}]})
		if len(walls) >= max_segments:
			break
	return walls


def _angle(dx: float, dy: float) -> float:
	return math.degrees(math.atan2(dy, dx))


def _merge_collinear_segments(
	walls: List[Dict[str, Any]],
	*,
	snap_m: float,
	angle_tol_deg: float,
) -> List[Dict[str, Any]]:
	if len(walls) < 2:
		return walls
	segments: List[Tuple[Tuple[float, float], Tuple[float, float], str]] = []
	for w in walls:
		pts = w["points"]
		if len(pts) < 2:
			continue
		p0, p1 = pts[0], pts[1]
		segments.append(((float(p0["x"]), float(p0["y"])), (float(p1["x"]), float(p1["y"])), w["id"]))
	merged: List[Tuple[Tuple[float, float], Tuple[float, float], str]] = []
	for a, b, wid in segments:
		if not merged:
			merged.append((a, b, wid))
			continue
		ca, cb, cid = merged[-1]
		ta = _angle(b[0] - a[0], b[1] - a[1])
		tb = _angle(cb[0] - ca[0], cb[1] - ca[1])
		if abs(((ta - tb + 180) % 360) - 180) > angle_tol_deg:
			merged.append((a, b, wid))
			continue
		# try extend if endpoints close
		d1 = math.hypot(a[0] - cb[0], a[1] - cb[1])
		d2 = math.hypot(b[0] - ca[0], b[1] - ca[1])
		if d1 < snap_m:
			merged[-1] = (ca, b, cid)
		elif d2 < snap_m:
			merged[-1] = (ca, b, cid)
		else:
			merged.append((a, b, wid))
	out: List[Dict[str, Any]] = []
	for i, (p0, p1, _) in enumerate(merged):
		out.append({"id": f"w_m_{i}", "points": [{"x": p0[0], "y": p0[1]}, {"x": p1[0], "y": p1[1]}]})
	return out


def detect_stair_shafts(
	points: np.ndarray,
	vertical_axis: str,
	floor_bands: Sequence[FloorBand],
	*,
	cell_m: float = 0.5,
	extent_ratio: float = 1.6,
) -> List[Dict[str, Any]]:
	"""
	XY cells with large vertical extent (column through multiple slabs) → stair shafts.
	Emits one manifest entry per connected component (pairwise consecutive floors touched).
	"""
	if len(floor_bands) < 2:
		return []
	vi = _axis_index(vertical_axis)
	ai = (vi + 1) % 3
	bi = (vi + 2) % 3
	floor_height = float(np.median([b.v_hi - b.v_lo for b in floor_bands])) or 3.0
	thresh = floor_height * extent_ratio

	xs = points[:, ai]
	ys = points[:, bi]
	xmin, xmax = float(xs.min()), float(xs.max())
	ymin, ymax = float(ys.min()), float(ys.max())
	nx = max(1, int(math.ceil((xmax - xmin) / cell_m)))
	ny = max(1, int(math.ceil((ymax - ymin) / cell_m)))
	ix = np.clip(((xs - xmin) / (xmax - xmin + 1e-9) * (nx - 1)).astype(np.int32), 0, nx - 1)
	iy = np.clip(((ys - ymin) / (ymax - ymin + 1e-9) * (ny - 1)).astype(np.int32), 0, ny - 1)

	vmin_g = np.full((ny, nx), np.inf, dtype=np.float64)
	vmax_g = np.full((ny, nx), -np.inf, dtype=np.float64)
	for i in range(len(points)):
		ixx, iyy, v = int(ix[i]), int(iy[i]), float(points[i, vi])
		if v < vmin_g[iyy, ixx]:
			vmin_g[iyy, ixx] = v
		if v > vmax_g[iyy, ixx]:
			vmax_g[iyy, ixx] = v
	ext_grid = vmax_g - vmin_g
	count_grid = np.zeros((ny, nx), dtype=np.int32)
	for i in range(len(points)):
		count_grid[int(iy[i]), int(ix[i])] += 1

	mask = (ext_grid >= thresh) & (count_grid >= 5)
	mask_u8 = (mask.astype(np.uint8) * 255)
	cv2 = _require_cv2()
	num, labels, stats, _ = cv2.connectedComponentsWithStats(mask_u8, connectivity=8)
	stairs: List[Dict[str, Any]] = []
	sid = 0
	for lab in range(1, num):
		area = int(stats[lab, cv2.CC_STAT_AREA])
		if area < 3:
			continue
		cx = stats[lab, cv2.CC_STAT_LEFT] + stats[lab, cv2.CC_STAT_WIDTH] * 0.5
		cy = stats[lab, cv2.CC_STAT_TOP] + stats[lab, cv2.CC_STAT_HEIGHT] * 0.5
		wx = xmin + (cx / max(nx - 1, 1)) * (xmax - xmin)
		wy = ymin + (cy / max(ny - 1, 1)) * (ymax - ymin)

		v_samples: List[float] = []
		for i in range(len(points)):
			if labels[int(iy[i]), int(ix[i])] == lab:
				v_samples.append(float(points[i, vi]))
		if len(v_samples) < 10:
			continue
		vmin_p = min(v_samples)
		vmax_p = max(v_samples)
		touched: List[int] = []
		for b in floor_bands:
			if not (vmax_p < b.v_lo or vmin_p > b.v_hi):
				touched.append(b.index)
		if len(touched) < 2:
			continue
		touched.sort()
		uniq: List[int] = []
		for t in touched:
			if not uniq or uniq[-1] != t:
				uniq.append(t)
		for j in range(len(uniq) - 1):
			a, bb = uniq[j], uniq[j + 1]
			if bb != a + 1:
				continue
			stairs.append(
				{
					"id": f"st_{sid}",
					"x": float(wx),
					"y": float(wy),
					"fromFloor": a,
					"toFloor": bb,
				}
			)
			sid += 1
	return stairs


def _corner_nodes_from_bounds(bounds: Tuple[float, float, float, float]) -> Tuple[List[Dict[str, Any]], float, float]:
	min_x, min_y, scale, pixels = bounds
	max_x = min_x + pixels / scale
	max_y = min_y + pixels / scale
	mid_x = (min_x + max_x) / 2
	mid_y = (min_y + max_y) / 2
	nodes = [
		{"id": "n_sw", "x": min_x + 1, "y": min_y + 1, "label": "Corner SW"},
		{"id": "n_se", "x": max_x - 1, "y": min_y + 1, "label": "Corner SE"},
		{"id": "n_nw", "x": min_x + 1, "y": max_y - 1, "label": "Corner NW"},
		{"id": "n_ne", "x": max_x - 1, "y": max_y - 1, "label": "Corner NE"},
		{"id": "n_c", "x": mid_x, "y": mid_y, "label": "Center"},
	]
	return nodes, mid_x, mid_y


def extract_floor_plan_slice(
	points: np.ndarray,
	vertical_axis: str,
	slice_center: float,
	slice_thickness: float,
	voxel_size: float,
) -> Tuple[List[Dict[str, Any]], Tuple[float, float, float, float], np.ndarray, Any, Any]:
	"""Returns walls, bounds, xy (planar), processed occupancy image, raw occupancy (pre-dilate)."""
	xy = _slice_at_height_to_planar_xy(
		points,
		vertical_axis,
		slice_center,
		slice_thickness,
		voxel_size,
	)
	sparse = len(xy) < 8000
	img, bounds, raw = _occupancy_grid_np(xy, sparse=sparse, return_raw=True)
	walls = _hough_walls_tuned(img, bounds)
	return walls, bounds, xy, img, raw


def build_floor_map_dict(
	name: str,
	walls: List[Dict[str, Any]],
	bounds: Tuple[float, float, float, float],
	stair_pois: List[Dict[str, Any]],
) -> Dict[str, Any]:
	nodes, mid_x, mid_y = _corner_nodes_from_bounds(bounds)
	min_x, min_y, scale, pixels = bounds
	max_x = min_x + pixels / scale
	max_y = min_y + pixels / scale
	labels = [
		{"id": "lbl_auto_center", "text": "Map center", "x": mid_x, "y": mid_y},
		{"id": "lbl_auto_w", "text": "West side", "x": min_x + (max_x - min_x) * 0.12, "y": mid_y},
		{"id": "lbl_auto_e", "text": "East side", "x": max_x - (max_x - min_x) * 0.12, "y": mid_y},
	]
	pois = [{"id": "poi_auto_entrance", "type": "entrance", "x": min_x + 2, "y": min_y + 2}]
	for sp in stair_pois:
		pois.append(dict(sp))
	return {
		"schemaVersion": 1,
		"name": name,
		"scale": 1.0,
		"walls": walls,
		"rooms": [],
		"labels": labels,
		"pois": pois,
		"nodes": nodes,
		"edges": [],
	}


def process_multi_floor_scan(
	path: Path,
	*,
	slice_thickness: float = 0.25,
	voxel_size: float | None = None,
	vertical_axis: str | None = None,
	mesh_sample_points: int = 400_000,
	height_offset_m: float = 1.0,
	preview_resolution_m: float = 0.05,
	mesh_min_segment_m: float = DEFAULT_MESH_MIN_SEGMENT_M,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Tuple[Any, List[Dict[str, Any]], Tuple[float, float, float, float], str]]]:
	"""
	Returns (per-floor map dicts, manifest dict, preview tuples: raw_img, walls, bounds, title).

	Mesh with faces: wall-face filter + mesh.section per floor (no Hough).
	Faceless point cloud: band slice + occupancy + Hough (unchanged).
	"""
	sfx = path.suffix.lower()
	floor_maps: List[Dict[str, Any]] = []
	manifest_floors: List[Dict[str, Any]] = []
	previews: List[Tuple[Any, List[Dict[str, Any]], Tuple[float, float, float, float], str]] = []

	combined_mesh = _try_load_mesh_with_faces(path)
	if combined_mesh is not None:
		trimesh = _require_trimesh()
		nsamp = min(int(mesh_sample_points), 500_000, max(len(combined_mesh.faces) * 3, 10_000))
		np.random.seed(42)
		surf_pts, _ = trimesh.sample.sample_surface(combined_mesh, int(nsamp))
		surf_pts = np.asarray(surf_pts, dtype=np.float64)
		verts = np.asarray(combined_mesh.vertices, dtype=np.float64)
		if vertical_axis is None:
			vaxis = "z" if sfx == ".ply" else _bbox_vertical_axis_np(surf_pts)
		else:
			vaxis = vertical_axis.lower()
		ext = surf_pts.max(axis=0) - surf_pts.min(axis=0)
		max_extent = float(np.max(ext))
		if voxel_size is None:
			voxel_size = max(0.015 * max_extent / 40.0, 1e-6)

		bands = detect_floor_bands(surf_pts, vaxis)
		stair_links = detect_stair_shafts_mesh(combined_mesh, vaxis, bands)
		wall_base = _extract_wall_faces(combined_mesh, vaxis, normal_threshold=0.3)

		for band in bands:
			slice_h = float(band.v_ref) + float(height_offset_m)
			slice_h = min(max(slice_h, band.v_lo + 0.08), band.v_hi - 0.08)
			walls, bounds = _walls_from_mesh_section(
				wall_base, vaxis, slice_h, min_segment_m=float(mesh_min_segment_m)
			)
			if not walls:
				warnings.warn(
					f"Skipping floor {band.name}: mesh.section produced no segments at height {slice_h:.3f}.",
					UserWarning,
				)
				continue
			raw_grid, _ = _rasterize_walls_grid(walls, resolution_m=float(preview_resolution_m))
			previews.append((raw_grid, walls, bounds, f"{path.stem} — {band.name}"))

			stair_pois_for_floor: List[Dict[str, Any]] = []
			for st in stair_links:
				if st["fromFloor"] == band.index or st["toFloor"] == band.index:
					stair_pois_for_floor.append(
						{
							"id": f"{st['id']}_f{band.index}",
							"type": "stairs",
							"x": st["x"],
							"y": st["y"],
						}
					)

			fmap = build_floor_map_dict(f"{path.stem} — {band.name}", walls, bounds, stair_pois_for_floor)
			floor_maps.append(fmap)
			manifest_floors.append(
				{
					"index": band.index,
					"level": band.name,
					"verticalRange": [band.v_lo, band.v_hi],
					"mapPath": f"uni-floor-{band.index}.json",
				}
			)

		manifest = {
			"schemaVersion": 1,
			"name": path.stem,
			"floors": manifest_floors,
			"stairs": stair_links,
		}
		return floor_maps, manifest, previews

	# --- Point cloud / faceless path ---
	points = load_scan_points_array(path, mesh_sample_points=mesh_sample_points)
	if vertical_axis is None:
		vaxis = "z" if sfx == ".ply" else _bbox_vertical_axis_np(points)
	else:
		vaxis = vertical_axis.lower()

	ext = points.max(axis=0) - points.min(axis=0)
	max_extent = float(np.max(ext))
	if voxel_size is None:
		voxel_size = max(0.015 * max_extent / 40.0, 1e-6)

	bands = detect_floor_bands(points, vaxis)
	stair_links = detect_stair_shafts(points, vaxis, bands)

	for band in bands:
		try:
			xy = _slice_band_to_planar_xy(points, vaxis, band.v_lo, band.v_hi, float(voxel_size))
		except Exception:
			xy = np.zeros((0, 2), dtype=np.float64)
		if len(xy) < 200:
			warnings.warn(f"Skipping floor {band.name}: too few points in vertical band.", UserWarning)
			continue
		sparse = len(xy) < 8000
		try:
			img, bounds, raw_img = _occupancy_grid_np(xy, sparse=sparse, return_raw=True)
			walls = _hough_walls_tuned(img, bounds)
		except ValueError:
			warnings.warn(f"Skipping floor {band.name}: occupancy failed.", UserWarning)
			continue
		if not walls:
			warnings.warn(f"Skipping floor {band.name}: no wall segments detected.", UserWarning)
			continue

		previews.append((raw_img, walls, bounds, f"{path.stem} — {band.name}"))

		stair_pois_for_floor: List[Dict[str, Any]] = []
		for st in stair_links:
			if st["fromFloor"] == band.index or st["toFloor"] == band.index:
				stair_pois_for_floor.append(
					{
						"id": f"{st['id']}_f{band.index}",
						"type": "stairs",
						"x": st["x"],
						"y": st["y"],
					}
				)

		fmap = build_floor_map_dict(f"{path.stem} — {band.name}", walls, bounds, stair_pois_for_floor)
		floor_maps.append(fmap)
		manifest_floors.append(
			{
				"index": band.index,
				"level": band.name,
				"verticalRange": [band.v_lo, band.v_hi],
				"mapPath": f"uni-floor-{band.index}.json",
			}
		)

	manifest = {
		"schemaVersion": 1,
		"name": path.stem,
		"floors": manifest_floors,
		"stairs": stair_links,
	}
	return floor_maps, manifest, previews


def process_scan_file(
	path: Path,
	*,
	slice_center: float | None = None,
	slice_thickness: float = 0.2,
	voxel_size: float | None = None,
	vertical_axis: str | None = None,
	mesh_sample_points: int = 400_000,
	height_offset_m: float = 1.0,
	mesh_min_segment_m: float = DEFAULT_MESH_MIN_SEGMENT_M,
) -> Dict[str, Any]:
	"""Single-slice map (legacy). Mesh with faces uses section at floor_min + height_offset (or slice_center)."""
	sfx = path.suffix.lower()
	combined_mesh = _try_load_mesh_with_faces(path)
	if combined_mesh is not None:
		trimesh = _require_trimesh()
		nsamp = min(int(mesh_sample_points), 200_000, max(len(combined_mesh.faces) * 3, 10_000))
		np.random.seed(42)
		surf_pts, _ = trimesh.sample.sample_surface(combined_mesh, int(nsamp))
		surf_pts = np.asarray(surf_pts, dtype=np.float64)
		verts = np.asarray(combined_mesh.vertices, dtype=np.float64)
		if vertical_axis is None:
			vaxis = "z" if sfx == ".ply" else _bbox_vertical_axis_np(surf_pts)
		else:
			vaxis = vertical_axis.lower()
		vi = _axis_index(vaxis)
		v0 = float(verts[:, vi].min())
		v1 = float(verts[:, vi].max())
		v_ref = 0.5 * (v0 + v1)
		slice_h = float(slice_center) if slice_center is not None else min(v_ref + float(height_offset_m), v1 - 0.08)
		wall_base = _extract_wall_faces(combined_mesh, vaxis, normal_threshold=0.3)
		walls, bounds = _walls_from_mesh_section(
			wall_base, vaxis, slice_h, min_segment_m=float(mesh_min_segment_m)
		)
		if not walls:
			raise ValueError(
				"No wall segments from mesh section; try multi-floor mode, adjust --height-offset, or use point-cloud input."
			)
	else:
		points = load_scan_points_array(path, mesh_sample_points=mesh_sample_points)
		if vertical_axis is None:
			vaxis = "z" if sfx == ".ply" else _bbox_vertical_axis_np(points)
		else:
			vaxis = vertical_axis.lower()
		ext = points.max(axis=0) - points.min(axis=0)
		max_extent = float(np.max(ext))
		if voxel_size is None:
			voxel_size = max(0.015 * max_extent / 40.0, 1e-6)
		center = float(slice_center) if slice_center is not None else float(points[:, _axis_index(vaxis)].min()) + 1.2
		walls, bounds, _xy, _img, _raw = extract_floor_plan_slice(
			points,
			vaxis,
			center,
			slice_thickness,
			float(voxel_size),
		)
		if not walls:
			raise ValueError("No wall segments detected for single-floor export; try multi-floor mode or adjust slice.")
	nodes, mid_x, mid_y = _corner_nodes_from_bounds(bounds)
	min_x, min_y, scale, pixels = bounds
	max_x = min_x + pixels / scale
	max_y = min_y + pixels / scale
	return {
		"schemaVersion": 1,
		"name": path.stem,
		"scale": 1.0,
		"walls": walls,
		"rooms": [],
		"labels": [
			{"id": "lbl_auto_center", "text": "Map center", "x": mid_x, "y": mid_y},
			{"id": "lbl_auto_w", "text": "West side", "x": min_x + (max_x - min_x) * 0.12, "y": mid_y},
			{"id": "lbl_auto_e", "text": "East side", "x": max_x - (max_x - min_x) * 0.12, "y": mid_y},
		],
		"pois": [{"id": "poi_auto_entrance", "type": "entrance", "x": min_x + 2, "y": min_y + 2}],
		"nodes": nodes,
		"edges": [],
	}


def write_multi_floor_outputs(
	path: Path,
	out_dir: Path,
	*,
	preview: bool = False,
	**kwargs: Any,
) -> None:
	"""Write uni-floor-*.json, uni-manifest.json, uni-bundle.json; optional PNG previews."""
	floor_maps, manifest, previews = process_multi_floor_scan(path, **kwargs)
	if not floor_maps:
		raise ValueError("No floors exported (empty slices or no walls on all bands).")
	out_dir.mkdir(parents=True, exist_ok=True)
	for i, fmap in enumerate(floor_maps):
		idx = int(manifest["floors"][i]["index"])
		fp = out_dir / f"uni-floor-{idx}.json"
		fp.write_text(json.dumps(fmap, indent=2), encoding="utf-8")
	(out_dir / "uni-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
	bundle = {
		"schemaVersion": 1,
		"name": manifest["name"],
		"stairs": manifest["stairs"],
		"floors": [{**manifest["floors"][i], "map": floor_maps[i]} for i in range(len(floor_maps))],
	}
	(out_dir / "uni-bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
	if preview:
		for i, (raw_img, walls, bounds, title) in enumerate(previews):
			idx = int(manifest["floors"][i]["index"])
			preview_floor_png(out_dir / f"uni-floor-{idx}.png", raw_img, walls, bounds, title=title)


def process_point_cloud_file(
	ply_path: Path,
	*,
	z_center: float = 1.2,
	slice_thickness: float = 0.2,
) -> Dict[str, Any]:
	return process_scan_file(
		ply_path,
		slice_center=z_center,
		slice_thickness=slice_thickness,
		vertical_axis="z",
	)


def write_floorplan_json(input_path: Path, out_path: Path, **kwargs: Any) -> None:
	kw = dict(kwargs)
	if "z_center" in kw:
		kw["slice_center"] = kw.pop("z_center")
		kw.setdefault("vertical_axis", "z")
	data = process_scan_file(input_path, **kw)
	out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def preview_floor_png(
	out_path: Path,
	raw_img: Any,
	walls: List[Dict[str, Any]],
	bounds: Tuple[float, float, float, float],
	*,
	title: str,
	scale_m_per_bar: float = 5.0,
) -> None:
	try:
		import matplotlib.pyplot as plt  # type: ignore
	except Exception:
		warnings.warn("matplotlib not installed; skip PNG preview.", UserWarning)
		return

	min_x, min_y, scale_px, pixels = bounds
	world_w = pixels / scale_px
	fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor="#191919")

	left = np.asarray(raw_img, dtype=np.float64)
	if left.ndim == 2:
		left_disp = np.flipud(left)
		axes[0].imshow(255 - left_disp, cmap="gray", origin="upper", vmin=0, vmax=255)
	else:
		axes[0].imshow(left, cmap="gray", origin="upper")
	axes[0].set_title(f"{title} — slice raster", color="w", fontsize=10)
	axes[0].set_facecolor("#0d0d0d")
	axes[0].axis("off")

	parch = (245 / 255.0, 240 / 255.0, 225 / 255.0)
	wall_rgb = (40 / 255.0, 35 / 255.0, 30 / 255.0)
	axes[1].set_facecolor(parch)
	axes[1].set_title(f"{title} — vector walls", color="w", fontsize=10)
	axes[1].set_aspect("equal")
	for w in walls:
		pts = w["points"]
		if len(pts) < 2:
			continue
		xs = [pts[0]["x"], pts[1]["x"]]
		ys = [pts[0]["y"], pts[1]["y"]]
		axes[1].plot(xs, ys, color=wall_rgb, linewidth=1.0, solid_capstyle="round")
	bar_len = scale_m_per_bar
	axes[1].plot(
		[min_x + 0.5, min_x + 0.5 + bar_len],
		[min_y + 0.5, min_y + 0.5],
		color="red",
		linewidth=3,
	)
	axes[1].text(min_x + 0.5, min_y + 0.95, f"{scale_m_per_bar:.0f} m", color="red", fontsize=10)
	axes[1].set_xlim(min_x - 0.5, min_x + world_w + 0.5)
	axes[1].set_ylim(min_y + world_w + 0.5, min_y - 0.5)
	axes[1].axis("off")
	plt.tight_layout()
	fig.savefig(str(out_path), dpi=180, facecolor="#191919", edgecolor="none")
	plt.close(fig)
