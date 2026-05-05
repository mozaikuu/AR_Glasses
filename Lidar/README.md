# Building scan (LiDAR / mesh)

This folder holds the **campus mesh** used by the indoor navigation MVP:

- **`Uni_textured.glb`** — textured 3D mesh (source for the automatic floorplan pass).

## Regenerate the Expo map JSON

From the repo root (with `app/requirements-navigation-mvp.txt` installed):

```bash
pip install -r app/requirements-navigation-mvp.txt
python scripts/floorplan_from_scan.py
```

Defaults:

- Input: `Lidar/Uni_textured.glb`
- Output directory: `clients/Expo/assets/navigation/uni/` (`uni-bundle.json`, `uni-manifest.json`, `uni-floor-*.json`)

Options: `--slice-center`, `--slice-thickness`, `--vertical-axis` (`x` \| `y` \| `z` \| `auto`), `--mesh-samples`.

The pipeline follows **Megaprompt.md**: voxel downsample → horizontal slice ~1.2 m above ground along the detected vertical axis → occupancy image → morphology → Canny → Hough line segments, plus placeholder **nodes**, **labels**, and an **entrance** POI for routing demos. If Hough finds no segments, a **footprint bounding box** is emitted so the editor and app still render a navigable outline.
