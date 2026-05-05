"""
CLI: point cloud (.ply) → NavigationMvpMapV1 JSON.

For `.glb` / `.gltf` (e.g. `Lidar/Uni_textured.glb`), use `scripts/floorplan_from_scan.py` instead.

Usage:
  python scripts/floorplan_from_ply.py --input path/to/scan.ply --output path/to/map.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.floorplan_processor import write_floorplan_json  # noqa: E402


def main() -> None:
	parser = argparse.ArgumentParser(description="Generate MVP floorplan JSON from a .ply scan.")
	parser.add_argument("--input", required=True, type=Path, help="Path to input .ply")
	parser.add_argument("--output", required=True, type=Path, help="Path to output .json")
	parser.add_argument("--z-center", type=float, default=1.2)
	parser.add_argument("--slice-thickness", type=float, default=0.2)
	args = parser.parse_args()

	if args.input.suffix.lower() != ".ply":
		raise SystemExit("MVP CLI currently supports .ply only.")

	write_floorplan_json(args.input, args.output, z_center=args.z_center, slice_thickness=args.slice_thickness)
	print(f"Wrote {args.output}")


if __name__ == "__main__":
	main()
