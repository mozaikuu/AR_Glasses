"""
CLI: LiDAR scan (.ply / .glb / .gltf) → NavigationMvpMapV1 JSON (single or multi-floor).

Default: multi-floor export to clients/Expo/assets/navigation/uni/

Usage:
  python scripts/floorplan_from_scan.py
  python scripts/floorplan_from_scan.py --single-floor --output clients/Expo/assets/navigation/uni-building-map.json
  python scripts/floorplan_from_scan.py --preview
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from app.services.floorplan_processor import (  # noqa: E402
	DEFAULT_MESH_MIN_SEGMENT_M,
	write_floorplan_json,
	write_multi_floor_outputs,
)


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate MVP floorplan JSON from .ply, .glb, or .gltf.")
	parser.add_argument(
		"--input",
		type=Path,
		default=ROOT / "Lidar" / "Uni_textured.glb",
		help="Input scan (default: Lidar/Uni_textured.glb)",
	)
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=ROOT / "clients" / "Expo" / "assets" / "navigation" / "uni",
		help="Multi-floor output directory (uni-floor-*.json, uni-manifest.json, uni-bundle.json)",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=None,
		help="With --single-floor: output JSON file path",
	)
	parser.add_argument(
		"--single-floor",
		action="store_true",
		help="Legacy single NavigationMvpMapV1 file (no manifest)",
	)
	parser.add_argument(
		"--preview",
		action="store_true",
		help="Write uni-floor-<i>.png previews (requires matplotlib)",
	)
	parser.add_argument(
		"--slice-center",
		type=float,
		default=None,
		help="(single-floor) Absolute slice position along vertical axis",
	)
	parser.add_argument("--slice-thickness", type=float, default=0.25)
	parser.add_argument(
		"--vertical-axis",
		choices=("x", "y", "z", "auto"),
		default="auto",
		help="World axis for vertical; auto uses z for .ply and smallest bbox extent for mesh",
	)
	parser.add_argument("--mesh-samples", type=int, default=400_000, help="Uniform samples for mesh→point fallback / point-cloud branch only")
	parser.add_argument(
		"--height-offset",
		type=float,
		default=1.0,
		help="Metres above each floor band's v_lo for mesh.section (mesh with faces only)",
	)
	parser.add_argument(
		"--preview-resolution",
		type=float,
		default=0.05,
		help="Metres per pixel for mesh preview raster (left panel)",
	)
	parser.add_argument(
		"--min-segment",
		type=float,
		default=None,
		help=f"Min wall segment length (m) for mesh.section path (default: {DEFAULT_MESH_MIN_SEGMENT_M})",
	)
	args = parser.parse_args()

	sfx = args.input.suffix.lower()
	if sfx not in (".ply", ".glb", ".gltf"):
		raise SystemExit(f"Unsupported format {args.input.suffix!r}; use .ply, .glb, or .gltf.")

	vaxis = None if args.vertical_axis == "auto" else args.vertical_axis

	kwargs: dict = {
		"slice_thickness": args.slice_thickness,
		"mesh_sample_points": args.mesh_samples,
		"height_offset_m": args.height_offset,
		"preview_resolution_m": args.preview_resolution,
	}
	if args.min_segment is not None:
		kwargs["mesh_min_segment_m"] = args.min_segment
	if args.slice_center is not None:
		kwargs["slice_center"] = args.slice_center
	if vaxis is not None:
		kwargs["vertical_axis"] = vaxis
	if sfx == ".ply" and args.vertical_axis == "auto":
		kwargs["vertical_axis"] = "z"

	if args.single_floor:
		out = args.output or (ROOT / "clients" / "Expo" / "assets" / "navigation" / "uni-building-map.json")
		out.parent.mkdir(parents=True, exist_ok=True)
		kw_single = {k: v for k, v in kwargs.items() if k != "preview_resolution_m"}
		write_floorplan_json(args.input, out, **kw_single)
		print(f"Wrote {out}")
		return

	kw2 = {k: v for k, v in kwargs.items() if k != "slice_center"}
	if vaxis is not None:
		kw2["vertical_axis"] = vaxis
	elif sfx == ".ply":
		kw2["vertical_axis"] = "z"

	write_multi_floor_outputs(args.input, args.output_dir, preview=args.preview, **kw2)
	print(f"Wrote multi-floor bundle under {args.output_dir}")


if __name__ == "__main__":
	main()
