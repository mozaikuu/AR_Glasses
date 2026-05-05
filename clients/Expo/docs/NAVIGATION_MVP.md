# Indoor navigation MVP (Expo + shared JSON)

This MVP follows **Megaprompt.md** (LiDAR → JSON pipeline, web editor, mobile routing). The mobile map uses **SVG** instead of MapLibre for Expo compatibility; routing is in-app **A\*** on `nodes` / `edges` as in the megaprompt.

## Campus map from `Lidar/`

- Source mesh: `Lidar/Uni_textured.glb` (see `Lidar/README.md`).
- Bundled multi-floor asset: `clients/Expo/assets/navigation/uni/uni-bundle.json` (per-floor maps + stair links)
- Regenerate after changing the mesh:

```bash
pip install -r app/requirements-navigation-mvp.txt
python scripts/floorplan_from_scan.py
# optional PNG previews (install matplotlib):
python scripts/floorplan_from_scan.py --preview
```

Optional **sample** rectilinear map: `clients/Expo/assets/navigation/sample-map.json`.

## Map format

- Schema and helpers: `clients/Expo/lib/navigation-mvp/`
- `loadBuildingMap()` in `loadBuildingMap.ts` (Megaprompt-style loader wrapper around `parseNavigationMvpMap`).

## Mobile: Navigation tab

- Screen: `clients/Expo/app/main/navigation.tsx`
- Tab: **Navigation** in `app/main/_layout.tsx`
- Flow aligned to megaprompt: **“Where do you want to go?”**, search, start + destination from **labels + POIs + path nodes**, **Preview route**, SVG map, bottom card with destination and **Clear route**.

Routing uses **A\***; if `edges` is empty, `ensureAutoEdges()` adds k-nearest links when routing.

## Web-only map editor

- Route: **`/map-editor`** → `clients/Expo/app/map-editor.tsx`
- Loads **`uni/uni-bundle.json`** by default (same as the Navigation tab).

## Python: scan → JSON

- Processor: `app/services/floorplan_processor.py` ( **trimesh** + **numpy** + **OpenCV** ; Open3D optional / not required)
- CLI: `scripts/floorplan_from_scan.py` (default input/output for `Lidar/Uni_textured.glb`)
- Legacy `.ply` only: `scripts/floorplan_from_ply.py`

**Caveats**

- First automatic pass is approximate; refine in the web editor.
- Megaprompt’s REST `GET /route` is not implemented; routing runs in TypeScript on the device (static map MVP).

## Archived experiment tabs

LiDAR / 3D / panorama tab UIs live under `clients/Expo/archived/` (see `archived/README.md`).
